from __future__ import annotations

from typing import Any

from .models import EvidenceReference, OperationOutcome, OutcomeIssue
from .outcome import build_operation_outcome


def outcome_from_enterprise_intake(preview: Any) -> OperationOutcome:
    summary = getattr(preview, "summary")
    readiness = getattr(summary, "commit_readiness", "READY_TO_COMMIT")
    status = {
        "READY_TO_COMMIT": "SUCCESS",
        "REVIEW_REQUIRED": "REVIEW_REQUIRED",
        "BLOCKED": "BLOCKED",
    }.get(readiness, "REVIEW_REQUIRED")
    if status == "SUCCESS" and getattr(summary, "partial_completion", False):
        status = "PARTIAL"

    issues = [_issue_from_intake_issue(issue) for issue in list(getattr(preview, "issues", []))]
    for row in getattr(preview, "rows", []):
        issues.extend(_issue_from_intake_issue(issue) for issue in getattr(row, "issues", []))

    affected = [
        f"accepted_rows:{getattr(summary, 'accepted_rows', 0)}",
        f"review_rows:{getattr(summary, 'review_rows', 0)}",
        f"rejected_rows:{getattr(summary, 'rejected_rows', 0)}",
    ]
    remaining = []
    if getattr(summary, "review_rows", 0):
        remaining.append("rows_require_review")
    if getattr(summary, "rejected_rows", 0):
        remaining.append("rows_blocked_or_rejected")

    return build_operation_outcome(
        status=status,  # type: ignore[arg-type]
        summary=f"Enterprise intake {readiness}",
        issues=issues,
        affected_scope=affected,
        remaining_scope=remaining,
        human_attention_required=status in {"REVIEW_REQUIRED", "BLOCKED"} or bool(remaining),
        trace={"source": "enterprise-intake", "source_name": getattr(preview, "source_name", "")},
    )


def outcome_from_ai_execution(result: Any) -> OperationOutcome:
    status = getattr(result, "status", "FAILED")
    issues = [
        OutcomeIssue(
            code=str(getattr(issue, "code", "")),
            severity=str(getattr(issue, "severity", "ERROR")).upper(),  # type: ignore[arg-type]
            message=str(getattr(issue, "message", "")),
            scope=str(getattr(issue, "scope", "EXECUTION")),
            evidence_id=getattr(issue, "evidence_id", None),
        )
        for issue in getattr(result, "issues", [])
    ]
    evidence = [
        EvidenceReference(
            id=str(getattr(item, "id", "")),
            source=str(getattr(item, "source", "")),
            reference=str(getattr(item, "reference", "")),
            metadata=dict(getattr(item, "metadata", {}) or {}),
        )
        for item in getattr(result, "evidence", [])
    ]
    return build_operation_outcome(
        status=status,  # type: ignore[arg-type]
        summary="AI execution outcome",
        issues=issues,
        evidence=evidence,
        affected_scope=["ai_execution_result"],
        remaining_scope=["human_review"] if getattr(result, "human_escalation_required", False) else [],
        confidence=getattr(result, "confidence", "UNKNOWN"),
        risk_level=getattr(result, "risk_level", "UNKNOWN"),
        human_attention_required=bool(getattr(result, "human_escalation_required", False)),
        fallback_used=bool(getattr(result, "fallback_used", False)),
        trace={"source": "ai-execution", **dict(getattr(result, "trace", {}) or {})},
    )


def outcome_from_knowledge_intake(snapshot: Any) -> OperationOutcome:
    issues = [
        OutcomeIssue(
            code=str(getattr(issue, "code", "")),
            severity=str(getattr(issue, "severity", "WARNING")).upper(),  # type: ignore[arg-type]
            message=str(getattr(issue, "message", "")),
            scope=str(getattr(issue, "scope", "KNOWLEDGE")),
            evidence_id=getattr(issue, "source_id", None) or getattr(issue, "unit_id", None),
        )
        for issue in getattr(snapshot, "issues", [])
    ]
    for retrieval in getattr(snapshot, "retrievals", []):
        issues.extend(
            OutcomeIssue(
                code=str(getattr(issue, "code", "")),
                severity=str(getattr(issue, "severity", "WARNING")).upper(),  # type: ignore[arg-type]
                message=str(getattr(issue, "message", "")),
                scope=str(getattr(issue, "scope", "RETRIEVAL")),
                evidence_id=getattr(issue, "source_id", None) or getattr(issue, "unit_id", None),
            )
            for issue in getattr(retrieval, "issues", [])
        )
    evidence = [
        EvidenceReference(id=str(getattr(unit, "unit_id", "")), source=str(getattr(unit, "source_id", "")), reference=str(getattr(unit, "source_ref", "")))
        for unit in getattr(snapshot, "units", [])
    ]
    attention = bool(getattr(snapshot, "human_review_required", False))
    return build_operation_outcome(
        status="REVIEW_REQUIRED" if attention else "SUCCESS",
        summary="Knowledge intake outcome",
        issues=issues,
        evidence=evidence,
        affected_scope=[f"sources:{len(getattr(snapshot, 'sources', []))}", f"units:{len(getattr(snapshot, 'units', []))}"],
        remaining_scope=["knowledge_review"] if attention else [],
        human_attention_required=attention,
        trace={"source": "knowledge-intake", **dict(getattr(snapshot, "trace", {}) or {})},
    )


def _issue_from_intake_issue(issue: Any) -> OutcomeIssue:
    return OutcomeIssue(
        code=str(getattr(issue, "code", "")),
        severity=str(getattr(issue, "severity", "WARNING")).upper(),  # type: ignore[arg-type]
        message=str(getattr(issue, "message", "")),
        scope=str(getattr(issue, "scope", "INTAKE")),
        evidence_id=str(getattr(issue, "source_column", "") or getattr(issue, "field", "") or "") or None,
    )
