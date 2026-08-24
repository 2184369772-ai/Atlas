from __future__ import annotations

import json
import time
from typing import Any

from .models import (
    AIExecutionIssue,
    AIExecutionRequest,
    AIExecutionResult,
    Confidence,
    FallbackBuilder,
    ProviderInvocation,
)


class ProviderFailureError(RuntimeError):
    pass


class ModelUnavailableError(ProviderFailureError):
    pass


class InvalidStructuredResultError(ProviderFailureError):
    pass


def execute_ai_request(
    request: AIExecutionRequest,
    provider: ProviderInvocation,
    *,
    fallback: FallbackBuilder | None = None,
) -> AIExecutionResult:
    if request.blocked_reason:
        return AIExecutionResult(
            status="BLOCKED",
            issues=[
                AIExecutionIssue(
                    code="EXECUTION_BLOCKED",
                    severity="ERROR",
                    message=request.blocked_reason,
                    scope="REQUEST",
                )
            ],
            evidence=list(request.evidence),
            confidence="LOW",
            risk_level=request.risk_level,
            human_escalation_required=True,
            failure_type="BLOCKED",
            provider=getattr(provider, "name", ""),
            trace=dict(request.trace),
        )

    started = time.monotonic()
    try:
        response = provider.invoke(request)
        elapsed_ms = int((time.monotonic() - started) * 1000)
        structured = response.structured
        content = response.content
        issues: list[AIExecutionIssue] = []
        if request.expected_output == "JSON_OBJECT" and structured is None:
            try:
                structured = parse_json_object(content)
            except (json.JSONDecodeError, ValueError) as exc:
                return _failed_or_partial_from_exception(
                    request,
                    provider,
                    exc,
                    fallback=fallback,
                    code="INVALID_STRUCTURED_RESULT",
                    failure_type="INVALID_RESULT",
                )
        confidence = _extract_confidence(structured)
        human_escalation = _extract_human_escalation(structured) or request.risk_level == "HIGH"
        risk_level = _extract_risk_level(structured, request.risk_level)
        if human_escalation:
            issues.append(
                AIExecutionIssue(
                    code="HUMAN_ESCALATION_REQUIRED",
                    severity="WARNING",
                    message="The AI result requires human review before operational use.",
                    scope="RESULT",
                )
            )
        if risk_level == "HIGH":
            issues.append(
                AIExecutionIssue(
                    code="HIGH_RISK_RESULT",
                    severity="WARNING",
                    message="The execution result carries high operational risk.",
                    scope="RESULT",
                )
            )
        return AIExecutionResult(
            status="SUCCESS",
            content=content,
            structured=structured,
            issues=issues,
            evidence=list(request.evidence),
            confidence=confidence,
            risk_level=risk_level,
            human_escalation_required=human_escalation,
            provider=response.provider or getattr(provider, "name", ""),
            model=response.model,
            trace={**request.trace, **response.trace, "elapsed_ms": elapsed_ms},
        )
    except TimeoutError as exc:
        return _failed_or_partial_from_exception(
            request,
            provider,
            exc,
            fallback=fallback,
            code="PROVIDER_TIMEOUT",
            failure_type="TIMEOUT",
        )
    except ModelUnavailableError as exc:
        return _failed_or_partial_from_exception(
            request,
            provider,
            exc,
            fallback=fallback,
            code="MODEL_UNAVAILABLE",
            failure_type="MODEL_UNAVAILABLE",
        )
    except Exception as exc:
        return _failed_or_partial_from_exception(
            request,
            provider,
            exc,
            fallback=fallback,
            code="PROVIDER_FAILURE",
            failure_type="PROVIDER_FAILURE",
        )


def parse_json_object(content: str) -> dict[str, Any]:
    text = str(content or "").strip()
    if text.startswith("```"):
        text = text.removeprefix("```json").removeprefix("```").strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(text[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("AI provider did not return a JSON object")
    return value


def _failed_or_partial_from_exception(
    request: AIExecutionRequest,
    provider: ProviderInvocation,
    exc: BaseException,
    *,
    fallback: FallbackBuilder | None,
    code: str,
    failure_type: str,
) -> AIExecutionResult:
    fallback_payload = fallback(request, exc) if fallback is not None else None
    fallback_used = fallback_payload is not None
    structured = fallback_payload if isinstance(fallback_payload, dict) else None
    content = fallback_payload if isinstance(fallback_payload, str) else ""
    return AIExecutionResult(
        status="PARTIAL" if fallback_used else "FAILED",
        content=content,
        structured=structured,
        issues=[
            AIExecutionIssue(
                code=code,
                severity="ERROR",
                message=str(exc),
                scope="PROVIDER",
            )
        ],
        evidence=list(request.evidence),
        confidence=_extract_confidence(structured) if structured else "LOW",
        risk_level=_extract_risk_level(structured, request.risk_level) if structured else request.risk_level,
        human_escalation_required=True,
        failure_type=failure_type,  # type: ignore[arg-type]
        fallback_used=fallback_used,
        provider=getattr(provider, "name", ""),
        trace=dict(request.trace),
    )


def _extract_confidence(structured: dict[str, Any] | None) -> Confidence:
    value = str((structured or {}).get("confidence", "")).strip().upper()
    if value in {"LOW", "MEDIUM", "HIGH"}:
        return value  # type: ignore[return-value]
    return "UNKNOWN"


def _extract_risk_level(structured: dict[str, Any] | None, default: str) -> str:
    value = str((structured or {}).get("risk_level", (structured or {}).get("risk", default))).strip().upper()
    if value in {"LOW", "MEDIUM", "HIGH"}:
        return value
    return default


def _extract_human_escalation(structured: dict[str, Any] | None) -> bool:
    if not structured:
        return False
    for key in ("manual_required", "human_escalation_required", "escalation_required"):
        if key in structured:
            return bool(structured[key])
    reasons = structured.get("escalation_reasons")
    return bool(reasons)
