from __future__ import annotations

from dataclasses import dataclass

from .models import ReportSnapshot
from .semantics import report_semantic_issues


@dataclass(slots=True)
class ReportSemanticDifference:
    scope: str
    key: str
    message: str
    explained: bool = False


def compare_report_semantics(primary: ReportSnapshot, atlas: ReportSnapshot) -> list[ReportSemanticDifference]:
    differences: list[ReportSemanticDifference] = []

    primary_dimensions = {dimension.key: dimension for dimension in primary.definition.dimensions}
    atlas_dimensions = {dimension.key: dimension for dimension in atlas.definition.dimensions}
    for key in sorted(primary_dimensions.keys() - atlas_dimensions.keys()):
        differences.append(ReportSemanticDifference("dimension", key, "Atlas lost a primary report dimension."))
    for key in sorted(atlas_dimensions.keys() - primary_dimensions.keys()):
        differences.append(ReportSemanticDifference("dimension", key, "Atlas added a non-primary report dimension.", explained=True))
    for key in sorted(primary_dimensions.keys() & atlas_dimensions.keys()):
        if primary_dimensions[key].semantic_key() != atlas_dimensions[key].semantic_key():
            differences.append(ReportSemanticDifference("dimension", key, "Report dimension semantics differ."))

    primary_metrics = {metric.key: metric for metric in primary.definition.metrics}
    atlas_metrics = {metric.key: metric for metric in atlas.definition.metrics}
    for key in sorted(primary_metrics.keys() - atlas_metrics.keys()):
        differences.append(ReportSemanticDifference("metric", key, "Atlas lost a primary report metric."))
    for key in sorted(atlas_metrics.keys() - primary_metrics.keys()):
        differences.append(ReportSemanticDifference("metric", key, "Atlas added a non-primary report metric.", explained=True))
    for key in sorted(primary_metrics.keys() & atlas_metrics.keys()):
        if primary_metrics[key].semantic_key() != atlas_metrics[key].semantic_key():
            differences.append(ReportSemanticDifference("metric", key, "Report metric semantics differ."))

    primary_sources = {source.key() for source in primary.definition.sources}
    atlas_sources = {source.key() for source in atlas.definition.sources}
    for source in sorted(primary_sources - atlas_sources):
        differences.append(ReportSemanticDifference("source", source[0], "Atlas lost a source fact reference."))

    primary_rows = {row.row_id: row for row in primary.rows}
    atlas_rows = {row.row_id: row for row in atlas.rows}
    for key in sorted(primary_rows.keys() - atlas_rows.keys()):
        differences.append(ReportSemanticDifference("row", key, "Atlas lost a primary report row."))
    for key in sorted(atlas_rows.keys() - primary_rows.keys()):
        differences.append(ReportSemanticDifference("row", key, "Atlas added a non-primary report row.", explained=True))
    for key in sorted(primary_rows.keys() & atlas_rows.keys()):
        if primary_rows[key].semantic_key() != atlas_rows[key].semantic_key():
            differences.append(ReportSemanticDifference("row", key, "Report row semantics differ."))

    if primary.projection and not atlas.projection:
        differences.append(ReportSemanticDifference("projection", primary.projection.projection_id, "Atlas lost the export projection."))
    elif primary.projection and atlas.projection and primary.projection.semantic_key() != atlas.projection.semantic_key():
        differences.append(ReportSemanticDifference("projection", primary.projection.projection_id, "Export projection semantics differ."))

    primary_issue_keys = {issue.key() for issue in report_semantic_issues(primary)}
    atlas_issue_keys = {issue.key() for issue in report_semantic_issues(atlas)}
    for issue in sorted(primary_issue_keys - atlas_issue_keys):
        differences.append(ReportSemanticDifference("issue", issue[0], "Atlas lost a report issue."))

    return differences
