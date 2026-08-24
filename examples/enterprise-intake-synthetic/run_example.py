from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
TABULAR_SRC = REPO_ROOT / "packages" / "tabular-input" / "src"
INTAKE_SRC = REPO_ROOT / "packages" / "enterprise-intake" / "src"

for package_src in (TABULAR_SRC, INTAKE_SRC):
    package_str = str(package_src)
    if package_str not in sys.path:
        sys.path.insert(0, package_str)

from atlas_enterprise_intake import HookedAdapter, IntakeIssue, IntakeRowDecision, build_preview_with_adapter  # noqa: E402
from atlas_tabular import read_tabular  # noqa: E402


def to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    return value


def build_adapter() -> HookedAdapter:
    def field_mapping(_headers):
        return {
            "employee_id": "employee_id",
            "hours": "planned_hours",
            "manager": "manager_username",
        }

    def evaluate(row):
        hours = parse_number(row.mapped_values.get("planned_hours"))
        manager = str(row.mapped_values.get("manager_username", "") or "").strip()
        if isinstance(hours, (int, float)) and hours < 0:
            return IntakeRowDecision(
                decision="REJECT",
                issues=[
                    IntakeIssue(
                        code="NEGATIVE_HOURS",
                        severity="ERROR",
                        scope="FIELD",
                        field="planned_hours",
                        message="Hours cannot be negative.",
                    )
                ],
            )
        if not manager:
            return IntakeRowDecision(
                decision="REVIEW",
                issues=[
                    IntakeIssue(
                        code="MANAGER_LOOKUP_PENDING",
                        severity="WARNING",
                        scope="FIELD",
                        field="manager_username",
                        message="Manager must be confirmed by a human.",
                    )
                ],
            )
        if hours == 0:
            return IntakeRowDecision(
                decision="SKIP",
                issues=[
                    IntakeIssue(
                        code="ZERO_HOURS_SKIP",
                        severity="WARNING",
                        scope="ROW",
                        message="Zero-hour row will be skipped.",
                    )
                ],
            )
        return IntakeRowDecision(
            decision="ACCEPT",
            normalized_values={
                "employee_id": row.mapped_values.get("employee_id"),
                "planned_hours": hours,
                "manager_username": manager,
            },
        )

    def trace(row, _decision):
        return {"source_row": row.source_row_index, "adapter_mode": "synthetic-public"}

    return HookedAdapter(
        row_evaluator=evaluate,
        field_mapping_hook=field_mapping,
        trace_metadata_hook=trace,
    )


def parse_number(value: Any) -> float | int | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        text = str(value).strip()
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return None


def main() -> int:
    sample_path = Path(__file__).with_name("sample.csv")
    tabular_result = read_tabular(sample_path)
    preview = build_preview_with_adapter(tabular_result, build_adapter())
    print(json.dumps(to_plain(preview), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
