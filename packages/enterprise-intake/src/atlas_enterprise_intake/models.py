from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol


Decision = Literal["ACCEPT", "SKIP", "REJECT", "REVIEW"]
CommitReadiness = Literal["READY_TO_COMMIT", "REVIEW_REQUIRED", "BLOCKED"]


@dataclass(slots=True)
class IntakeRequest:
    source_name: str | None = None
    preview_mode: bool = True
    field_mapping: dict[str, str] = field(default_factory=dict)
    stop_on_structural_errors: bool = False


@dataclass(slots=True)
class IntakeIssue:
    code: str
    severity: str
    scope: str
    message: str
    row: int | None = None
    field: str | None = None
    column: int | None = None
    source_column: str | None = None
    canonical_code: str | None = None
    original_value: Any = None


@dataclass(slots=True)
class IntakeRowInput:
    row_index: int
    source_row_index: int
    raw_values: list[Any]
    values_by_header: dict[str, Any]
    mapped_values: dict[str, Any]


@dataclass(slots=True)
class IntakeRowDecision:
    decision: Decision
    issues: list[IntakeIssue] = field(default_factory=list)
    normalized_values: dict[str, Any] = field(default_factory=dict)
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IntakeRowResult:
    row_index: int
    source_row_index: int
    decision: Decision
    mapped_values: dict[str, Any] = field(default_factory=dict)
    normalized_values: dict[str, Any] = field(default_factory=dict)
    issues: list[IntakeIssue] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class IntakeSummary:
    total_rows: int = 0
    accepted_rows: int = 0
    skipped_rows: int = 0
    rejected_rows: int = 0
    review_rows: int = 0
    issue_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    partial_completion: bool = False
    preview_mode: bool = True
    commit_readiness: CommitReadiness = "READY_TO_COMMIT"


@dataclass(slots=True)
class IntakePreview:
    source_name: str
    table_name: str | None
    request: IntakeRequest
    rows: list[IntakeRowResult] = field(default_factory=list)
    issues: list[IntakeIssue] = field(default_factory=list)
    summary: IntakeSummary = field(default_factory=IntakeSummary)


class IntakeAdapter(Protocol):
    def evaluate_row(self, row: IntakeRowInput) -> IntakeRowDecision: ...
