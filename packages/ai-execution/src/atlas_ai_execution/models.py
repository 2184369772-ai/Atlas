from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Literal, Protocol


ExecutionStatus = Literal["SUCCESS", "PARTIAL", "FAILED", "BLOCKED"]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]
FailureType = Literal[
    "NONE",
    "TIMEOUT",
    "PROVIDER_FAILURE",
    "MODEL_UNAVAILABLE",
    "INVALID_RESULT",
    "BLOCKED",
    "UNKNOWN",
]
Confidence = Literal["UNKNOWN", "LOW", "MEDIUM", "HIGH"]
RiskLevel = Literal["UNKNOWN", "LOW", "MEDIUM", "HIGH"]


@dataclass(slots=True)
class EvidenceReference:
    id: str
    source: str = ""
    reference: str = ""
    score: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AIExecutionIssue:
    code: str
    severity: IssueSeverity
    message: str
    scope: str = "EXECUTION"
    evidence_id: str | None = None


@dataclass(slots=True)
class AIExecutionRequest:
    input_payload: dict[str, Any]
    instructions: str = ""
    expected_output: Literal["TEXT", "JSON_OBJECT"] = "TEXT"
    timeout_seconds: float | None = None
    evidence: list[EvidenceReference] = field(default_factory=list)
    risk_level: RiskLevel = "UNKNOWN"
    trace: dict[str, Any] = field(default_factory=dict)
    blocked_reason: str = ""


@dataclass(slots=True)
class ProviderResponse:
    content: str = ""
    structured: dict[str, Any] | None = None
    model: str = ""
    provider: str = ""
    raw: dict[str, Any] = field(default_factory=dict)
    trace: dict[str, Any] = field(default_factory=dict)


class ProviderInvocation(Protocol):
    name: str

    def invoke(self, request: AIExecutionRequest) -> ProviderResponse:
        raise NotImplementedError


FallbackBuilder = Callable[[AIExecutionRequest, BaseException], dict[str, Any] | str | None]


@dataclass(slots=True)
class AIExecutionResult:
    status: ExecutionStatus
    content: str = ""
    structured: dict[str, Any] | None = None
    issues: list[AIExecutionIssue] = field(default_factory=list)
    evidence: list[EvidenceReference] = field(default_factory=list)
    confidence: Confidence = "UNKNOWN"
    risk_level: RiskLevel = "UNKNOWN"
    human_escalation_required: bool = False
    failure_type: FailureType = "NONE"
    fallback_used: bool = False
    provider: str = ""
    model: str = ""
    trace: dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)
