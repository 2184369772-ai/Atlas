from __future__ import annotations

import re
from pathlib import Path
from time import perf_counter
from typing import Any

from .errors import (
    CANONICAL_CELL_DATE_NUMERIC_PARSE_DIFFERENCE,
    CANONICAL_HEADER_DUPLICATED,
    CANONICAL_HEADER_EMPTY,
    CANONICAL_HEADER_UNMAPPED,
    CANONICAL_ROW_LIMIT_EXCEEDED,
    CELL_KIND_BLANK,
    CELL_KIND_BOOLEAN,
    CELL_KIND_DATE,
    CELL_KIND_NUMERIC,
    CELL_KIND_TEXT,
    ERROR,
    ENTITY_CELL,
    ENTITY_HEADER,
    ISSUE_KIND_STRUCTURAL,
    ISSUE_KIND_WARNING,
    HEADER_DUPLICATED,
    HEADER_EMPTY,
    HEADER_UNMAPPED,
    LIMIT_MAX_ROWS_EXCEEDED,
    RESULT_TRUNCATED,
    SCOPE_HEADER,
    SCOPE_LIMIT,
    WARNING,
)
from .models import Cell, Header, Metadata, Summary, TabularIssue, TabularResult


DATE_TEXT_RE = re.compile(r"^\d{4}[-/.]\d{1,2}[-/.]\d{1,2}$")


def normalize_header(value: Any) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\ufeff", "").strip()
    return re.sub(r"\s+", " ", text)


def normalize_cell(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\ufeff", "").strip()
    return value


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def is_empty_row(values: list[Any]) -> bool:
    return all(is_blank(value) for value in values)


def source_name_from(source: str | bytes | Path, source_name: str | None) -> str:
    if source_name:
        return source_name
    if isinstance(source, (str, Path)):
        return Path(source).name
    return "<bytes>"


def start_result(source_name: str, detected_format: str) -> TabularResult:
    return TabularResult(
        metadata=Metadata(source_name=source_name, detected_format=detected_format),
        summary=Summary(format=detected_format),
    )


def finish_result(result: TabularResult, started_at: float) -> TabularResult:
    result.metadata.duration_ms = int((perf_counter() - started_at) * 1000)
    result.summary.error_count = len(result.errors)
    result.summary.warning_count = len(result.warnings)
    result.summary.returned_rows = len(result.rows)
    return result


def set_header_summary(result: TabularResult) -> None:
    result.summary.header_count = len(result.headers)
    result.summary.mapped_header_count = sum(1 for header in result.headers if header.field_key)
    result.summary.unmapped_header_count = result.summary.header_count - result.summary.mapped_header_count


def mark_truncated(result: TabularResult, source_row_index: int) -> None:
    result.summary.truncated = True
    result.errors.append(
        make_issue(
            LIMIT_MAX_ROWS_EXCEEDED,
            ERROR,
            SCOPE_LIMIT,
            "Maximum returned rows exceeded.",
            row=source_row_index,
            suggestion="Increase max_rows or split the file.",
            entity="row",
            issue_kind=ISSUE_KIND_STRUCTURAL,
            canonical_code=CANONICAL_ROW_LIMIT_EXCEEDED,
        )
    )
    result.warnings.append(
        make_issue(
            RESULT_TRUNCATED,
            WARNING,
            SCOPE_LIMIT,
            "Result was truncated by max_rows.",
            row=source_row_index,
            entity="summary",
            issue_kind=ISSUE_KIND_WARNING,
        )
    )


def build_headers(raw_headers: list[Any], header_mapping: dict[str, str] | None) -> tuple[list[Header], list[TabularIssue]]:
    mapping = {normalize_header(key): value for key, value in (header_mapping or {}).items()}
    seen: dict[str, int] = {}
    headers: list[Header] = []
    warnings: list[TabularIssue] = []

    for column_index, raw_label in enumerate(raw_headers, start=1):
        label = "" if raw_label is None else str(raw_label)
        normalized = normalize_header(raw_label)
        count = seen.get(normalized, 0)
        seen[normalized] = count + 1
        field_key = mapping.get(normalized)
        is_empty = normalized == ""
        is_duplicate = normalized != "" and count > 0

        headers.append(
            Header(
                column_index=column_index,
                label=label,
                normalized_label=normalized,
                field_key=field_key,
                is_empty=is_empty,
                is_duplicate=is_duplicate,
            )
        )

        if is_empty:
            warnings.append(
                make_issue(
                    code=HEADER_EMPTY,
                    severity=WARNING,
                    scope=SCOPE_HEADER,
                    message="Header is empty.",
                    column=column_index,
                    original_value=raw_label,
                    suggestion="Provide a header label or ignore this column in the caller.",
                    entity=ENTITY_HEADER,
                    issue_kind=ISSUE_KIND_STRUCTURAL,
                    canonical_code=CANONICAL_HEADER_EMPTY,
                )
            )
        elif is_duplicate:
            warnings.append(
                make_issue(
                    code=HEADER_DUPLICATED,
                    severity=WARNING,
                    scope=SCOPE_HEADER,
                    message="Header label is duplicated.",
                    column=column_index,
                    original_value=raw_label,
                    suggestion="Rename duplicated headers if the caller needs stable mapping.",
                    entity=ENTITY_HEADER,
                    issue_kind=ISSUE_KIND_STRUCTURAL,
                    canonical_code=CANONICAL_HEADER_DUPLICATED,
                )
            )
        elif header_mapping is not None and field_key is None:
            warnings.append(
                make_issue(
                    code=HEADER_UNMAPPED,
                    severity=WARNING,
                    scope=SCOPE_HEADER,
                    message="Header was not mapped by caller-provided header_mapping.",
                    column=column_index,
                    original_value=raw_label,
                    suggestion="Add this header to header_mapping if it should be mapped.",
                    entity=ENTITY_HEADER,
                    issue_kind=ISSUE_KIND_WARNING,
                    canonical_code=CANONICAL_HEADER_UNMAPPED,
                )
            )

    return headers, warnings


def mapped_values(headers: list[Header], values: list[Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for index, header in enumerate(headers):
        if header.field_key:
            output[header.field_key] = values[index] if index < len(values) else None
    return output


def make_issue(
    code: str,
    severity: str,
    scope: str,
    message: str,
    *,
    row: int | None = None,
    column: int | None = None,
    field: str | None = None,
    original_value: Any = None,
    suggestion: str | None = None,
    entity: str | None = None,
    issue_kind: str | None = None,
    canonical_code: str | None = None,
) -> TabularIssue:
    return TabularIssue(
        code=code,
        severity=severity,
        scope=scope,
        message=message,
        row=row,
        column=column,
        field=field,
        original_value=original_value,
        suggestion=suggestion,
        entity=entity,
        issue_kind=issue_kind,
        canonical_code=canonical_code,
    )


def basic_cell_kind(value: Any) -> str:
    if value is None:
        return CELL_KIND_BLANK
    if isinstance(value, bool):
        return CELL_KIND_BOOLEAN
    if isinstance(value, (int, float)):
        return CELL_KIND_NUMERIC
    return CELL_KIND_TEXT


def make_basic_cell(column_index: int, value: Any) -> Cell:
    return Cell(
        column_index=column_index,
        value=value,
        kind=basic_cell_kind(value),
        source_kind=basic_cell_kind(value),
    )


def add_date_numeric_parse_warnings(result: TabularResult) -> None:
    column_kinds: dict[int, set[str]] = {}
    for row in result.rows:
        for cell in row.cells:
            if cell.kind in {CELL_KIND_DATE, CELL_KIND_NUMERIC}:
                column_kinds.setdefault(cell.column_index, set()).add(cell.kind)

    for header in result.headers:
        kinds = column_kinds.get(header.column_index, set())
        if CELL_KIND_DATE in kinds and CELL_KIND_NUMERIC in kinds:
            result.warnings.append(
                make_issue(
                    code="DATE_NUMERIC_PARSE_DIFFERENCE",
                    severity=WARNING,
                    scope=SCOPE_HEADER,
                    message="Column mixes date-normalized and numeric-normalized cell values.",
                    column=header.column_index,
                    original_value=header.label,
                    suggestion="Normalize the source workbook so the column uses one date/numeric representation.",
                    entity=ENTITY_CELL,
                    issue_kind=ISSUE_KIND_STRUCTURAL,
                    canonical_code=CANONICAL_CELL_DATE_NUMERIC_PARSE_DIFFERENCE,
                )
            )
