from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


SOURCE_KINDS = {"uploaded", "generated", "imported", "external", "local", "backup", "system"}
REFERENCE_KINDS = {"local", "memory", "external", "generated", "missing"}
LIFECYCLE_STATES = {"received", "accepted", "rejected", "consumed", "generated", "available", "failed", "cleaned"}
RETENTION_MODES = {"temporary", "retained", "archive", "generated_output", "cleanup_eligible"}
ISSUE_SEVERITIES = {"info", "warning", "error"}
BUSINESS_STATES = {
    "approved",
    "revoked",
    "archived",
    "published",
    "pending_review",
    "retrievable",
    "completed",
    "active",
    "closed",
}
REFERENCE_REQUIRED_STATES = {"accepted", "consumed", "generated", "available", "cleaned"}
ISSUE_REQUIRED_STATES = {"rejected", "failed"}
ALLOWED_TRANSITIONS = {
    "received": {"accepted", "rejected", "failed", "generated"},
    "accepted": {"consumed", "available", "failed", "cleaned"},
    "generated": {"available", "consumed", "failed", "cleaned"},
    "available": {"consumed", "failed", "cleaned"},
    "consumed": {"failed", "cleaned"},
    "failed": {"cleaned"},
    "rejected": set(),
    "cleaned": set(),
}


class ContractViolation(ValueError):
    """Raised when a File Lifecycle object violates the minimum contract."""


@dataclass(frozen=True, slots=True)
class FileReference:
    reference_kind: str
    locator: str | None = None
    display_locator: str | None = None

    def __post_init__(self) -> None:
        if self.reference_kind not in REFERENCE_KINDS:
            raise ContractViolation(f"Invalid reference kind: {self.reference_kind}.")
        if self.reference_kind != "missing" and self.locator is None:
            raise ContractViolation("FileReference.locator is required unless reference_kind is 'missing'.")


@dataclass(frozen=True, slots=True)
class FileMetadata:
    original_name: str | None = None
    display_name: str | None = None
    extension: str | None = None
    media_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None

    def __post_init__(self) -> None:
        if self.size_bytes is not None and self.size_bytes < 0:
            raise ContractViolation("File size cannot be negative.")

    @property
    def is_identifiable(self) -> bool:
        return any([self.original_name, self.display_name, self.extension, self.media_type])


@dataclass(frozen=True, slots=True)
class FileSource:
    source_kind: str
    source_label: str | None = None

    def __post_init__(self) -> None:
        if self.source_kind not in SOURCE_KINDS:
            raise ContractViolation(f"Invalid source kind: {self.source_kind}.")


@dataclass(frozen=True, slots=True)
class LifecycleState:
    value: str = "received"
    reason: str | None = None
    changed_at: str | None = None

    def __post_init__(self) -> None:
        if self.value in BUSINESS_STATES:
            raise ContractViolation(f"Business state is not a file lifecycle state: {self.value}.")
        if self.value not in LIFECYCLE_STATES:
            raise ContractViolation(f"Invalid lifecycle state: {self.value}.")


@dataclass(frozen=True, slots=True)
class FileIssue:
    code: str
    severity: str
    message: str
    suggestion: str | None = None
    original_value: Any = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ContractViolation("FileIssue.code is required.")
        if self.severity not in ISSUE_SEVERITIES:
            raise ContractViolation(f"Invalid issue severity: {self.severity}.")
        if not self.message:
            raise ContractViolation("FileIssue.message is required.")


@dataclass(frozen=True, slots=True)
class RetentionIntent:
    mode: str = "temporary"
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in RETENTION_MODES:
            raise ContractViolation(f"Invalid retention mode: {self.mode}.")
        if self.mode == "archive" and not self.reason:
            raise ContractViolation("Archive retention requires a reason.")


_UNSET = object()


@dataclass(frozen=True, slots=True)
class FileItem:
    id: str
    source: FileSource
    metadata: FileMetadata
    state: LifecycleState = field(default_factory=LifecycleState)
    retention: RetentionIntent = field(default_factory=RetentionIntent)
    reference: FileReference | None = None
    issues: tuple[FileIssue, ...] = field(default_factory=tuple)
    created_at: str | None = None
    updated_at: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ContractViolation("FileItem.id is required.")
        if not isinstance(self.source, FileSource):
            raise ContractViolation("FileItem.source is required.")
        if not isinstance(self.metadata, FileMetadata):
            raise ContractViolation("FileItem.metadata is required.")
        if not isinstance(self.state, LifecycleState):
            raise ContractViolation("FileItem.state is required.")
        if not isinstance(self.retention, RetentionIntent):
            raise ContractViolation("FileItem.retention is required.")

        issues = _normalize_issues(self.issues)
        object.__setattr__(self, "issues", issues)
        self._validate_contract()

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def with_issue(self, issue: FileIssue) -> "FileItem":
        return FileItem(
            id=self.id,
            source=self.source,
            metadata=self.metadata,
            state=self.state,
            retention=self.retention,
            reference=self.reference,
            issues=(*self.issues, issue),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )

    def transition_to(
        self,
        state: str,
        *,
        reference: FileReference | None | object = _UNSET,
        metadata: FileMetadata | None = None,
        retention: RetentionIntent | None = None,
        issue: FileIssue | None = None,
        reason: str | None = None,
        changed_at: str | None = None,
    ) -> "FileItem":
        if state not in ALLOWED_TRANSITIONS[self.state.value]:
            raise ContractViolation(f"Transition from {self.state.value} to {state} is not allowed.")

        next_reference = self.reference if reference is _UNSET else reference
        next_issues = (*self.issues, issue) if issue is not None else self.issues

        return FileItem(
            id=self.id,
            source=self.source,
            metadata=metadata or self.metadata,
            state=LifecycleState(value=state, reason=reason, changed_at=changed_at),
            retention=retention or self.retention,
            reference=next_reference,
            issues=next_issues,
            created_at=self.created_at,
            updated_at=changed_at or self.updated_at,
        )

    def _validate_contract(self) -> None:
        state = self.state.value
        if state in REFERENCE_REQUIRED_STATES and self.reference is None:
            raise ContractViolation(f"State '{state}' requires FileReference.")

        if state in ISSUE_REQUIRED_STATES and not self.issues:
            raise ContractViolation(f"State '{state}' requires at least one FileIssue.")

        if state == "available" and not self.metadata.is_identifiable:
            raise ContractViolation("Available files require identifiable metadata.")


def _normalize_issues(issues: Iterable[FileIssue]) -> tuple[FileIssue, ...]:
    normalized = tuple(issues)
    for issue in normalized:
        if not isinstance(issue, FileIssue):
            raise ContractViolation("FileItem.issues must contain FileIssue instances.")
    return normalized
