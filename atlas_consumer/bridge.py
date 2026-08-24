from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TABULAR_SRC = REPO_ROOT / "packages" / "tabular-input" / "src"

if str(TABULAR_SRC) not in sys.path:
    sys.path.insert(0, str(TABULAR_SRC))

from atlas_tabular import TabularResult, read_tabular  # noqa: E402


def inspect_file(
    file_path: str | Path,
    *,
    format_hint: str | None = None,
    sheet_name: str | None = None,
    sheet_index: int = 0,
    header_row: int = 1,
    max_rows: int | None = None,
) -> TabularResult:
    return read_tabular(
        Path(file_path),
        format_hint=format_hint,
        sheet_name=sheet_name,
        sheet_index=sheet_index,
        header_row=header_row,
        max_rows=max_rows,
    )


def result_to_payload(result: TabularResult) -> dict[str, Any]:
    payload = _to_plain_value(result)
    payload["issues"] = payload["errors"] + payload["warnings"]
    return payload


def result_to_json(result: TabularResult) -> str:
    return json.dumps(result_to_payload(result), ensure_ascii=False, indent=2)


def _to_plain_value(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _to_plain_value(raw) for key, raw in asdict(value).items()}
    if isinstance(value, dict):
        return {key: _to_plain_value(raw) for key, raw in value.items()}
    if isinstance(value, list):
        return [_to_plain_value(item) for item in value]
    return value
