from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path
from time import perf_counter

from .common import (
    add_date_numeric_parse_warnings,
    build_headers,
    finish_result,
    is_empty_row,
    mark_truncated,
    make_basic_cell,
    make_issue,
    mapped_values,
    normalize_cell,
    set_header_summary,
    source_name_from,
    start_result,
)
from .errors import (
    CANONICAL_ROW_EMPTY,
    CANONICAL_WORKBOOK_EMPTY,
    CANONICAL_WORKBOOK_MISSING,
    EMPTY_ROW_SKIPPED,
    ENCODING_DETECTION_FAILED,
    FILE_EMPTY,
    FILE_NOT_FOUND,
    FILE_OPEN_FAILED,
    FATAL,
    INFO,
    ISSUE_KIND_STRUCTURAL,
    ISSUE_KIND_WARNING,
    SCOPE_INPUT,
    SCOPE_ROW,
    ENTITY_ROW,
    ENTITY_WORKBOOK,
)
from .models import Row, TabularIssue, TabularResult

CSV_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


def read_csv_tabular(
    source: str | bytes | Path,
    *,
    source_name: str | None,
    encoding_hint: str | None,
    header_row: int,
    header_mapping: dict[str, str] | None,
    max_rows: int | None,
    skip_empty_rows: bool,
    started_at: float | None = None,
) -> TabularResult:
    started_at = perf_counter() if started_at is None else started_at
    result = start_result(source_name_from(source, source_name), "csv")
    result.metadata.header_row_index = header_row

    raw = _read_bytes(source, result)
    if raw is None:
        return finish_result(result, started_at)
    if raw == b"":
        result.errors.append(
            make_issue(
                FILE_EMPTY,
                FATAL,
                SCOPE_INPUT,
                "CSV file is empty.",
                entity=ENTITY_WORKBOOK,
                issue_kind=ISSUE_KIND_STRUCTURAL,
                canonical_code=CANONICAL_WORKBOOK_EMPTY,
            )
        )
        return finish_result(result, started_at)

    decoded, encoding = _decode(raw, encoding_hint)
    if decoded is None:
        result.errors.append(
            make_issue(
                ENCODING_DETECTION_FAILED,
                FATAL,
                SCOPE_INPUT,
                "CSV encoding could not be detected.",
                suggestion="Provide encoding_hint or save the file as utf-8-sig, utf-8, or gb18030.",
                entity=ENTITY_WORKBOOK,
                issue_kind=ISSUE_KIND_STRUCTURAL,
            )
        )
        return finish_result(result, started_at)
    result.metadata.encoding = encoding

    rows = list(csv.reader(StringIO(decoded)))
    result.summary.total_physical_rows = len(rows)
    if not rows:
        result.errors.append(
            make_issue(
                FILE_EMPTY,
                FATAL,
                SCOPE_INPUT,
                "CSV file has no rows.",
                entity=ENTITY_WORKBOOK,
                issue_kind=ISSUE_KIND_STRUCTURAL,
                canonical_code=CANONICAL_WORKBOOK_EMPTY,
            )
        )
        return finish_result(result, started_at)
    if header_row < 1 or header_row > len(rows):
        result.errors.append(
            make_issue(
                FILE_EMPTY,
                FATAL,
                SCOPE_INPUT,
                "Header row is outside the CSV row range.",
                row=header_row,
                suggestion="Use a header_row value that exists in the file.",
                entity="header",
                issue_kind=ISSUE_KIND_STRUCTURAL,
                canonical_code="header.missing",
            )
        )
        return finish_result(result, started_at)

    headers, warnings = build_headers(rows[header_row - 1], header_mapping)
    result.headers = headers
    result.warnings.extend(warnings)
    set_header_summary(result)

    for source_row_index, raw_values in enumerate(rows[header_row:], start=header_row + 1):
        values = [normalize_cell(value) for value in raw_values]
        if skip_empty_rows and is_empty_row(values):
            result.summary.skipped_rows += 1
            result.warnings.append(
                make_issue(
                    EMPTY_ROW_SKIPPED,
                    INFO,
                    SCOPE_ROW,
                    "Empty row skipped.",
                    row=source_row_index,
                    entity=ENTITY_ROW,
                    issue_kind=ISSUE_KIND_STRUCTURAL,
                    canonical_code=CANONICAL_ROW_EMPTY,
                )
            )
            continue
        if max_rows is not None and len(result.rows) >= max_rows:
            mark_truncated(result, source_row_index)
            break
        cells = [make_basic_cell(column_index, value) for column_index, value in enumerate(values, start=1)]
        result.rows.append(
            Row(
                row_index=len(result.rows) + 1,
                source_row_index=source_row_index,
                raw_values=values,
                cells=cells,
                mapped_values=mapped_values(headers, values),
            )
        )

    result.summary.total_data_rows = len(result.rows) + result.summary.skipped_rows
    add_date_numeric_parse_warnings(result)
    return finish_result(result, started_at)


def _read_bytes(source: str | bytes | Path, result: TabularResult) -> bytes | None:
    if isinstance(source, bytes):
        return source
    try:
        path = Path(source)
        if not path.exists():
            result.errors.append(
                make_issue(
                    FILE_NOT_FOUND,
                    FATAL,
                    SCOPE_INPUT,
                    "CSV file was not found.",
                    entity=ENTITY_WORKBOOK,
                    issue_kind=ISSUE_KIND_STRUCTURAL,
                    canonical_code=CANONICAL_WORKBOOK_MISSING,
                )
            )
            return None
        return path.read_bytes()
    except OSError as exc:
        result.errors.append(
            make_issue(
                FILE_OPEN_FAILED,
                FATAL,
                SCOPE_INPUT,
                "CSV file could not be opened.",
                original_value=str(exc),
                entity=ENTITY_WORKBOOK,
                issue_kind=ISSUE_KIND_STRUCTURAL,
            )
        )
        return None


def _decode(raw: bytes, encoding_hint: str | None) -> tuple[str | None, str | None]:
    encodings = (encoding_hint,) if encoding_hint else CSV_ENCODINGS
    for encoding in encodings:
        if not encoding:
            continue
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return None, None
