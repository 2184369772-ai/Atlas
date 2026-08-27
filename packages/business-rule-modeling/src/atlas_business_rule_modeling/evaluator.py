from __future__ import annotations

from typing import Any

from .models import (
    BusinessRule,
    BusinessRuleEvaluation,
    BusinessRuleModel,
    DecisionStatus,
    RuleConstraint,
    RuleDecision,
    RuleEffect,
    RuleIssue,
)


def evaluate_rule_model(model: BusinessRuleModel, facts: dict[str, Any] | None = None) -> BusinessRuleEvaluation:
    facts = facts or {}
    decisions = [_evaluate_rule(rule, facts) for rule in model.active_rules()]
    issues = [issue for decision in decisions for issue in decision.issues]
    return BusinessRuleEvaluation(status=_overall_status(decisions), decisions=decisions, issues=issues)


def _evaluate_rule(rule: BusinessRule, facts: dict[str, Any]) -> RuleDecision:
    issues: list[RuleIssue] = []
    effects: list[RuleEffect] = []

    if not rule.intent.strip():
        issues.append(_issue(rule, "rule.intent_missing", "ERROR", "Rule intent must remain explicit."))

    if rule.rule_type == "RESPONSIBILITY_BOUNDARY" and not rule.responsibility:
        issues.append(_issue(rule, "rule.responsibility_missing", "ERROR", "Responsibility boundary rules require at least one actor boundary."))

    if rule.formal_fact_protected and rule.effect not in {"PROTECT", "BLOCK", "REVIEW"} and not rule.derived_suggestion:
        issues.append(_issue(rule, "rule.formal_fact_unprotected", "ERROR", "Formal facts require PROTECT, BLOCK, or REVIEW effect."))

    if rule.derived_suggestion and rule.effect not in {"SUGGEST", "WARN", "REVIEW"}:
        issues.append(_issue(rule, "rule.suggestion_overwrites_fact", "ERROR", "Derived suggestions must not be modeled as direct formal-fact writes."))

    for constraint in rule.constraints:
        if not _constraint_passes(constraint, facts):
            effects.append(constraint.effect)
            issues.append(
                _issue(
                    rule,
                    f"constraint.{constraint.operator.lower()}",
                    _severity_for_effect(constraint.effect),
                    constraint.message or f"Constraint failed for {constraint.field}.",
                    field=constraint.field,
                )
            )

    if rule.effect != "ALLOW" and not rule.constraints:
        effects.append(rule.effect)
    status = _status_from(rule, issues, effects)
    return RuleDecision(
        rule_id=rule.rule_id,
        status=status,
        issues=issues,
        effects=sorted(set(effects)),
        human_decision_required=rule.human_decision_required or status == "REVIEW",
        formal_fact_protected=rule.formal_fact_protected,
        trace={"rule_type": rule.rule_type, **rule.trace},
    )


def _constraint_passes(constraint: RuleConstraint, facts: dict[str, Any]) -> bool:
    if constraint.field not in facts:
        return constraint.operator not in {"REQUIRED", "PRESENT"}
    actual = facts.get(constraint.field)
    if constraint.operator in {"REQUIRED", "PRESENT"}:
        return actual not in {None, ""}
    if constraint.operator == "FORBIDDEN":
        return actual in {None, ""}
    if constraint.operator == "EQUALS":
        return actual == constraint.value
    if constraint.operator == "NOT_EQUALS":
        return actual != constraint.value
    if constraint.operator == "IN":
        return actual in (constraint.value or [])
    if constraint.operator == "NOT_IN":
        return actual not in (constraint.value or [])
    return True


def _status_from(rule: BusinessRule, issues: list[RuleIssue], effects: list[RuleEffect]) -> DecisionStatus:
    if any(issue.severity == "ERROR" for issue in issues) or "BLOCK" in effects:
        return "BLOCK"
    if rule.human_decision_required or "REVIEW" in effects:
        return "REVIEW"
    if any(issue.severity == "WARNING" for issue in issues) or "WARN" in effects or "SUGGEST" in effects:
        return "WARN"
    return "PASS"


def _overall_status(decisions: list[RuleDecision]) -> DecisionStatus:
    statuses = {decision.status for decision in decisions}
    if "BLOCK" in statuses:
        return "BLOCK"
    if "REVIEW" in statuses:
        return "REVIEW"
    if "WARN" in statuses:
        return "WARN"
    return "PASS"


def _severity_for_effect(effect: RuleEffect) -> str:
    if effect == "BLOCK":
        return "ERROR"
    if effect in {"WARN", "SUGGEST", "REVIEW"}:
        return "WARNING"
    return "INFO"


def _issue(rule: BusinessRule, code: str, severity: str, message: str, field: str | None = None) -> RuleIssue:
    evidence_id = rule.source.evidence[0].id if rule.source.evidence else None
    return RuleIssue(code=code, severity=severity, message=message, rule_id=rule.rule_id, field=field, evidence_id=evidence_id)
