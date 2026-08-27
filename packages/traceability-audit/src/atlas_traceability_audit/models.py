from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


ActorType = Literal["HUMAN", "SYSTEM", "AI", "IMPORTER", "UNKNOWN"]
SourceType = Literal["FILE", "DATABASE", "API", "GIT", "AI_RESULT", "HUMAN_INPUT", "PROJECT_RECORD", "UNKNOWN"]
EventType = Literal[
    "CREATED",
    "UPDATED",
    "STATUS_CHANGED",
    "IMPORTED",
    "VALIDATED",
    "APPROVED",
    "REJECTED",
    "CORRECTED",
    "SUPERSEDED",
    "REPLACED",
    "VOIDED",
    "DERIVED",
    "SNAPSHOT",
    "CONFIRMED",
]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]


@dataclass(slots=True)
class TraceActor:
    actor_id: str
    actor_type: ActorType = "UNKNOWN"
    display: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str]:
        return (self.actor_type, self.actor_id)


@dataclass(slots=True)
class TraceSource:
    source_id: str
    source_type: SourceType = "UNKNOWN"
    uri: str = ""
    version: str = ""
    checksum: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str, str]:
        return (self.source_type, self.source_id, self.version, self.checksum)


@dataclass(slots=True)
class TraceReference:
    ref_id: str
    source_id: str = ""
    reference: str = ""
    evidence_type: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str, str]:
        return (self.ref_id, self.source_id, self.reference, self.evidence_type)


@dataclass(slots=True)
class TraceChange:
    field: str
    before: Any = None
    after: Any = None
    reason: str = ""

    def key(self) -> tuple[str, str, str, str]:
        return (self.field, repr(self.before), repr(self.after), self.reason)


@dataclass(slots=True)
class TraceEvent:
    event_id: str
    event_type: EventType
    subject_id: str
    occurred_at: str = ""
    actor: TraceActor | None = None
    producer: str = ""
    action: str = ""
    reason: str = ""
    changes: list[TraceChange] = field(default_factory=list)
    references: list[TraceReference] = field(default_factory=list)
    derived_from: list[str] = field(default_factory=list)
    correlation_id: str = ""
    task_id: str = ""
    immutable_formal_fact: bool = False
    supersedes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[Any, ...]:
        actor_key = self.actor.key() if self.actor else ("UNKNOWN", "")
        return (
            self.event_id,
            self.event_type,
            self.subject_id,
            actor_key,
            self.producer,
            self.action,
            tuple(change.key() for change in self.changes),
            tuple(reference.key() for reference in self.references),
            tuple(sorted(self.derived_from)),
            self.correlation_id,
            self.task_id,
            self.immutable_formal_fact,
            tuple(sorted(self.supersedes)),
        )


@dataclass(slots=True)
class TraceIssue:
    code: str
    severity: IssueSeverity
    message: str
    event_id: str | None = None
    subject_id: str | None = None


@dataclass(slots=True)
class TraceChain:
    chain_id: str
    subject_id: str
    sources: list[TraceSource] = field(default_factory=list)
    events: list[TraceEvent] = field(default_factory=list)
    references: list[TraceReference] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def event_ids(self) -> set[str]:
        return {event.event_id for event in self.events}
