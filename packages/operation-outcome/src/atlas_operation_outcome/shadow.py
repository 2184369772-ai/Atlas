from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .models import OperationOutcome


OutcomeDiffKind = Literal[
    "MATCH",
    "CORE_DIFFERENCE",
    "ADAPTER_DIFFERENCE",
    "BUSINESS_ONLY_DIFFERENCE",
    "ACCEPTABLE_DIFFERENCE",
]


@dataclass(slots=True)
class OutcomeDifference:
    kind: OutcomeDiffKind
    scope: str
    message: str


@dataclass(slots=True)
class OutcomeShadowComparison:
    overall: OutcomeDiffKind
    differences: list[OutcomeDifference] = field(default_factory=list)
    unexplained_differences: int = 0
    lost_evidence: int = 0


def compare_operation_outcome(primary: OperationOutcome, atlas: OperationOutcome) -> OutcomeShadowComparison:
    differences: list[OutcomeDifference] = []
    unexplained = 0
    lost_evidence = 0

    for scope in ("status", "confidence", "risk_level", "human_attention_required", "fallback_used"):
        primary_value = getattr(primary, scope)
        atlas_value = getattr(atlas, scope)
        if primary_value != atlas_value:
            differences.append(OutcomeDifference("CORE_DIFFERENCE", scope, f"Primary={primary_value!r}, Atlas={atlas_value!r}"))
            unexplained += 1

    primary_issues = {issue.key() for issue in primary.issues}
    atlas_issues = {issue.key() for issue in atlas.issues}
    for missing in sorted(primary_issues - atlas_issues):
        differences.append(OutcomeDifference("CORE_DIFFERENCE", "issue.lost", f"Missing Atlas issue {missing!r}"))
        unexplained += 1
        lost_evidence += 1
    for extra in sorted(atlas_issues - primary_issues):
        differences.append(OutcomeDifference("ACCEPTABLE_DIFFERENCE", "issue.extra", f"Extra Atlas issue {extra!r}"))

    primary_evidence = {item.key() for item in primary.evidence}
    atlas_evidence = {item.key() for item in atlas.evidence}
    for missing in sorted(primary_evidence - atlas_evidence):
        differences.append(OutcomeDifference("CORE_DIFFERENCE", "evidence.lost", f"Missing Atlas evidence {missing!r}"))
        unexplained += 1
        lost_evidence += 1
    for extra in sorted(atlas_evidence - primary_evidence):
        differences.append(OutcomeDifference("ACCEPTABLE_DIFFERENCE", "evidence.extra", f"Extra Atlas evidence {extra!r}"))

    for scope in ("affected_scope", "remaining_scope"):
        primary_values = set(getattr(primary, scope))
        atlas_values = set(getattr(atlas, scope))
        if primary_values != atlas_values:
            differences.append(
                OutcomeDifference(
                    "ADAPTER_DIFFERENCE",
                    scope,
                    f"Primary={sorted(primary_values)!r}, Atlas={sorted(atlas_values)!r}",
                )
            )
            unexplained += 1

    if primary.trace != atlas.trace:
        differences.append(OutcomeDifference("BUSINESS_ONLY_DIFFERENCE", "trace", f"Primary={primary.trace!r}, Atlas={atlas.trace!r}"))

    return OutcomeShadowComparison(
        overall=_overall(differences),
        differences=differences,
        unexplained_differences=unexplained,
        lost_evidence=lost_evidence,
    )


def _overall(differences: list[OutcomeDifference]) -> OutcomeDiffKind:
    overall: OutcomeDiffKind = "MATCH"
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
    return overall
