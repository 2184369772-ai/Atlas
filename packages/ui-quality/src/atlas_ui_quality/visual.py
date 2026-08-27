from __future__ import annotations

import re
from pathlib import PurePath

from .models import UIConfidence, UIQualityIssue, UISeverity


def review_visual_text(text: str, *, file: str) -> list[UIQualityIssue]:
    issues: list[UIQualityIssue] = []
    issues.extend(_review_tables(text, file))
    issues.extend(_review_action_hierarchy(text, file))
    issues.extend(_review_form_grouping(text, file))
    issues.extend(_review_metadata_density(text, file))
    issues.extend(_review_technical_detail_disclosure(text, file))
    return issues


def _review_tables(text: str, file: str) -> list[UIQualityIssue]:
    issues: list[UIQualityIssue] = []
    matches = list(re.finditer(r"<table\b[^>]*>.*?</table>", text, re.IGNORECASE | re.DOTALL))
    matches.extend(re.finditer(r"<el-table\b[^>]*>.*?</el-table>", text, re.IGNORECASE | re.DOTALL))
    seen_categories: set[str] = set()
    for match in sorted(matches, key=lambda item: item.start()):
        table = match.group(0)
        lowered = table.lower()
        is_vue_table = lowered.startswith("<el-table")
        header_count = len(re.findall(r"<el-table-column\b", table, re.IGNORECASE)) if is_vue_table else len(
            re.findall(r"<th\b", table, re.IGNORECASE)
        )
        if header_count < (6 if is_vue_table else 8):
            continue

        line = _line_number(text, match.start())
        evidence = f"table has {header_count} header cells"
        local_context = text[max(0, match.start() - 1200) : min(len(text), match.end() + 1600)].lower()
        matrix_without_hierarchy = "matrix-table" in lowered and not any(
            token in lowered for token in ("summary-row", "group-row", "category-row", "tone", "year-total", "sticky")
        )
        uniform_summary_hierarchy = lowered.count("summary-row") >= 3 and not any(
            token in lowered for token in ("group-row", "category-row", "investment-row", "net-row", "excluded-row", "tone")
        )
        if (
            "wide_table_readability" not in seen_categories
            and not is_vue_table
            and (header_count >= 10 or "matrix-table" in lowered)
            and "sticky" not in lowered
            and "<colgroup" not in lowered
        ):
            issues.append(
                _visual_issue(
                    category="wide_table_readability",
                    severity="WARNING",
                    file=file,
                    line=line,
                    evidence=f"{evidence}; no sticky reading anchor or column sizing",
                    reason="Wide enterprise tables become difficult to scan when row identity disappears during horizontal movement.",
                    suggested_fix=(
                        "Keep the key identity column visible, define column widths by information value, "
                        "and reduce the visual weight of low-value supporting columns."
                    ),
                    confidence="HIGH",
                )
            )
            seen_categories.add("wide_table_readability")

        if "responsive_content_strategy" not in seen_categories and not any(
            token in local_context for token in ("mobile-only", "card-list", "report-table-wrap", "sticky-col")
        ):
            issues.append(
                _visual_issue(
                    category="responsive_content_strategy",
                    severity="WARNING",
                    file=file,
                    line=line,
                    evidence=f"{evidence}; no explicit compact-screen representation",
                    reason="A desktop-width table cannot preserve hierarchy and action clarity by shrinking alone.",
                    suggested_fix=(
                        "Add an explicit small-screen representation: use cards for action-heavy rows, "
                        "or a scroll region with key columns anchored for comparison-heavy data."
                    ),
                    confidence="HIGH",
                )
            )
            seen_categories.add("responsive_content_strategy")

        if (
            "table_visual_hierarchy" not in seen_categories
            and not is_vue_table
            and (header_count >= 10 or matrix_without_hierarchy or uniform_summary_hierarchy)
            and not any(token in lowered for token in ("group-row", "category-row", "tone", "year-total", "sticky"))
        ):
            issues.append(
                _visual_issue(
                    category="table_visual_hierarchy",
                    severity="INFO",
                    file=file,
                    line=line,
                    evidence=f"{evidence}; summary and exception rows share one visual treatment",
                    reason="Dense matrices need stable row groups and emphasis levels so totals, exceptions, and detail rows do not compete equally.",
                    suggested_fix=(
                        "Introduce explicit group, subtotal, total, and muted-supporting row treatments; "
                        "keep numeric alignment consistent and emphasize only decision-relevant values."
                    ),
                    confidence="HIGH",
                )
            )
            seen_categories.add("table_visual_hierarchy")
    return issues


def _review_action_hierarchy(text: str, file: str) -> list[UIQualityIssue]:
    issues: list[UIQualityIssue] = []
    pattern = re.compile(
        r"<(?:div|section)\b[^>]*(?:class|className)\s*=\s*[\"'][^\"']*(?:actions|toolbar)[^\"']*[\"'][^>]*>"
        r"(.*?)</(?:div|section)>",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        block = match.group(0)
        buttons = len(re.findall(r"<(?:button|el-button)\b", block, re.IGNORECASE))
        if buttons < 3:
            continue
        primary = len(re.findall(r"(?:primary|btn-primary|type\s*=\s*[\"']primary)", block, re.IGNORECASE))
        if primary not in (0, buttons):
            continue
        issues.append(
            _visual_issue(
                category="action_hierarchy",
                severity="WARNING",
                file=file,
                line=_line_number(text, match.start()),
                evidence=f"action group has {buttons} peer-styled actions and {primary} explicit primary actions",
                reason="When every action has equal visual weight, users must reread the group instead of recognizing the next likely step.",
                suggested_fix=(
                    "Keep one primary action in the first-level action area; group secondary actions together "
                    "and lower the visual weight of infrequent or reversible commands."
                ),
                confidence="HIGH",
            )
        )
        break
    return issues


def _review_form_grouping(text: str, file: str) -> list[UIQualityIssue]:
    controls = len(re.findall(r"<(?:input|select|textarea|el-input|el-select)\b", text, re.IGNORECASE))
    if controls < 8:
        return []
    grouping_markers = len(
        re.findall(r"<(?:fieldset|section)\b|form-(?:section|group)|step-(?:panel|section)|section-heading", text, re.IGNORECASE)
    )
    if grouping_markers >= 2:
        return []
    return [
        _visual_issue(
            category="form_grouping",
            severity="WARNING",
            file=file,
            line=1,
            evidence=f"{controls} form controls with {grouping_markers} explicit grouping markers",
            reason="Long ungrouped forms increase scanning cost and make completion progress difficult to understand.",
            suggested_fix=(
                "Group fields by business stage or decision topic, give each group a short heading, "
                "and keep the primary submit action with the final group."
            ),
            confidence="MEDIUM",
        )
    ]


def _review_metadata_density(text: str, file: str) -> list[UIQualityIssue]:
    pattern = re.compile(
        r"<(?:div|section)\b[^>]*(?:class|className)\s*=\s*[\"'][^\"']*(?:meta|metadata)[^\"']*[\"'][^>]*>"
        r"(.*?)</(?:div|section)>",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(text):
        item_count = len(re.findall(r"<(?:span|p|small)\b", match.group(1), re.IGNORECASE))
        if item_count < 5:
            continue
        return [
            _visual_issue(
                category="metadata_density",
                severity="INFO",
                file=file,
                line=_line_number(text, match.start()),
                evidence=f"metadata block exposes {item_count} peer-level items",
                reason="Dense peer-level metadata competes with the decision, status, and next action users need first.",
                suggested_fix=(
                    "Promote decision status and next action to the primary scan line; move source, version, "
                    "timestamps, and technical context to muted text or a secondary disclosure."
                ),
                confidence="MEDIUM",
            )
        ]
    return []


def _review_technical_detail_disclosure(text: str, file: str) -> list[UIQualityIssue]:
    lowered = text.lower()
    error_container = re.search(r"classname\s*=\s*[\"'][^\"']*error[^\"']*[\"']", lowered)
    rendered_react_error = None
    if error_container:
        error_window = lowered[max(0, error_container.start() - 200) : error_container.end() + 300]
        if "errormessage" in error_window:
            rendered_react_error = error_container
    explicit_positions = [
        lowered.find(token)
        for token in ("technicaldetail", "technical_detail", "stacktrace", "traceback")
        if token in lowered
    ]
    token_position = rendered_react_error.start() if rendered_react_error else min(explicit_positions, default=-1)
    if token_position < 0:
        return []
    local_context = lowered[token_position : token_position + 400]
    if "<details" in local_context:
        return []
    return [
        _visual_issue(
            category="technical_detail_disclosure",
            severity="INFO",
            file=file,
            line=_line_number(text, token_position),
            evidence="error or technical detail is rendered without an explicit disclosure boundary",
            reason="Raw technical detail dominates the page and makes the recovery message harder to scan.",
            suggested_fix=(
                "Keep a short user-facing error and recovery action visible; place stack traces or provider detail "
                "inside an expandable technical-details section."
            ),
            confidence="MEDIUM",
        )
    ]


def _visual_issue(
    *,
    category: str,
    severity: UISeverity,
    file: str,
    line: int,
    evidence: str,
    reason: str,
    suggested_fix: str,
    confidence: UIConfidence,
) -> UIQualityIssue:
    return UIQualityIssue(
        category=category,
        severity=severity,
        file=file,
        line=line,
        component=PurePath(file).stem,
        evidence=evidence,
        reason=reason,
        suggested_fix=suggested_fix,
        auto_fix_safe=False,
        confidence=confidence,
        recommendation_class="VISUAL_RECOMMENDATION",
        execution_mode="codex_edit",
    )


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1
