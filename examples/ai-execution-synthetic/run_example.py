from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
AI_EXECUTION_SRC = REPO_ROOT / "packages" / "ai-execution" / "src"
if str(AI_EXECUTION_SRC) not in sys.path:
    sys.path.insert(0, str(AI_EXECUTION_SRC))

from atlas_ai_execution import (  # noqa: E402
    AIExecutionRequest,
    EvidenceReference,
    ProviderResponse,
    execute_ai_request,
)


class SyntheticProvider:
    name = "synthetic-provider"

    def __init__(self, *, fail: bool = False):
        self.fail = fail

    def invoke(self, request: AIExecutionRequest) -> ProviderResponse:
        if self.fail:
            raise RuntimeError("synthetic provider unavailable")
        return ProviderResponse(
            content=json.dumps(
                {
                    "answer": "Synthetic analysis completed.",
                    "confidence": "medium",
                    "risk_level": "high",
                    "manual_required": True,
                    "escalation_reasons": ["synthetic high-risk result needs review"],
                }
            ),
            provider=self.name,
            model="synthetic-model",
            trace={"adapter_mode": "synthetic-public"},
        )


def fallback_result(_request: AIExecutionRequest, exc: BaseException) -> dict[str, Any]:
    return {
        "answer": "Synthetic fallback result.",
        "confidence": "low",
        "risk_level": "medium",
        "manual_required": True,
        "fallback_reason": type(exc).__name__,
    }


def to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    return value


def main() -> int:
    request = AIExecutionRequest(
        input_payload={"task": "synthetic_quality_check", "record_id": "SYN-001"},
        expected_output="JSON_OBJECT",
        evidence=[EvidenceReference(id="SYN-EVIDENCE-001", source="synthetic_fixture", reference="sample")],
        risk_level="MEDIUM",
        trace={"example": "ai-execution-synthetic"},
    )

    success = execute_ai_request(request, SyntheticProvider())
    failure_with_fallback = execute_ai_request(request, SyntheticProvider(fail=True), fallback=fallback_result)

    payload = {
        "summary": {
            "success_status": success.status,
            "success_confidence": success.confidence,
            "success_risk_level": success.risk_level,
            "success_escalation": success.human_escalation_required,
            "failure_status": failure_with_fallback.status,
            "failure_type": failure_with_fallback.failure_type,
            "fallback_used": failure_with_fallback.fallback_used,
            "fallback_confidence": failure_with_fallback.confidence,
            "fallback_risk_level": failure_with_fallback.risk_level,
            "fallback_escalation": failure_with_fallback.human_escalation_required,
        },
        "success": to_plain(success),
        "failure_with_fallback": to_plain(failure_with_fallback),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
