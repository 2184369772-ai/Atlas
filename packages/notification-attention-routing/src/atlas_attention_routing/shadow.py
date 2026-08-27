from __future__ import annotations

from dataclasses import dataclass

from .models import AttentionSnapshot
from .routing import attention_routing_issues


@dataclass(slots=True)
class AttentionRoutingDifference:
    scope: str
    signal_id: str
    message: str
    explained: bool = False


def compare_attention_routing(primary: AttentionSnapshot, atlas: AttentionSnapshot) -> list[AttentionRoutingDifference]:
    differences: list[AttentionRoutingDifference] = []
    primary_signals = {signal.signal_id: signal for signal in primary.signals()}
    atlas_signals = {signal.signal_id: signal for signal in atlas.signals()}

    for signal_id in sorted(primary_signals.keys() - atlas_signals.keys()):
        differences.append(AttentionRoutingDifference("signal", signal_id, "Atlas lost a primary attention signal."))
    for signal_id in sorted(atlas_signals.keys() - primary_signals.keys()):
        differences.append(AttentionRoutingDifference("signal", signal_id, "Atlas added a non-primary attention signal.", explained=True))

    for signal_id in sorted(primary_signals.keys() & atlas_signals.keys()):
        if primary_signals[signal_id].semantic_key() != atlas_signals[signal_id].semantic_key():
            differences.append(AttentionRoutingDifference("semantic", signal_id, "Attention target/level/state/reason/timing/source semantics differ."))

    primary_issue_keys = {issue.key() for issue in attention_routing_issues(primary)}
    atlas_issue_keys = {issue.key() for issue in attention_routing_issues(atlas)}
    for issue in sorted(primary_issue_keys - atlas_issue_keys):
        differences.append(AttentionRoutingDifference("issue", issue[2] or issue[0], "Atlas lost an attention routing issue."))

    return differences
