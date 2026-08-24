from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AI_EXECUTION_SRC = REPO_ROOT / "packages" / "ai-execution" / "src"
if str(AI_EXECUTION_SRC) not in sys.path:
    sys.path.insert(0, str(AI_EXECUTION_SRC))

from atlas_ai_execution import AIExecutionRequest, ProviderResponse, execute_ai_request  # noqa: E402


class SyntheticProvider:
    name = "synthetic-provider"

    def __init__(self, *, fail: bool = False):
        self.fail = fail

    def invoke(self, _request: AIExecutionRequest) -> ProviderResponse:
        if self.fail:
            raise RuntimeError("synthetic provider unavailable")
        return ProviderResponse(
            content='{"answer":"ok","confidence":"medium","risk_level":"high","manual_required":true}',
            provider=self.name,
            model="synthetic-model",
        )


def test_synthetic_provider_success_extracts_result_boundary():
    result = execute_ai_request(
        AIExecutionRequest(input_payload={"task": "synthetic"}, expected_output="JSON_OBJECT"),
        SyntheticProvider(),
    )

    assert result.status == "SUCCESS"
    assert result.confidence == "MEDIUM"
    assert result.risk_level == "HIGH"
    assert result.human_escalation_required is True


def test_synthetic_provider_failure_uses_fallback_boundary():
    result = execute_ai_request(
        AIExecutionRequest(input_payload={"task": "synthetic"}, expected_output="JSON_OBJECT"),
        SyntheticProvider(fail=True),
        fallback=lambda _request, _exc: {
            "answer": "fallback",
            "confidence": "low",
            "risk_level": "medium",
            "manual_required": True,
        },
    )

    assert result.status == "PARTIAL"
    assert result.failure_type == "PROVIDER_FAILURE"
    assert result.fallback_used is True
    assert result.confidence == "LOW"
    assert result.human_escalation_required is True


def test_public_example_runs_without_external_provider():
    completed = subprocess.run(
        [sys.executable, "examples/ai-execution-synthetic/run_example.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["summary"]["success_status"] == "SUCCESS"
    assert payload["summary"]["failure_status"] == "PARTIAL"
    assert payload["summary"]["fallback_used"] is True
