from __future__ import annotations

import os
import re
from dataclasses import dataclass, field, replace
from pathlib import Path

from .models import UIQualityIssue
from .reviewer import UI_EXTENSIONS, review_text, should_skip_dir


@dataclass(frozen=True, slots=True)
class UIFixOperation:
    category: str
    file: str
    line: int
    reason: str
    before: str
    after: str
    applied: bool = False


@dataclass(frozen=True, slots=True)
class UIManualReviewItem:
    category: str
    file: str
    line: int
    reason: str
    suggested_fix: str


@dataclass(slots=True)
class UIFixResult:
    project_path: str
    mode: str
    operations: list[UIFixOperation] = field(default_factory=list)
    skipped_as_unsafe: list[UIManualReviewItem] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        return {
            "safe_fixes_generated": len(self.operations),
            "safe_fixes_applied": sum(operation.applied for operation in self.operations),
            "skipped_as_unsafe": len(self.skipped_as_unsafe),
            "manual_review_items": len(self.skipped_as_unsafe),
            "files_changed": len(self.files_changed),
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "project_path": self.project_path,
            "mode": self.mode,
            "summary": self.summary,
            "operations": [
                {
                    "category": operation.category,
                    "file": operation.file,
                    "line": operation.line,
                    "reason": operation.reason,
                    "before": operation.before,
                    "after": operation.after,
                    "applied": operation.applied,
                }
                for operation in self.operations
            ],
            "skipped_as_unsafe": [
                {
                    "category": item.category,
                    "file": item.file,
                    "line": item.line,
                    "reason": item.reason,
                    "suggested_fix": item.suggested_fix,
                }
                for item in self.skipped_as_unsafe
            ],
            "files_changed": self.files_changed,
        }


@dataclass(frozen=True, slots=True)
class UITextFixResult:
    text: str
    operations: tuple[UIFixOperation, ...]
    skipped_as_unsafe: tuple[UIManualReviewItem, ...]


def fix_project(project_path: str | Path, *, apply: bool = False) -> UIFixResult:
    root = Path(project_path)
    if not root.exists():
        raise FileNotFoundError(f"UI project path does not exist: {root}")

    result = UIFixResult(project_path=str(root), mode="safe" if apply else "dry-run")
    for path in _iter_ui_files(root):
        text, encoding = _read_text(path)
        relative = str(path.relative_to(root)) if root.is_dir() else str(path)
        text_result = fix_text(text, file=relative, apply=apply)
        result.operations.extend(text_result.operations)
        result.skipped_as_unsafe.extend(text_result.skipped_as_unsafe)
        if apply and text_result.text != text:
            path.write_text(text_result.text, encoding=encoding)
            result.files_changed.append(relative)
    return result


def fix_text(text: str, *, file: str = "<memory>", apply: bool = False) -> UITextFixResult:
    review = review_text(text, file=file)
    operations = _plan_mechanical_fixes(text, file=file)
    covered = {(operation.category, operation.line) for operation in operations}
    skipped = tuple(
        _manual_item(issue)
        for issue in review.issues
        if (issue.category, issue.line) not in covered
    )

    updated = text
    finalized: list[UIFixOperation] = []
    for operation in operations:
        applied = False
        if apply and operation.before in updated:
            updated = updated.replace(operation.before, operation.after, 1)
            applied = True
        finalized.append(replace(operation, applied=applied))

    return UITextFixResult(
        text=updated,
        operations=tuple(finalized),
        skipped_as_unsafe=skipped,
    )


def _plan_mechanical_fixes(text: str, *, file: str) -> list[UIFixOperation]:
    operations: list[UIFixOperation] = []

    for match in re.finditer(r"<button\b[^>]*>(?:.*?)</button>", text, re.IGNORECASE | re.DOTALL):
        original = match.group(0)
        current = original
        line = text.count("\n", 0, match.start()) + 1
        loading_flag = _find_loading_flag_near(text, line)

        if _is_icon_only(current) and "aria-label" not in current.lower() and "title=" not in current.lower():
            label = _infer_accessible_label(current)
            if label:
                updated = re.sub(r"<button\b", f'<button aria-label="{label}"', current, count=1, flags=re.IGNORECASE)
                operations.append(
                    UIFixOperation(
                        category="accessibility_label",
                        file=file,
                        line=line,
                        reason="The action name is mechanically identifiable from the button markup.",
                        before=current,
                        after=updated,
                    )
                )
                current = updated

        lowered = current.lower()
        if loading_flag and ("onclick" in lowered or "@click" in lowered or "v-on:click" in lowered) and "disabled" not in lowered:
            if "@click" in lowered or "v-on:click" in lowered:
                attribute = f':disabled="{loading_flag}"'
            else:
                attribute = f"disabled={{{loading_flag}}}"
            updated = re.sub(r"<button\b", f"<button {attribute}", current, count=1, flags=re.IGNORECASE)
            operations.append(
                UIFixOperation(
                    category="action_availability",
                    file=file,
                    line=line,
                    reason=f"Existing loading flag '{loading_flag}' provides a mechanical action guard.",
                    before=current,
                    after=updated,
                )
            )

    for line, line_no in _lines_with_numbers(text):
        width_match = re.search(r"(?<!max-)\bwidth\s*:\s*(1[2-9]\d{2}|[2-9]\d{3,})px\s*;", line, re.IGNORECASE)
        if width_match and "max-width" not in line.lower():
            pixels = width_match.group(1)
            replacement = f"max-width: {pixels}px; width: 100%;"
            operations.append(
                UIFixOperation(
                    category="responsive_layout_risk",
                    file=file,
                    line=line_no,
                    reason="A large fixed width can be bounded without changing the project's visual styling.",
                    before=width_match.group(0),
                    after=replacement,
                )
            )

        height_match = re.search(r"(?<!min-)\bheight\s*:\s*100vh\s*;", line, re.IGNORECASE)
        if height_match and "position: fixed" not in line.lower() and "overflow" not in line.lower():
            operations.append(
                UIFixOperation(
                    category="overflow_visibility",
                    file=file,
                    line=line_no,
                    reason="Replacing a standalone viewport height with min-height preserves growth and prevents clipping.",
                    before=height_match.group(0),
                    after="min-height: 100vh;",
                )
            )

    return operations


def _find_loading_flag_near(text: str, line: int) -> str | None:
    lines = text.splitlines()
    window = "\n".join(lines[max(0, line - 6) : min(len(lines), line + 6)])
    match = re.search(r"\b(isLoading|isSaving|isSubmitting|isPending|loading|saving|submitting|pending)\b", window)
    return match.group(1) if match else None


def _infer_accessible_label(tag: str) -> str | None:
    lowered = tag.lower()
    labels = (
        (("opensettings", "settings", "cog"), "Open settings"),
        (("close", "xmark", "x-icon"), "Close"),
        (("search", "magnif"), "Search"),
        (("delete", "remove", "trash"), "Delete"),
        (("edit", "pencil"), "Edit"),
        (("save",), "Save"),
        (("refresh", "reload"), "Refresh"),
        (("menu",), "Open menu"),
        (("download",), "Download"),
        (("upload",), "Upload"),
        (("approve", "check"), "Approve"),
        (("reject",), "Reject"),
        (("add", "plus", "create"), "Add"),
    )
    for tokens, label in labels:
        if any(token in lowered for token in tokens):
            return label
    return None


def _is_icon_only(tag: str) -> bool:
    content = re.sub(r"<[^>]+>", "", tag).strip()
    lowered = tag.lower()
    return not content and any(token in lowered for token in ("svg", "icon", "lucide", "aria-hidden"))


def _manual_item(issue: UIQualityIssue) -> UIManualReviewItem:
    return UIManualReviewItem(
        category=issue.category,
        file=issue.file,
        line=issue.line,
        reason=issue.reason,
        suggested_fix=issue.suggested_fix,
    )


def _lines_with_numbers(text: str) -> list[tuple[str, int]]:
    return [(line, index) for index, line in enumerate(text.splitlines(), start=1)]


def _iter_ui_files(root: Path):
    if root.is_file():
        if root.suffix.lower() in UI_EXTENSIONS:
            yield root
        return
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [dirname for dirname in dirnames if not should_skip_dir(dirname)]
        current = Path(current_root)
        for filename in filenames:
            path = current / filename
            if path.suffix.lower() in UI_EXTENSIONS:
                yield path


def _read_text(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig"), "utf-8-sig"
    return raw.decode("utf-8"), "utf-8"
