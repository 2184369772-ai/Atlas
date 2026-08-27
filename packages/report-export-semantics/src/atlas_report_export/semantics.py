from __future__ import annotations

from .models import ReportIssue, ReportSnapshot


def report_semantic_issues(snapshot: ReportSnapshot) -> list[ReportIssue]:
    issues: list[ReportIssue] = list(snapshot.issues)
    dimension_keys = snapshot.definition.dimension_keys()
    metric_keys = snapshot.definition.metric_keys()
    known_fields = dimension_keys | metric_keys

    if not snapshot.definition.sources:
        issues.append(ReportIssue("report.source_missing", "ERROR", "Report definition requires at least one source fact reference."))

    if snapshot.projection:
        for field in snapshot.projection.fields:
            if field not in known_fields:
                issues.append(
                    ReportIssue(
                        "report.projection_field_missing",
                        "ERROR",
                        "Export projection references a field not present in dimensions or metrics.",
                        field=field,
                    )
                )
        if snapshot.projection.source_mutation_allowed:
            issues.append(
                ReportIssue(
                    "report.projection_mutates_source",
                    "ERROR",
                    "Report/export projection must not be modeled as a source-fact mutation.",
                )
            )

    for row in snapshot.rows:
        if not row.source_refs:
            issues.append(
                ReportIssue(
                    "report.row_source_trace_missing",
                    "WARNING",
                    "Report row has no source trace reference.",
                    row_id=row.row_id,
                )
            )
        for key in row.dimensions:
            if key not in dimension_keys:
                issues.append(
                    ReportIssue(
                        "report.row_dimension_unknown",
                        "ERROR",
                        "Report row uses a dimension not present in the definition.",
                        row_id=row.row_id,
                        field=key,
                    )
                )
        for key in row.metrics:
            if key not in metric_keys:
                issues.append(
                    ReportIssue(
                        "report.row_metric_unknown",
                        "ERROR",
                        "Report row uses a metric not present in the definition.",
                        row_id=row.row_id,
                        field=key,
                    )
                )
        issues.extend(row.issues)

    return issues
