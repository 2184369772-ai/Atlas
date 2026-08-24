from __future__ import annotations

from collections import Counter
from typing import Any

from atlas_tabular import TabularIssue, TabularResult

from .models import (
    CommitReadiness,
    IntakeAdapter,
    IntakeIssue,
    IntakePreview,
    IntakeRequest,
    IntakeRowDecision,
    IntakeRowInput,
    IntakeRowResult,
    IntakeSummary,
)


VALID_DECISIONS = {"ACCEPT", "SKIP", "REJECT", "REVIEW"}


def build_intake_preview(
    tabular_result: TabularResult,
    adapter: IntakeAdapter,
    *,
    request: IntakeRequest | None = None,
) -> IntakePreview:
    request = request or IntakeRequest()
    preview = IntakePreview(
        source_name=request.source_name or tabular_result.metadata.source_name,
        table_name=tabular_result.metadata.selected_table or tabular_result.metadata.selected_sheet,
        request=request,
    )
    preview.issues.extend(_convert_tabular_issues(tabular_result.errors))
    preview.issues.extend(_convert_tabular_issues(tabular_result.warnings))

    if not tabular_result.rows:
        preview.issues.append(
            IntakeIssue(
                code="EMPTY_INPUT",
                severity="ERROR",
                scope="SOURCE",
                message="No data rows were available for enterprise intake.",
            )
        )
        preview.summary = _build_summary(preview.rows, preview.issues, preview_mode=request.preview_mode)
        return preview

    if request.stop_on_structural_errors and any(issue.severity == "ERROR" for issue in preview.issues):
        preview.summary = _build_summary(preview.rows, preview.issues, preview_mode=request.preview_mode)
        return preview

    headers = tabular_result.headers
    for row in tabular_result.rows:
        values_by_header = {
            (header.normalized_label or header.label): value
            for header, value in zip(headers, row.raw_values)
            if header.label or header.normalized_label
        }
        mapped_values, unmapped_headers = _map_values(headers, row.raw_values, request.field_mapping)
        row_input = IntakeRowInput(
            row_index=row.row_index,
            source_row_index=row.source_row_index,
            raw_values=list(row.raw_values),
            values_by_header=values_by_header,
            mapped_values=mapped_values,
        )
        decision = adapter.evaluate_row(row_input)
        _validate_decision(decision)
        row_issues = _normalize_row_issues(decision, row_input)
        for header_label in unmapped_headers:
            row_issues.append(
                IntakeIssue(
                    code="UNKNOWN_COLUMN",
                    severity="WARNING",
                    scope="MAPPING",
                    message=f"Column '{header_label}' was not mapped and will be ignored.",
                    row=row.source_row_index,
                    source_column=header_label,
                )
            )
        preview.rows.append(
            IntakeRowResult(
                row_index=row.row_index,
                source_row_index=row.source_row_index,
                decision=decision.decision,
                mapped_values=mapped_values,
                normalized_values=dict(decision.normalized_values),
                issues=row_issues,
                trace={"source_row": row.source_row_index, **decision.trace},
            )
        )
        preview.issues.extend(row_issues)

    preview.summary = _build_summary(preview.rows, preview.issues, preview_mode=request.preview_mode)
    return preview


def _map_values(headers: list[Any], raw_values: list[Any], field_mapping: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    if not field_mapping:
        return {}, []

    mapped: dict[str, Any] = {}
    unmapped_headers: list[str] = []
    for header, value in zip(headers, raw_values):
        lookup_keys = [
            header.normalized_label,
            (header.normalized_label or "").lower() or None,
            header.label,
            (header.label or "").lower() or None,
            header.field_key,
            (header.field_key or "").lower() or None,
        ]
        for key in lookup_keys:
            if key and key in field_mapping:
                mapped[field_mapping[key]] = value
                break
        else:
            if header.label and not header.is_empty:
                unmapped_headers.append(header.label)
    return mapped, unmapped_headers


def _convert_tabular_issues(issues: list[TabularIssue]) -> list[IntakeIssue]:
    return [
        IntakeIssue(
            code=issue.code,
            severity=issue.severity,
            scope="STRUCTURE",
            message=issue.message,
            row=issue.row,
            field=issue.field,
            column=issue.column,
            canonical_code=issue.canonical_code,
            original_value=issue.original_value,
        )
        for issue in issues
    ]


def _normalize_row_issues(decision: IntakeRowDecision, row_input: IntakeRowInput) -> list[IntakeIssue]:
    normalized: list[IntakeIssue] = []
    for issue in decision.issues:
        normalized.append(
            IntakeIssue(
                code=issue.code,
                severity=issue.severity,
                scope=issue.scope,
                message=issue.message,
                row=issue.row if issue.row is not None else row_input.source_row_index,
                field=issue.field,
                column=issue.column,
                source_column=issue.source_column,
                canonical_code=issue.canonical_code,
                original_value=issue.original_value,
            )
        )
    return normalized


def _validate_decision(decision: IntakeRowDecision) -> None:
    if decision.decision not in VALID_DECISIONS:
        raise ValueError(f"Unsupported intake decision: {decision.decision}")


def _build_summary(rows: list[IntakeRowResult], issues: list[IntakeIssue], *, preview_mode: bool) -> IntakeSummary:
    counts = Counter(row.decision for row in rows)
    error_count = sum(1 for issue in issues if issue.severity == "ERROR")
    warning_count = sum(1 for issue in issues if issue.severity == "WARNING")
    commit_readiness = _determine_commit_readiness(rows, issues)
    non_zero_buckets = sum(1 for key in ("ACCEPT", "SKIP", "REJECT", "REVIEW") if counts.get(key, 0) > 0)
    return IntakeSummary(
        total_rows=len(rows),
        accepted_rows=counts.get("ACCEPT", 0),
        skipped_rows=counts.get("SKIP", 0),
        rejected_rows=counts.get("REJECT", 0),
        review_rows=counts.get("REVIEW", 0),
        issue_count=len(issues),
        error_count=error_count,
        warning_count=warning_count,
        partial_completion=non_zero_buckets > 1 or counts.get("SKIP", 0) > 0 or counts.get("REVIEW", 0) > 0,
        preview_mode=preview_mode,
        commit_readiness=commit_readiness,
    )


def _determine_commit_readiness(rows: list[IntakeRowResult], issues: list[IntakeIssue]) -> CommitReadiness:
    if any(issue.scope == "STRUCTURE" and issue.severity == "ERROR" for issue in issues):
        return "BLOCKED"
    if any(issue.scope == "SOURCE" and issue.severity == "ERROR" for issue in issues):
        return "BLOCKED"
    if rows and all(row.decision in {"REJECT", "SKIP"} for row in rows):
        return "BLOCKED"
    if any(row.decision == "REVIEW" for row in rows):
        return "REVIEW_REQUIRED"
    return "READY_TO_COMMIT"
