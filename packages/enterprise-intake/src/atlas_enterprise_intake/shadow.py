from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .models import IntakePreview


ShadowDiffKind = Literal[
    "MATCH",
    "CORE_DIFFERENCE",
    "ADAPTER_DIFFERENCE",
    "BUSINESS_ONLY_DIFFERENCE",
    "ACCEPTABLE_DIFFERENCE",
]


@dataclass(slots=True)
class ShadowIssueSnapshot:
    code: str
    severity: str
    row: int | None = None
    field: str | None = None
    source_column: str | None = None
    message: str = ""

    def key(self) -> tuple[str, str, int | None, str | None, str | None]:
        return (self.code, self.severity, self.row, self.field, self.source_column)


@dataclass(slots=True)
class ShadowRowSnapshot:
    source_row_index: int
    decision: str
    issues: list[ShadowIssueSnapshot] = field(default_factory=list)
    duplicate_intent: str = ""
    trace_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ShadowRunSnapshot:
    source_name: str
    rows: list[ShadowRowSnapshot]
    commit_readiness: str
    accepted_rows: int
    skipped_rows: int
    rejected_rows: int
    review_rows: int
    partial_completion: bool
    global_issues: list[ShadowIssueSnapshot] = field(default_factory=list)


@dataclass(slots=True)
class ShadowDifference:
    kind: ShadowDiffKind
    scope: str
    row: int | None
    message: str


@dataclass(slots=True)
class ShadowComparison:
    overall: ShadowDiffKind
    differences: list[ShadowDifference] = field(default_factory=list)
    unexplained_differences: int = 0
    lost_issues: int = 0


def preview_to_shadow_snapshot(preview: IntakePreview) -> ShadowRunSnapshot:
    rows = []
    global_issue_map: dict[tuple[str, str, int | None, str | None, str | None], ShadowIssueSnapshot] = {}
    for row in preview.rows:
        duplicate_intent = ""
        row_issues: list[ShadowIssueSnapshot] = []
        trace_metadata = dict(row.trace)
        for issue in row.issues:
            if "DUPLICATE" in issue.code.upper():
                duplicate_intent = issue.code
            snapshot = ShadowIssueSnapshot(
                code=issue.code,
                severity=issue.severity,
                row=issue.row,
                field=issue.field,
                source_column=issue.source_column,
                message=issue.message,
            )
            if issue.source_column and issue.scope == "MAPPING":
                snapshot.row = None
                global_issue_map[snapshot.key()] = snapshot
            else:
                row_issues.append(snapshot)
        if not duplicate_intent:
            duplicate_intent = str(trace_metadata.get("duplicate_intent", "") or "")
        trace_metadata.pop("duplicate_intent", None)
        rows.append(
            ShadowRowSnapshot(
                source_row_index=row.source_row_index,
                decision=row.decision,
                issues=row_issues,
                duplicate_intent=duplicate_intent,
                trace_metadata=trace_metadata,
            )
        )
    return ShadowRunSnapshot(
        source_name=preview.source_name,
        rows=rows,
        commit_readiness=preview.summary.commit_readiness,
        accepted_rows=preview.summary.accepted_rows,
        skipped_rows=preview.summary.skipped_rows,
        rejected_rows=preview.summary.rejected_rows,
        review_rows=preview.summary.review_rows,
        partial_completion=preview.summary.partial_completion,
        global_issues=list(global_issue_map.values()),
    )


def compare_primary_vs_atlas(primary: ShadowRunSnapshot, atlas: ShadowRunSnapshot) -> ShadowComparison:
    differences: list[ShadowDifference] = []
    lost_issues = 0
    unexplained = 0

    if primary.commit_readiness != atlas.commit_readiness:
        differences.append(
            ShadowDifference(
                kind="CORE_DIFFERENCE",
                scope="summary.commit_readiness",
                row=None,
                message=f"Primary={primary.commit_readiness}, Atlas={atlas.commit_readiness}",
            )
        )
        unexplained += 1

    summary_keys = ("accepted_rows", "skipped_rows", "rejected_rows", "review_rows", "partial_completion")
    for key in summary_keys:
        if getattr(primary, key) != getattr(atlas, key):
            differences.append(
                ShadowDifference(
                    kind="CORE_DIFFERENCE",
                    scope=f"summary.{key}",
                    row=None,
                    message=f"Primary={getattr(primary, key)!r}, Atlas={getattr(atlas, key)!r}",
                )
            )
            unexplained += 1

    primary_global = {issue.key() for issue in primary.global_issues}
    atlas_global = {issue.key() for issue in atlas.global_issues}
    for missing_key in sorted(primary_global - atlas_global):
        differences.append(
            ShadowDifference(
                kind="CORE_DIFFERENCE",
                scope="global_issue.lost",
                row=None,
                message=f"Missing Atlas global issue {missing_key!r}",
            )
        )
        unexplained += 1
        lost_issues += 1
    for extra_key in sorted(atlas_global - primary_global):
        differences.append(
            ShadowDifference(
                kind="ACCEPTABLE_DIFFERENCE",
                scope="global_issue.extra",
                row=None,
                message=f"Extra Atlas global issue {extra_key!r}",
            )
        )

    primary_rows = {row.source_row_index: row for row in primary.rows}
    atlas_rows = {row.source_row_index: row for row in atlas.rows}
    if set(primary_rows) != set(atlas_rows):
        differences.append(
            ShadowDifference(
                kind="CORE_DIFFERENCE",
                scope="rows",
                row=None,
                message=f"Primary rows={sorted(primary_rows)}, Atlas rows={sorted(atlas_rows)}",
            )
        )
        unexplained += 1

    for source_row, primary_row in primary_rows.items():
        atlas_row = atlas_rows.get(source_row)
        if atlas_row is None:
            continue
        if primary_row.decision != atlas_row.decision:
            differences.append(
                ShadowDifference(
                    kind="ADAPTER_DIFFERENCE",
                    scope="row.decision",
                    row=source_row,
                    message=f"Primary={primary_row.decision}, Atlas={atlas_row.decision}",
                )
            )
            unexplained += 1
        if primary_row.duplicate_intent != atlas_row.duplicate_intent:
            differences.append(
                ShadowDifference(
                    kind="ADAPTER_DIFFERENCE",
                    scope="row.duplicate_intent",
                    row=source_row,
                    message=f"Primary={primary_row.duplicate_intent!r}, Atlas={atlas_row.duplicate_intent!r}",
                )
            )
            unexplained += 1
        primary_issue_keys = {issue.key() for issue in primary_row.issues}
        atlas_issue_keys = {issue.key() for issue in atlas_row.issues}
        missing_issue_keys = primary_issue_keys - atlas_issue_keys
        extra_issue_keys = atlas_issue_keys - primary_issue_keys
        for missing_key in sorted(missing_issue_keys):
            lost_issues += 1
            differences.append(
                ShadowDifference(
                    kind="CORE_DIFFERENCE",
                    scope="row.issue.lost",
                    row=source_row,
                    message=f"Missing Atlas issue {missing_key!r}",
                )
            )
            unexplained += 1
        for extra_key in sorted(extra_issue_keys):
            differences.append(
                ShadowDifference(
                    kind="ACCEPTABLE_DIFFERENCE",
                    scope="row.issue.extra",
                    row=source_row,
                    message=f"Extra Atlas issue {extra_key!r}",
                )
            )
        primary_trace = dict(primary_row.trace_metadata)
        atlas_trace = dict(atlas_row.trace_metadata)
        if primary_trace != atlas_trace:
            differences.append(
                ShadowDifference(
                    kind="BUSINESS_ONLY_DIFFERENCE",
                    scope="row.trace_metadata",
                    row=source_row,
                    message=f"Primary={primary_trace!r}, Atlas={atlas_trace!r}",
                )
            )

    overall: ShadowDiffKind = "MATCH"
    priority = {
        "MATCH": 0,
        "ACCEPTABLE_DIFFERENCE": 1,
        "BUSINESS_ONLY_DIFFERENCE": 2,
        "ADAPTER_DIFFERENCE": 3,
        "CORE_DIFFERENCE": 4,
    }
    for difference in differences:
        if priority[difference.kind] > priority[overall]:
            overall = difference.kind
    return ShadowComparison(
        overall=overall,
        differences=differences,
        unexplained_differences=unexplained,
        lost_issues=lost_issues,
    )
