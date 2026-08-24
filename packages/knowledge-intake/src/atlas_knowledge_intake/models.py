from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


SourceType = Literal["FILE", "URL", "DATABASE", "HUMAN_SUPPLIED", "PROJECT_RECORD", "UNKNOWN"]
KnowledgeStatus = Literal["DRAFT", "PENDING_REVIEW", "APPROVED", "REVOKED", "SUPERSEDED", "ARCHIVED", "UNKNOWN"]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]
Confidence = Literal["UNKNOWN", "LOW", "MEDIUM", "HIGH"]


@dataclass(slots=True)
class KnowledgeSource:
    source_id: str
    title: str
    source_type: SourceType = "UNKNOWN"
    version: str = ""
    status: KnowledgeStatus = "UNKNOWN"
    uri: str = ""
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeCitation:
    source_id: str
    unit_id: str = ""
    reference: str = ""
    quote: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str]:
        return (self.source_id, self.unit_id, self.reference)


@dataclass(slots=True)
class KnowledgeIssue:
    code: str
    severity: IssueSeverity
    message: str
    source_id: str | None = None
    unit_id: str | None = None
    scope: str = "KNOWLEDGE"

    def key(self) -> tuple[str, str, str, str | None, str | None]:
        return (self.code, self.severity, self.scope, self.source_id, self.unit_id)


@dataclass(slots=True)
class KnowledgeUnit:
    unit_id: str
    source_id: str
    title: str = ""
    text: str = ""
    source_ref: str = ""
    status: KnowledgeStatus = "UNKNOWN"
    confidence: Confidence = "UNKNOWN"
    citations: list[KnowledgeCitation] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.citations:
            self.citations.append(KnowledgeCitation(source_id=self.source_id, unit_id=self.unit_id, reference=self.source_ref))


@dataclass(slots=True)
class RetrievalEvidence:
    query: str
    units: list[KnowledgeUnit] = field(default_factory=list)
    citations: list[KnowledgeCitation] = field(default_factory=list)
    issues: list[KnowledgeIssue] = field(default_factory=list)
    confidence: Confidence = "UNKNOWN"
    conflict: bool = False
    ambiguity: bool = False
    human_review_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KnowledgeIntakeSnapshot:
    source_project: str
    sources: list[KnowledgeSource] = field(default_factory=list)
    units: list[KnowledgeUnit] = field(default_factory=list)
    retrievals: list[RetrievalEvidence] = field(default_factory=list)
    issues: list[KnowledgeIssue] = field(default_factory=list)
    human_review_required: bool = False
    trace: dict[str, Any] = field(default_factory=dict)
