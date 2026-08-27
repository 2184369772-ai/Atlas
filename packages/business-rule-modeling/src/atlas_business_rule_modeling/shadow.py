from __future__ import annotations

from dataclasses import dataclass

from .models import BusinessRuleModel


@dataclass(slots=True)
class BusinessRuleShadowDifference:
    scope: str
    rule_id: str
    message: str
    explained: bool = False


def compare_business_rule_model(primary: BusinessRuleModel, atlas: BusinessRuleModel) -> list[BusinessRuleShadowDifference]:
    differences: list[BusinessRuleShadowDifference] = []
    primary_rules = {rule.rule_id: rule for rule in primary.active_rules()}
    atlas_rules = {rule.rule_id: rule for rule in atlas.active_rules()}

    for rule_id in sorted(primary_rules.keys() - atlas_rules.keys()):
        differences.append(BusinessRuleShadowDifference("rule", rule_id, "Atlas model lost a primary business-rule semantic."))
    for rule_id in sorted(atlas_rules.keys() - primary_rules.keys()):
        differences.append(BusinessRuleShadowDifference("rule", rule_id, "Atlas model added a rule not present in the primary snapshot.", explained=True))

    for rule_id in sorted(primary_rules.keys() & atlas_rules.keys()):
        primary_rule = primary_rules[rule_id]
        atlas_rule = atlas_rules[rule_id]
        if primary_rule.semantic_key() != atlas_rule.semantic_key():
            differences.append(
                BusinessRuleShadowDifference(
                    "semantic",
                    rule_id,
                    "Rule type/effect/constraint/responsibility/human/fact-protection semantics differ.",
                )
            )
    return differences
