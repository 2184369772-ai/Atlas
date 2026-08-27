from __future__ import annotations

from .models import TraceChain, TraceEvent, TraceIssue, TraceReference, TraceSource


def build_trace_chain(
    chain_id: str,
    subject_id: str,
    events: list[TraceEvent],
    sources: list[TraceSource] | None = None,
    references: list[TraceReference] | None = None,
) -> TraceChain:
    ordered = sorted(events, key=lambda event: (event.occurred_at, event.event_id))
    return TraceChain(chain_id=chain_id, subject_id=subject_id, sources=sources or [], events=ordered, references=references or [])


def trace_chain_issues(chain: TraceChain) -> list[TraceIssue]:
    issues: list[TraceIssue] = []
    known_events = chain.event_ids()
    source_ids = {source.source_id for source in chain.sources}
    references = {reference.ref_id for reference in chain.references}

    for event in chain.events:
        if not event.occurred_at:
            issues.append(TraceIssue("trace.timestamp_missing", "WARNING", "Trace event has no timestamp.", event.event_id, event.subject_id))
        if event.actor is None and not event.producer:
            issues.append(TraceIssue("trace.producer_missing", "WARNING", "Trace event has no actor or producer.", event.event_id, event.subject_id))
        for parent in event.derived_from:
            if parent not in known_events:
                issues.append(TraceIssue("trace.parent_missing", "ERROR", "Trace event derives from an unknown event.", event.event_id, event.subject_id))
        for superseded in event.supersedes:
            if superseded not in known_events:
                issues.append(TraceIssue("trace.superseded_event_missing", "ERROR", "Trace event supersedes an unknown event.", event.event_id, event.subject_id))
        for reference in event.references:
            if reference.ref_id and reference.ref_id not in references:
                issues.append(TraceIssue("trace.reference_unregistered", "WARNING", "Trace event uses a reference not registered on the chain.", event.event_id, event.subject_id))
            if reference.source_id and source_ids and reference.source_id not in source_ids:
                issues.append(TraceIssue("trace.source_missing", "ERROR", "Trace reference points to an unknown source.", event.event_id, event.subject_id))
        if event.immutable_formal_fact and event.event_type in {"UPDATED", "REPLACED"} and not event.reason:
            issues.append(TraceIssue("trace.formal_fact_reason_missing", "ERROR", "Formal-fact change requires an explicit reason.", event.event_id, event.subject_id))
    return issues
