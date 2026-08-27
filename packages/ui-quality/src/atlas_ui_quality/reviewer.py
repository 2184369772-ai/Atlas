from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable

from .models import UIQualityIssue, UIQualityReview
from .visual import review_visual_text


UI_EXTENSIONS = {".css", ".html", ".jsx", ".tsx", ".ts", ".vue"}
SKIP_DIRS = {
    ".cache",
    ".codex_tmp",
    ".git",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "cache",
    "collectstatic",
    "coverage",
    "dist",
    "generated",
    "node_modules",
    "out",
    "review",
    "site-packages",
    "staticfiles",
    "target",
    "var",
    "vendor",
}


def review_project(project_path: str | Path) -> UIQualityReview:
    root = Path(project_path)
    issues: list[UIQualityIssue] = []
    for path in _iter_ui_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_text(encoding="utf-8-sig")
        relative = str(path.relative_to(root)) if root.is_dir() else str(path)
        issues.extend(review_text(text, file=relative, project_path=str(root)).issues)
    return UIQualityReview(project_path=str(root), issues=issues)


def review_text(text: str, *, file: str = "<memory>", project_path: str = "") -> UIQualityReview:
    lines = text.splitlines()
    issues: list[UIQualityIssue] = []
    lower_text = text.lower()
    is_markup = _is_markup_file(file)

    if is_markup:
        issues.extend(_review_markup(lines, file))
        issues.extend(review_visual_text(text, file=file))
    if file.endswith(".css") or "<style" in lower_text:
        issues.extend(_review_css(lines, file))
    issues.extend(_review_state_feedback(lines, file))

    return UIQualityReview(project_path=project_path, issues=issues)


def _iter_ui_files(root: Path) -> Iterable[Path]:
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


def should_skip_dir(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered in SKIP_DIRS
        or lowered.endswith(".egg-info")
        or lowered.endswith(".dist-info")
        or lowered.endswith("_cache")
        or "cache" in lowered
    )


def _review_markup(lines: list[str], file: str) -> list[UIQualityIssue]:
    issues: list[UIQualityIssue] = []
    text = "\n".join(lines)
    buttons = list(_tag_matches(text, "button"))
    for line_no, tag in buttons:
        lowered_tag = tag.lower()
        if any(token in lowered_tag for token in ("onclick", "@click", "v-on:click")) and "disabled" not in lowered_tag:
            issues.append(
                UIQualityIssue(
                    category="action_availability",
                    severity="WARNING",
                    file=file,
                    line=line_no,
                    evidence=_compact(tag),
                    reason="Clickable action does not expose an obvious disabled/loading guard.",
                    suggested_fix="Bind disabled state to loading, permission, or form-validity conditions.",
                    auto_fix_safe=False,
                    confidence="HIGH",
                )
            )
        if _looks_destructive(tag) and not _has_confirmation_near(lines, line_no):
            issues.append(
                UIQualityIssue(
                    category="destructive_action_protection",
                    severity="ERROR",
                    file=file,
                    line=line_no,
                    evidence=_compact(tag),
                    reason="Destructive action lacks nearby confirmation or explicit protection signal.",
                    suggested_fix="Add confirmation, undo, or disabled-until-selected protection in the project UI.",
                    auto_fix_safe=False,
                    confidence="HIGH",
                    recommendation_class="BUSINESS_JUDGMENT",
                    execution_mode="human_judgment",
                )
            )
        if _is_icon_only(tag) and "aria-label" not in tag.lower() and "title=" not in tag.lower():
            issues.append(
                UIQualityIssue(
                    category="accessibility_label",
                    severity="WARNING",
                    file=file,
                    line=line_no,
                    evidence=_compact(tag),
                    reason="Icon-only or terse button lacks an accessible label.",
                    suggested_fix="Add aria-label or visible text that describes the action.",
                    auto_fix_safe=False,
                )
            )

    for line_no, tag in _tag_matches(text, "input"):
        lowered = tag.lower()
        if "placeholder=" in lowered and not _has_label_near(lines, line_no):
            issues.append(
                UIQualityIssue(
                    category="form_label",
                    severity="WARNING",
                    file=file,
                    line=line_no,
                    evidence=_compact(tag),
                    reason="Input appears to rely on placeholder text without a nearby persistent label.",
                    suggested_fix="Keep a visible label and use placeholder only as an example.",
                    auto_fix_safe=False,
                )
            )

    if _has_async_or_loading_word(text) and not _has_feedback_markup(text):
        issues.append(
            UIQualityIssue(
                category="loading_error_empty_state",
                severity="WARNING",
                file=file,
                line=1,
                evidence="loading/error-like code without visible state markup",
                reason="Async UI code should expose visible loading, empty, or error feedback.",
                suggested_fix="Add project-appropriate loading, empty, and error states near the affected panel.",
                auto_fix_safe=False,
                confidence="MEDIUM",
                recommendation_class="VISUAL_RECOMMENDATION",
                execution_mode="codex_edit",
            )
        )

    return issues


def _review_css(lines: list[str], file: str) -> list[UIQualityIssue]:
    issues: list[UIQualityIssue] = []
    css = "\n".join(lines).lower()
    has_media = "@media" in css
    for index, line in enumerate(lines, start=1):
        lowered = line.lower()
        if re.search(r"(?<!max-)\bwidth\s*:\s*(1[2-9]\d{2}|[2-9]\d{3,})px", lowered) and not has_media:
            issues.append(
                UIQualityIssue(
                    category="responsive_layout_risk",
                    severity="WARNING",
                    file=file,
                    line=index,
                    evidence=line.strip(),
                    reason="Large fixed width without a responsive breakpoint can cause horizontal overflow.",
                    suggested_fix="Use max-width, minmax, wrapping, or media/container queries.",
                    auto_fix_safe=True,
                    confidence="HIGH",
                    execution_mode="safe_auto_fix",
                )
            )
        if re.search(r"(?<!min-)\bheight\s*:\s*100vh", lowered) and "overflow" not in lowered:
            issues.append(
                UIQualityIssue(
                    category="overflow_visibility",
                    severity="WARNING",
                    file=file,
                    line=index,
                    evidence=line.strip(),
                    reason="Full-viewport height without overflow handling can hide content on small screens.",
                    suggested_fix="Use min-height or add explicit overflow handling for the scroll region.",
                    auto_fix_safe=True,
                    confidence="HIGH",
                    execution_mode="safe_auto_fix",
                )
            )
        if "overflow: hidden" in lowered:
            issues.append(
                UIQualityIssue(
                    category="overflow_visibility",
                    severity="INFO",
                    file=file,
                    line=index,
                    evidence=line.strip(),
                    reason="Hidden overflow may conceal content, focus rings, menus, or long text.",
                    suggested_fix="Verify this container has a deliberate clipping boundary.",
                    auto_fix_safe=False,
                    recommendation_class="BUSINESS_JUDGMENT",
                    execution_mode="human_judgment",
                )
            )
    return issues


def _review_state_feedback(lines: list[str], file: str) -> list[UIQualityIssue]:
    issues: list[UIQualityIssue] = []
    text = "\n".join(lines)
    for index, line in enumerate(lines, start=1):
        lowered = line.lower()
        if ".catch(" in lowered and not _near_feedback(lines, index):
            issues.append(
                UIQualityIssue(
                    category="interaction_feedback",
                    severity="WARNING",
                    file=file,
                    line=index,
                    evidence=line.strip(),
                    reason="Failure path is not near an obvious user-facing feedback update.",
                    suggested_fix="Surface a visible error, toast, inline message, or retry guidance.",
                    auto_fix_safe=False,
                    recommendation_class="VISUAL_RECOMMENDATION",
                    execution_mode="codex_edit",
                )
            )
        if re.search(r"set[A-Za-z0-9_]*\([^)]*\)", line) and any(token in lowered for token in ("save", "submit", "delete", "remove")):
            if not _near_feedback(lines, index):
                issues.append(
                    UIQualityIssue(
                        category="stale_state_refresh",
                        severity="INFO",
                        file=file,
                        line=index,
                        evidence=line.strip(),
                        reason="Mutation-like UI path should make refresh or success feedback explicit.",
                        suggested_fix="Confirm the affected list/detail view refreshes or shows completion feedback.",
                        auto_fix_safe=False,
                        recommendation_class="VISUAL_RECOMMENDATION",
                        execution_mode="codex_edit",
                    )
                )
    return issues


def _tag_matches(text: str, tag: str) -> Iterable[tuple[int, str]]:
    pattern = re.compile(rf"<{tag}\b[^>]*>(?:.*?)</{tag}>|<{tag}\b[^>]*/?>", re.IGNORECASE | re.DOTALL)
    for match in pattern.finditer(text):
        line_no = text.count("\n", 0, match.start()) + 1
        yield line_no, match.group(0)


def _is_markup_file(file: str) -> bool:
    return file.endswith((".html", ".jsx", ".tsx", ".vue"))


def _compact(value: str) -> str:
    return " ".join(value.split())[:240]


def _looks_destructive(tag: str) -> bool:
    lowered = tag.lower()
    return any(token in lowered for token in ("delete", "remove", "danger", "删除", "移除", "作废", "清空"))


def _has_confirmation_near(lines: list[str], line_no: int) -> bool:
    window = "\n".join(lines[max(0, line_no - 6) : min(len(lines), line_no + 6)]).lower()
    return any(token in window for token in ("confirm", "确认", "撤销", "undo", "dialog", "modal"))


def _is_icon_only(tag: str) -> bool:
    content = re.sub(r"<[^>]+>", "", tag).strip()
    lowered = tag.lower()
    return not content and any(token in lowered for token in ("svg", "icon", "lucide", "aria-hidden"))


def _has_label_near(lines: list[str], line_no: int) -> bool:
    window = "\n".join(lines[max(0, line_no - 4) : min(len(lines), line_no + 2)]).lower()
    return "<label" in window or "aria-label" in window or "<span" in window


def _has_async_or_loading_word(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("fetch(", "axios", ".then(", "await ", "loading", "isloading"))


def _has_feedback_markup(text: str) -> bool:
    lowered = text.lower()
    return any(token in lowered for token in ("empty-state", "loading", "spinner", "error", "toast", "message", "alert", "暂无", "失败"))


def _near_feedback(lines: list[str], line_no: int) -> bool:
    window = "\n".join(lines[max(0, line_no - 5) : min(len(lines), line_no + 6)]).lower()
    return any(token in window for token in ("seterror", "toast", "message", "alert", "empty", "loading", "失败", "错误", "完成", "成功"))
