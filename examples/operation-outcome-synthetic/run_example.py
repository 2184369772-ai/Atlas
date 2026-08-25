from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATION_SRC = REPO_ROOT / "packages" / "operation-outcome" / "src"
if str(OPERATION_SRC) not in sys.path:
    sys.path.insert(0, str(OPERATION_SRC))

from atlas_operation_outcome import EvidenceReference, OutcomeIssue, build_operation_outcome  # noqa: E402


def main() -> int:
    outcome = build_operation_outcome(
        status="PARTIAL",
        summary="Synthetic operation completed with reviewable warnings.",
        issues=[
            OutcomeIssue(
                code="row_warning",
                severity="WARNING",
                message="One row requires review before commit.",
                scope="row:2",
            )
        ],
        evidence=[EvidenceReference(id="synthetic-trace-1", source="synthetic", reference="example://operation/1")],
        affected_scope=["accepted_rows=9"],
        remaining_scope=["review_rows=1"],
        confidence="MEDIUM",
        risk_level="MEDIUM",
        human_attention_required=True,
    )
    print(json.dumps(asdict(outcome), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
