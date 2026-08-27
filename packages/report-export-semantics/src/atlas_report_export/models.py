from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


Aggregation = Literal["NONE", "SUM", "COUNT", "AVG", "MIN", "MAX", "DERIVED"]
MetricRole = Literal["FACT", "PLAN", "ACTUAL", "VARIANCE", "DERIVED", "COUNT"]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]
SourceType = Literal["TABLE", "QUERY", "FILE", "API", "SNAPSHOT", "PROJECT_RECORD", "UNKNOWN"]


@dataclass(slots=True)
class ReportSource:
    source_id: str
    source_type: SourceType = "UNKNOWN"
    reference: str = ""
    version: str = ""
    as_of: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str, str, str]:
        return (self.source_id, self.source_type, self.reference, self.version, self.as_of)


@dataclass(slots=True)
class ReportDimension:
    key: str
    label: str = ""
    source_field: str = ""
    groupable: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[str, str, bool]:
        return (self.key, self.source_field, self.groupable)


@dataclass(slots=True)
class ReportMetric:
    key: str
    role: MetricRole
    aggregation: Aggregation = "NONE"
    label: str = ""
    source_field: str = ""
    derived_from: list[str] = field(default_factory=list)
    formula_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[str, str, str, str, tuple[str, ...], str]:
        return (self.key, self.role, self.aggregation, self.source_field, tuple(sorted(self.derived_from)), self.formula_ref)


@dataclass(slots=True)
class ReportIssue:
    code: str
    severity: IssueSeverity
    message: str
    row_id: str | None = None
    field: str | None = None
    source_id: str | None = None

    def key(self) -> tuple[str, str, str | None, str | None, str | None]:
        return (self.code, self.severity, self.row_id, self.field, self.source_id)


@dataclass(slots=True)
class ReportRow:
    row_id: str
    dimensions: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    source_refs: list[str] = field(default_factory=list)
    issues: list[ReportIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.row_id,
            tuple(sorted((key, repr(value)) for key, value in self.dimensions.items())),
            tuple(sorted((key, repr(value)) for key, value in self.metrics.items())),
            tuple(sorted(self.source_refs)),
            tuple(issue.key() for issue in self.issues),
        )


@dataclass(slots=True)
class ExportProjection:
    projection_id: str
    fields: list[str]
    export_format: Literal["TABLE", "CSV", "XLSX", "JSON"] = "TABLE"
    generated_from_snapshot_id: str = ""
    source_mutation_allowed: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[str, tuple[str, ...], str, str, bool]:
        return (
            self.projection_id,
            tuple(self.fields),
            self.export_format,
            self.generated_from_snapshot_id,
            self.source_mutation_allowed,
        )


@dataclass(slots=True)
class ReportDefinition:
    report_id: str
    dimensions: list[ReportDimension] = field(default_factory=list)
    metrics: list[ReportMetric] = field(default_factory=list)
    sources: list[ReportSource] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def dimension_keys(self) -> set[str]:
        return {dimension.key for dimension in self.dimensions}

    def metric_keys(self) -> set[str]:
        return {metric.key for metric in self.metrics}


@dataclass(slots=True)
class ReportSnapshot:
    snapshot_id: str
    definition: ReportDefinition
    rows: list[ReportRow] = field(default_factory=list)
    as_of: str = ""
    projection: ExportProjection | None = None
    issues: list[ReportIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
