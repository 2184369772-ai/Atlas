from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TABULAR_SRC = REPO_ROOT / "packages" / "tabular-input" / "src"
INTAKE_SRC = REPO_ROOT / "packages" / "enterprise-intake" / "src"

for path in (str(INTAKE_SRC), str(TABULAR_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

from atlas_enterprise_intake import HookedAdapter, IntakeIssue, IntakeRowDecision, build_preview_with_adapter  # noqa: E402
from atlas_tabular import read_tabular  # noqa: E402


FIXTURE = REPO_ROOT / "examples" / "enterprise-intake-synthetic" / "sample.csv"


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
        return IntakeRowDecision(decision="ACCEPT")

    return HookedAdapter(row_evaluator=evaluate, field_mapping_hook=field_mapping)


def parse_number(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return None


def test_public_synthetic_enterprise_intake_preview():
    result = read_tabular(FIXTURE)
    preview = build_preview_with_adapter(result, build_adapter())

    assert preview.summary.total_rows == 4
    assert preview.summary.accepted_rows == 1
    assert preview.summary.skipped_rows == 1
    assert preview.summary.review_rows == 1
    assert preview.summary.rejected_rows == 1
    assert preview.summary.commit_readiness == "REVIEW_REQUIRED"
    assert preview.summary.partial_completion is True
    assert any(issue.code == "NEGATIVE_HOURS" for issue in preview.issues)
    assert any(issue.code == "MANAGER_LOOKUP_PENDING" for issue in preview.issues)
