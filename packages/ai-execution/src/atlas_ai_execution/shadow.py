from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .models import AIExecutionResult


AIExecutionDiffKind = Literal[
    "MATCH",
    "CORE_DIFFERENCE",
    "ADAPTER_DIFFERENCE",
    "BUSINESS_ONLY_DIFFERENCE",
    "ACCEPTABLE_DIFFERENCE",
]


@dataclass(slots=True)
class AIExecutionDifference:
    kind: AIExecutionDiffKind
    scope: str
    message: str


@dataclass(slots=True)
class AIExecutionShadowComparison:
    overall: AIExecutionDiffKind
    differences: list[AIExecutionDifference] = field(default_factory=list)
    unexplained_differences: int = 0
    blockers: list[str] = field(default_factory=list)


def compare_ai_execution(primary: AIExecutionResult, atlas: AIExecutionResult) -> AIExecutionShadowComparison:
    differences: list[AIExecutionDifference] = []
    unexplained = 0

    for scope in ("status", "failure_type", "confidence", "risk_level", "human_escalation_required", "fallback_used"):
        primary_value = getattr(primary, scope)
        atlas_value = getattr(atlas, scope)
        if primary_value != atlas_value:
            differences.append(
                AIExecutionDifference(
                    kind="CORE_DIFFERENCE",
                    scope=scope,
                    message=f"Primary={primary_value!r}, Atlas={atlas_value!r}",
                )
            )
            unexplained += 1

    primary_issue_codes = {(issue.code, issue.severity, issue.scope) for issue in primary.issues}
    atlas_issue_codes = {(issue.code, issue.severity, issue.scope) for issue in atlas.issues}
    for missing in sorted(primary_issue_codes - atlas_issue_codes):
        differences.append(
            AIExecutionDifference(
                kind="CORE_DIFFERENCE",
                scope="issue.lost",
                message=f"Missing Atlas issue {missing!r}",
            )
        )
        unexplained += 1
    for extra in sorted(atlas_issue_codes - primary_issue_codes):
        differences.append(
            AIExecutionDifference(
                kind="ACCEPTABLE_DIFFERENCE",
                scope="issue.extra",
                message=f"Extra Atlas issue {extra!r}",
            )
        )

    primary_evidence = {item.id for item in primary.evidence}
    atlas_evidence = {item.id for item in atlas.evidence}
    if primary_evidence != atlas_evidence:
        differences.append(
            AIExecutionDifference(
                kind="ADAPTER_DIFFERENCE",
                scope="evidence",
                message=f"Primary={sorted(primary_evidence)!r}, Atlas={sorted(atlas_evidence)!r}",
            )
        )
        unexplained += 1

    if primary.trace != atlas.trace:
        differences.append(
            AIExecutionDifference(
                kind="BUSINESS_ONLY_DIFFERENCE",
                scope="trace",
                message=f"Primary={primary.trace!r}, Atlas={atlas.trace!r}",
            )
        )

    overall: AIExecutionDiffKind = "MATCH"
    priority = {
        "MATCH": 0,
        "ACCEPTABLE_DIFFERENCE": 1,
        "BUSINESS_ONLY_DIFFERENCE": 2,
        "ADAPTER_DIFFERENCE": 3,
        "CORE_DIFFERENCE": 4,
    }
    for difference in differences:
        if priority[difference.kind] > priority[overall]:
            overall = difference.kind
    return AIExecutionShadowComparison(overall=overall, differences=differences, unexplained_differences=unexplained)
