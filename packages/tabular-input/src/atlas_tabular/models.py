from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Metadata:
    source_name: str
    detected_format: str
    encoding: str | None = None
    selected_table: str | None = None
    selected_sheet: str | None = None
    header_row_index: int | None = None
    duration_ms: int = 0


@dataclass(slots=True)
class Header:
    column_index: int
    label: str
    normalized_label: str
    field_key: str | None = None
    is_empty: bool = False
    is_duplicate: bool = False


@dataclass(slots=True)
class Cell:
    column_index: int
    value: Any
    kind: str
    source_kind: str | None = None
    has_formula: bool = False
    has_cached_value: bool | None = None


@dataclass(slots=True)
class Row:
    row_index: int
    source_row_index: int
    raw_values: list[Any]
    cells: list[Cell] = field(default_factory=list)
    mapped_values: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TabularIssue:
    code: str
    severity: str
    scope: str
    message: str
    row: int | None = None
    column: int | None = None
    field: str | None = None
    original_value: Any = None
    suggestion: str | None = None
    entity: str | None = None
    issue_kind: str | None = None
    canonical_code: str | None = None


@dataclass(slots=True)
class Summary:
    total_physical_rows: int = 0
    total_data_rows: int = 0
    returned_rows: int = 0
    skipped_rows: int = 0
    header_count: int = 0
    mapped_header_count: int = 0
    unmapped_header_count: int = 0
    error_count: int = 0
    warning_count: int = 0
    truncated: bool = False
    format: str = ""


@dataclass(slots=True)
class TabularResult:
    metadata: Metadata
    headers: list[Header] = field(default_factory=list)
    rows: list[Row] = field(default_factory=list)
    errors: list[TabularIssue] = field(default_factory=list)
    warnings: list[TabularIssue] = field(default_factory=list)
    summary: Summary = field(default_factory=Summary)
