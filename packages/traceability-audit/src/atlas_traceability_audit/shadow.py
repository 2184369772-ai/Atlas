from __future__ import annotations

from dataclasses import dataclass

from .models import TraceChain


@dataclass(slots=True)
class TraceabilityDifference:
    scope: str
    event_id: str
    message: str
    explained: bool = False


def compare_traceability(primary: TraceChain, atlas: TraceChain) -> list[TraceabilityDifference]:
    differences: list[TraceabilityDifference] = []
    primary_events = {event.event_id: event for event in primary.events}
    atlas_events = {event.event_id: event for event in atlas.events}

    for event_id in sorted(primary_events.keys() - atlas_events.keys()):
        differences.append(TraceabilityDifference("event", event_id, "Atlas lost a primary trace event."))
    for event_id in sorted(atlas_events.keys() - primary_events.keys()):
        differences.append(TraceabilityDifference("event", event_id, "Atlas added a non-primary trace event.", explained=True))
    for event_id in sorted(primary_events.keys() & atlas_events.keys()):
        if primary_events[event_id].semantic_key() != atlas_events[event_id].semantic_key():
            differences.append(TraceabilityDifference("semantic", event_id, "Trace event semantics differ."))

    primary_sources = {source.key() for source in primary.sources}
    atlas_sources = {source.key() for source in atlas.sources}
    for source in sorted(primary_sources - atlas_sources):
        differences.append(TraceabilityDifference("source", source[1], "Atlas lost a trace source."))

    primary_refs = {reference.key() for reference in primary.references}
    atlas_refs = {reference.key() for reference in atlas.references}
    for reference in sorted(primary_refs - atlas_refs):
        differences.append(TraceabilityDifference("reference", reference[0], "Atlas lost a trace reference."))

    return differences
