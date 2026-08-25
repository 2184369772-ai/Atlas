from __future__ import annotations

from typing import Any

from .models import EvidenceReference, OperationOutcome, OutcomeIssue, OutcomeStatus


def build_operation_outcome(
    *,
    status: OutcomeStatus,
    summary: str = "",
    issues: list[OutcomeIssue] | None = None,
    evidence: list[EvidenceReference] | None = None,
    affected_scope: list[str] | None = None,
    remaining_scope: list[str] | None = None,
    confidence: str = "UNKNOWN",
    risk_level: str = "UNKNOWN",
    human_attention_required: bool | None = None,
    fallback_used: bool = False,
    trace: dict[str, Any] | None = None,
) -> OperationOutcome:
    issue_items = list(issues or [])
    attention = (
        status in {"BLOCKED", "REVIEW_REQUIRED"}
        or any(issue.severity == "ERROR" for issue in issue_items)
        if human_attention_required is None
        else human_attention_required
    )
    return OperationOutcome(
        status=status,
        summary=summary,
        issues=issue_items,
        evidence=list(evidence or []),
        affected_scope=list(affected_scope or []),
        remaining_scope=list(remaining_scope or []),
        confidence=_confidence(confidence),
        risk_level=_risk(risk_level),
        human_attention_required=attention,
        fallback_used=fallback_used,
        trace=dict(trace or {}),
    )


def _confidence(value: str) -> str:
    normalized = str(value or "UNKNOWN").upper()
    return normalized if normalized in {"UNKNOWN", "LOW", "MEDIUM", "HIGH"} else "UNKNOWN"


def _risk(value: str) -> str:
    normalized = str(value or "UNKNOWN").upper()
    return normalized if normalized in {"UNKNOWN", "LOW", "MEDIUM", "HIGH"} else "UNKNOWN"
