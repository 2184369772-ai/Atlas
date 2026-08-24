from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .models import KnowledgeIntakeSnapshot, KnowledgeIssue


KnowledgeDiffKind = Literal[
    "MATCH",
    "CORE_DIFFERENCE",
    "ADAPTER_DIFFERENCE",
    "BUSINESS_ONLY_DIFFERENCE",
    "ACCEPTABLE_DIFFERENCE",
]


@dataclass(slots=True)
class KnowledgeDifference:
    kind: KnowledgeDiffKind
    scope: str
    message: str


@dataclass(slots=True)
class KnowledgeShadowComparison:
    overall: KnowledgeDiffKind
    differences: list[KnowledgeDifference] = field(default_factory=list)
    unexplained_differences: int = 0
    lost_evidence: int = 0


def compare_knowledge_intake(primary: KnowledgeIntakeSnapshot, atlas: KnowledgeIntakeSnapshot) -> KnowledgeShadowComparison:
    differences: list[KnowledgeDifference] = []
    unexplained = 0
    lost_evidence = 0

    if primary.human_review_required != atlas.human_review_required:
        differences.append(
            KnowledgeDifference(
                kind="CORE_DIFFERENCE",
                scope="human_review_required",
                message=f"Primary={primary.human_review_required!r}, Atlas={atlas.human_review_required!r}",
            )
        )
        unexplained += 1

    primary_sources = {(item.source_id, item.version, item.status) for item in primary.sources}
    atlas_sources = {(item.source_id, item.version, item.status) for item in atlas.sources}
    unexplained += _compare_sets(differences, "source", primary_sources, atlas_sources)

    primary_units = {(item.unit_id, item.source_id, item.status, item.source_ref) for item in primary.units}
    atlas_units = {(item.unit_id, item.source_id, item.status, item.source_ref) for item in atlas.units}
    lost_units = primary_units - atlas_units
    lost_evidence += len(lost_units)
    unexplained += _compare_sets(differences, "unit", primary_units, atlas_units)

    primary_citations = {citation.key() for item in primary.units for citation in item.citations}
    atlas_citations = {citation.key() for item in atlas.units for citation in item.citations}
    lost_citations = primary_citations - atlas_citations
    lost_evidence += len(lost_citations)
    unexplained += _compare_sets(differences, "citation", primary_citations, atlas_citations)

    primary_issues = {issue.key() for issue in _all_issues(primary)}
    atlas_issues = {issue.key() for issue in _all_issues(atlas)}
    missing_issues = primary_issues - atlas_issues
    lost_evidence += len(missing_issues)
    unexplained += _compare_sets(differences, "issue", primary_issues, atlas_issues)

    for index, primary_retrieval in enumerate(primary.retrievals):
        if index >= len(atlas.retrievals):
            differences.append(KnowledgeDifference("CORE_DIFFERENCE", "retrieval.missing", f"Missing Atlas retrieval at index {index}"))
            unexplained += 1
            continue
        atlas_retrieval = atlas.retrievals[index]
        for scope in ("confidence", "conflict", "ambiguity", "human_review_required"):
            primary_value = getattr(primary_retrieval, scope)
            atlas_value = getattr(atlas_retrieval, scope)
            if primary_value != atlas_value:
                differences.append(
                    KnowledgeDifference(
                        kind="CORE_DIFFERENCE",
                        scope=f"retrieval.{scope}",
                        message=f"Primary={primary_value!r}, Atlas={atlas_value!r}",
                    )
                )
                unexplained += 1

    if len(primary.retrievals) != len(atlas.retrievals):
        differences.append(
            KnowledgeDifference(
                kind="ADAPTER_DIFFERENCE",
                scope="retrieval.count",
                message=f"Primary={len(primary.retrievals)}, Atlas={len(atlas.retrievals)}",
            )
        )
        unexplained += 1

    if primary.trace != atlas.trace:
        differences.append(
            KnowledgeDifference(
                kind="BUSINESS_ONLY_DIFFERENCE",
                scope="trace",
                message=f"Primary={primary.trace!r}, Atlas={atlas.trace!r}",
            )
        )

    return KnowledgeShadowComparison(
        overall=_overall(differences),
        differences=differences,
        unexplained_differences=unexplained,
        lost_evidence=lost_evidence,
    )


def _all_issues(snapshot: KnowledgeIntakeSnapshot) -> list[KnowledgeIssue]:
    issues = list(snapshot.issues)
    for retrieval in snapshot.retrievals:
        issues.extend(retrieval.issues)
    return issues


def _compare_sets(differences: list[KnowledgeDifference], scope: str, primary: set, atlas: set) -> int:
    unexplained = 0
    for missing in sorted(primary - atlas):
        differences.append(KnowledgeDifference("CORE_DIFFERENCE", f"{scope}.lost", f"Missing Atlas {scope} {missing!r}"))
        unexplained += 1
    for extra in sorted(atlas - primary):
        differences.append(KnowledgeDifference("ACCEPTABLE_DIFFERENCE", f"{scope}.extra", f"Extra Atlas {scope} {extra!r}"))
    return unexplained


def _overall(differences: list[KnowledgeDifference]) -> KnowledgeDiffKind:
    overall: KnowledgeDiffKind = "MATCH"
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
