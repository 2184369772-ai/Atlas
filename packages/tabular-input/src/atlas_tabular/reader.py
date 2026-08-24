from __future__ import annotations

from pathlib import Path
from time import perf_counter

from .common import finish_result, source_name_from, start_result
from .csv_reader import read_csv_tabular
from .errors import ERROR, FORMAT_UNSUPPORTED, SCOPE_FORMAT
from .models import TabularIssue, TabularResult
from .xlsx_reader import read_xlsx_tabular


def read_tabular(
    source: str | bytes | Path,
    *,
    source_name: str | None = None,
    format_hint: str | None = None,
    encoding_hint: str | None = None,
    header_row: int = 1,
    sheet_name: str | None = None,
    sheet_index: int = 0,
    header_mapping: dict[str, str] | None = None,
    max_rows: int | None = None,
    skip_empty_rows: bool = True,
) -> TabularResult:
    started_at = perf_counter()
    detected_format = _detect_format(source, source_name, format_hint)

    if detected_format == "csv":
        return read_csv_tabular(
            source,
            source_name=source_name,
            encoding_hint=encoding_hint,
            header_row=header_row,
            header_mapping=header_mapping,
            max_rows=max_rows,
            skip_empty_rows=skip_empty_rows,
            started_at=started_at,
        )
    if detected_format == "xlsx":
        return read_xlsx_tabular(
            source,
            source_name=source_name,
            header_row=header_row,
            sheet_name=sheet_name,
            sheet_index=sheet_index,
            header_mapping=header_mapping,
            max_rows=max_rows,
            skip_empty_rows=skip_empty_rows,
            started_at=started_at,
        )

    result = start_result(source_name_from(source, source_name), detected_format or "unknown")
    result.errors.append(
        TabularIssue(
            code=FORMAT_UNSUPPORTED,
            severity=ERROR,
            scope=SCOPE_FORMAT,
            message="Unsupported tabular input format.",
            suggestion="Use .csv or .xlsx, or provide format_hint='csv' or 'xlsx'.",
        )
    )
    return finish_result(result, started_at)


def _detect_format(source: str | bytes | Path, source_name: str | None, format_hint: str | None) -> str:
    if format_hint:
        return format_hint.lower().lstrip(".")
    candidate = source_name
    if candidate is None and isinstance(source, (str, Path)):
        candidate = str(source)
    suffix = Path(candidate or "").suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".xlsx":
        return "xlsx"
    return "unknown"
