from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


RuleType = Literal[
    "CONSTRAINT",
    "VALIDATION",
    "STATE_TRANSITION",
    "RESPONSIBILITY_BOUNDARY",
    "DERIVED_SUGGESTION",
    "FORMAL_FACT_PROTECTION",
]
RuleEffect = Literal["ALLOW", "BLOCK", "WARN", "REVIEW", "SUGGEST", "PROTECT"]
DecisionStatus = Literal["PASS", "WARN", "BLOCK", "REVIEW"]
IssueSeverity = Literal["INFO", "WARNING", "ERROR"]


@dataclass(slots=True)
class EvidenceReference:
    id: str
    source: str = ""
    reference: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def key(self) -> tuple[str, str, str]:
        return (self.id, self.source, self.reference)


@dataclass(slots=True)
class RuleSource:
    source_id: str
    project: str
    intent: str
    evidence: list[EvidenceReference] = field(default_factory=list)
    source_type: str = "REAL_PROJECT"


@dataclass(slots=True)
class RuleConstraint:
    field: str
    operator: Literal["REQUIRED", "FORBIDDEN", "EQUALS", "NOT_EQUALS", "IN", "NOT_IN", "PRESENT"] = "REQUIRED"
    value: Any = None
    effect: RuleEffect = "BLOCK"
    message: str = ""

    def key(self) -> tuple[str, str, str, str]:
        return (self.field, self.operator, repr(self.value), self.effect)


@dataclass(slots=True)
class ResponsibilityBoundary:
    actor_ref: str
    owns: list[str] = field(default_factory=list)
    may_change: list[str] = field(default_factory=list)
    may_view: list[str] = field(default_factory=list)
    must_not_change: list[str] = field(default_factory=list)
    requires_trace: bool = False

    def key(self) -> tuple[str, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], bool]:
        return (
            self.actor_ref,
            tuple(sorted(self.owns)),
            tuple(sorted(self.may_change)),
            tuple(sorted(self.may_view)),
            tuple(sorted(self.must_not_change)),
            self.requires_trace,
        )


@dataclass(slots=True)
class BusinessRule:
    rule_id: str
    rule_type: RuleType
    source: RuleSource
    intent: str
    constraints: list[RuleConstraint] = field(default_factory=list)
    responsibility: list[ResponsibilityBoundary] = field(default_factory=list)
    effect: RuleEffect = "ALLOW"
    human_decision_required: bool = False
    formal_fact_protected: bool = False
    derived_suggestion: bool = False
    active: bool = True
    trace: dict[str, Any] = field(default_factory=dict)

    def semantic_key(self) -> tuple[Any, ...]:
        return (
            self.rule_id,
            self.rule_type,
            self.effect,
            self.human_decision_required,
            self.formal_fact_protected,
            self.derived_suggestion,
            tuple(constraint.key() for constraint in self.constraints),
            tuple(boundary.key() for boundary in self.responsibility),
        )


@dataclass(slots=True)
class RuleIssue:
    code: str
    severity: IssueSeverity
    message: str
    rule_id: str
    field: str | None = None
    evidence_id: str | None = None

    def key(self) -> tuple[str, str, str, str | None]:
        return (self.rule_id, self.code, self.severity, self.field)


@dataclass(slots=True)
class RuleDecision:
    rule_id: str
    status: DecisionStatus
    issues: list[RuleIssue] = field(default_factory=list)
    effects: list[RuleEffect] = field(default_factory=list)
    human_decision_required: bool = False
    formal_fact_protected: bool = False
    trace: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class BusinessRuleEvaluation:
    status: DecisionStatus
    decisions: list[RuleDecision] = field(default_factory=list)
    issues: list[RuleIssue] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "ERROR" for issue in self.issues)


@dataclass(slots=True)
class BusinessRuleModel:
    model_id: str
    rules: list[BusinessRule] = field(default_factory=list)
    evidence: list[EvidenceReference] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)

    def active_rules(self) -> list[BusinessRule]:
        return [rule for rule in self.rules if rule.active]
