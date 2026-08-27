from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


AttentionLevel = Literal["INFO", "NOTICE", "ACTION_REQUIRED", "REVIEW_REQUIRED", "URGENT"]
AttentionState = Literal["OPEN", "ACKNOWLEDGED", "RESOLVED", "DISMISSED", "ESCALATED"]
TargetType = Literal["USER", "ROLE", "GROUP", "TEAM", "SYSTEM", "UNKNOWN"]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]


@dataclass(slots=True)
class AttentionTarget:
    target_id: str
    target_type: TargetType = "UNKNOWN"
    display: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str]:
        return (self.target_type, self.target_id)


@dataclass(slots=True)
class AttentionReason:
    code: str
    message: str = ""
    source_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str]:
        return (self.code, self.message, self.source_ref)


@dataclass(slots=True)
class AttentionTiming:
    due_at: str = ""
    remind_at: str = ""
    repeated_notice_key: str = ""
    escalation_after: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str, str]:
        return (self.due_at, self.remind_at, self.repeated_notice_key, self.escalation_after)


@dataclass(slots=True)
class AttentionSignal:
    signal_id: str
    event_ref: str
    level: AttentionLevel
    state: AttentionState = "OPEN"
    targets: list[AttentionTarget] = field(default_factory=list)
    reasons: list[AttentionReason] = field(default_factory=list)
    timing: AttentionTiming = field(default_factory=AttentionTiming)
    source_refs: list[str] = field(default_factory=list)
    acknowledgement_ref: str = ""
    resolved_ref: str = ""
    dismissed_ref: str = ""
    escalation_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.signal_id,
            self.event_ref,
            self.level,
            self.state,
            tuple(target.key() for target in self.targets),
            tuple(reason.key() for reason in self.reasons),
            self.timing.key(),
            tuple(sorted(self.source_refs)),
            self.acknowledgement_ref,
            self.resolved_ref,
            self.dismissed_ref,
            self.escalation_ref,
        )


@dataclass(slots=True)
class AttentionRoute:
    route_id: str
    signals: list[AttentionSignal] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AttentionIssue:
    code: str
    severity: IssueSeverity
    message: str
    signal_id: str | None = None

    def key(self) -> tuple[str, str, str | None]:
        return (self.code, self.severity, self.signal_id)


@dataclass(slots=True)
class AttentionSnapshot:
    snapshot_id: str
    routes: list[AttentionRoute] = field(default_factory=list)
    issues: list[AttentionIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def signals(self) -> list[AttentionSignal]:
        return [signal for route in self.routes for signal in route.signals]
