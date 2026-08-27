from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


SectionKind = Literal["SUMMARY", "FACTS", "STATUS", "ATTENTION", "RISKS", "OUTCOMES", "ACTIONS", "REPORTS", "DETAIL"]
ItemKind = Literal["FACT", "STATUS", "ATTENTION", "RISK", "ISSUE", "OUTCOME", "ACTION", "REPORT", "REFERENCE"]
ItemState = Literal["PENDING", "ACTIVE", "RESOLVED", "DISMISSED", "STALE", "UNKNOWN"]
Priority = Literal["LOW", "NORMAL", "HIGH", "URGENT"]
ActionType = Literal["OPEN", "REVIEW", "CONFIRM", "RESOLVE", "DRILL_DOWN", "CONTINUE", "EXPORT", "PROJECT_OWNED"]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]


@dataclass(slots=True)
class ActionEntry:
    action_id: str
    action_type: ActionType
    label: str = ""
    target_ref: str = ""
    owner_ref: str = ""
    source_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str, str, tuple[str, ...]]:
        return (self.action_id, self.action_type, self.target_ref, self.owner_ref, tuple(sorted(self.source_refs)))


@dataclass(slots=True)
class WorkspaceItem:
    item_id: str
    item_kind: ItemKind
    title: str
    state: ItemState = "UNKNOWN"
    priority: Priority = "NORMAL"
    summary: str = ""
    detail: str = ""
    as_of: str = ""
    freshness: str = ""
    owner_ref: str = ""
    source_refs: list[str] = field(default_factory=list)
    drilldown_target: str = ""
    actions: list[ActionEntry] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.item_id,
            self.item_kind,
            self.state,
            self.priority,
            self.summary,
            self.as_of,
            self.freshness,
            self.owner_ref,
            tuple(sorted(self.source_refs)),
            self.drilldown_target,
            tuple(action.key() for action in self.actions),
        )


@dataclass(slots=True)
class WorkspaceIssue:
    code: str
    severity: IssueSeverity
    message: str
    item_id: str | None = None
    section_id: str | None = None

    def key(self) -> tuple[str, str, str | None, str | None]:
        return (self.code, self.severity, self.item_id, self.section_id)


@dataclass(slots=True)
class WorkspaceSection:
    section_id: str
    section_kind: SectionKind
    title: str = ""
    priority: Priority = "NORMAL"
    items: list[WorkspaceItem] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.section_id,
            self.section_kind,
            self.priority,
            tuple(sorted(self.source_refs)),
            tuple(item.semantic_key() for item in self.items),
        )


@dataclass(slots=True)
class WorkspaceSnapshot:
    snapshot_id: str
    sections: list[WorkspaceSection] = field(default_factory=list)
    as_of: str = ""
    issues: list[WorkspaceIssue] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def items(self) -> list[WorkspaceItem]:
        return [item for section in self.sections for item in section.items]
