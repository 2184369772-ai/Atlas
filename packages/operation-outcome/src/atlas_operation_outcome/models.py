from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


OutcomeStatus = Literal["SUCCESS", "PARTIAL", "FAILED", "BLOCKED", "REVIEW_REQUIRED"]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]
Confidence = Literal["UNKNOWN", "LOW", "MEDIUM", "HIGH"]
RiskLevel = Literal["UNKNOWN", "LOW", "MEDIUM", "HIGH"]


@dataclass(slots=True)
class EvidenceReference:
    id: str
    source: str = ""
    reference: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str]:
        return (self.id, self.source, self.reference)


@dataclass(slots=True)
class OutcomeIssue:
    code: str
    severity: IssueSeverity
    message: str
    scope: str = "OPERATION"
    evidence_id: str | None = None

    def key(self) -> tuple[str, str, str, str | None]:
        return (self.code, self.severity, self.scope, self.evidence_id)


@dataclass(slots=True)
class OperationOutcome:
    status: OutcomeStatus
    summary: str = ""
    issues: list[OutcomeIssue] = field(default_factory=list)
    evidence: list[EvidenceReference] = field(default_factory=list)
    affected_scope: list[str] = field(default_factory=list)
    remaining_scope: list[str] = field(default_factory=list)
    confidence: Confidence = "UNKNOWN"
    risk_level: RiskLevel = "UNKNOWN"
    human_attention_required: bool = False
    fallback_used: bool = False
    trace: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)
