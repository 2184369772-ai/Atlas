from __future__ import annotations

from .models import AttentionIssue, AttentionSnapshot


def attention_routing_issues(snapshot: AttentionSnapshot) -> list[AttentionIssue]:
    issues: list[AttentionIssue] = list(snapshot.issues)
    seen_repeat_keys: dict[str, str] = {}

    for signal in snapshot.signals():
        if not signal.event_ref:
            issues.append(AttentionIssue("attention.event_missing", "ERROR", "Attention signal must reference the triggering event.", signal.signal_id))
        if not signal.targets:
            issues.append(AttentionIssue("attention.target_missing", "ERROR", "Attention signal must have at least one semantic target.", signal.signal_id))
        if not signal.reasons:
            issues.append(AttentionIssue("attention.reason_missing", "ERROR", "Attention signal must preserve why attention is needed.", signal.signal_id))
        if signal.level in {"ACTION_REQUIRED", "REVIEW_REQUIRED", "URGENT"} and signal.state in {"RESOLVED", "DISMISSED"}:
            if not (signal.resolved_ref or signal.dismissed_ref):
                issues.append(
                    AttentionIssue(
                        "attention.close_ref_missing",
                        "WARNING",
                        "Closed attention signals should preserve resolved or dismissed reference.",
                        signal.signal_id,
                    )
                )
        if signal.state == "ACKNOWLEDGED" and not signal.acknowledgement_ref:
            issues.append(
                AttentionIssue(
                    "attention.ack_ref_missing",
                    "WARNING",
                    "Acknowledged attention signals should preserve acknowledgement reference.",
                    signal.signal_id,
                )
            )
        repeat_key = signal.timing.repeated_notice_key
        if repeat_key:
            previous = seen_repeat_keys.get(repeat_key)
            if previous:
                issues.append(
                    AttentionIssue(
                        "attention.repeated_notice_key_duplicate",
                        "INFO",
                        "Repeated notices share a dedupe key and should be handled by project-owned delivery logic.",
                        signal.signal_id,
                    )
                )
            else:
                seen_repeat_keys[repeat_key] = signal.signal_id

    return issues
