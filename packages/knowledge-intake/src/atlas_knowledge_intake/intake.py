from __future__ import annotations

from .models import KnowledgeIntakeSnapshot, KnowledgeIssue, KnowledgeSource, KnowledgeUnit, RetrievalEvidence


def build_knowledge_snapshot(
    *,
    source_project: str,
    sources: list[KnowledgeSource],
    units: list[KnowledgeUnit],
    retrievals: list[RetrievalEvidence] | None = None,
    issues: list[KnowledgeIssue] | None = None,
    trace: dict | None = None,
) -> KnowledgeIntakeSnapshot:
    all_issues = list(issues or [])
    retrieval_items = list(retrievals or [])
    for source in sources:
        if source.status in {"DRAFT", "PENDING_REVIEW", "REVOKED", "UNKNOWN"}:
            all_issues.append(
                KnowledgeIssue(
                    code=f"SOURCE_{source.status}",
                    severity="WARNING" if source.status != "REVOKED" else "ERROR",
                    message=f"Knowledge source {source.source_id} is {source.status}.",
                    source_id=source.source_id,
                    scope="SOURCE",
                )
            )
    for unit in units:
        if unit.status in {"DRAFT", "PENDING_REVIEW", "REVOKED", "UNKNOWN"}:
            all_issues.append(
                KnowledgeIssue(
                    code=f"UNIT_{unit.status}",
                    severity="WARNING" if unit.status != "REVOKED" else "ERROR",
                    message=f"Knowledge unit {unit.unit_id} is {unit.status}.",
                    source_id=unit.source_id,
                    unit_id=unit.unit_id,
                    scope="UNIT",
                )
            )
    human_review = any(issue.severity == "ERROR" for issue in all_issues) or any(
        retrieval.human_review_required or retrieval.conflict or retrieval.ambiguity for retrieval in retrieval_items
    )
    return KnowledgeIntakeSnapshot(
        source_project=source_project,
        sources=sources,
        units=units,
        retrievals=retrieval_items,
        issues=all_issues,
        human_review_required=human_review,
        trace=dict(trace or {}),
    )


def build_retrieval_evidence(
    *,
    query: str,
    units: list[KnowledgeUnit],
    issues: list[KnowledgeIssue] | None = None,
    confidence: str = "UNKNOWN",
    conflict: bool = False,
    ambiguity: bool = False,
    metadata: dict | None = None,
) -> RetrievalEvidence:
    citations = [citation for unit in units for citation in unit.citations]
    human_review_required = conflict or ambiguity or any(issue.severity == "ERROR" for issue in issues or [])
    if not units:
        human_review_required = True
    return RetrievalEvidence(
        query=query,
        units=units,
        citations=citations,
        issues=list(issues or []),
        confidence=confidence,  # type: ignore[arg-type]
        conflict=conflict,
        ambiguity=ambiguity,
        human_review_required=human_review_required,
        metadata=dict(metadata or {}),
    )
