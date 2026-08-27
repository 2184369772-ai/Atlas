from __future__ import annotations

from .models import WorkspaceIssue, WorkspaceSnapshot


def workspace_semantic_issues(snapshot: WorkspaceSnapshot) -> list[WorkspaceIssue]:
    issues: list[WorkspaceIssue] = list(snapshot.issues)

    if not snapshot.sections:
        issues.append(WorkspaceIssue("workspace.sections_missing", "ERROR", "Workspace snapshot requires at least one section."))

    for section in snapshot.sections:
        if not section.items:
            issues.append(WorkspaceIssue("workspace.section_empty", "INFO", "Workspace section has no items.", section_id=section.section_id))
        if section.section_kind in {"FACTS", "STATUS", "ATTENTION", "RISKS", "OUTCOMES", "REPORTS"} and not section.source_refs:
            issues.append(
                WorkspaceIssue(
                    "workspace.section_source_missing",
                    "WARNING",
                    "Workspace section should preserve source references.",
                    section_id=section.section_id,
                )
            )
        for item in section.items:
            if item.item_kind in {"FACT", "STATUS", "ATTENTION", "RISK", "ISSUE", "OUTCOME", "REPORT"} and not item.source_refs:
                issues.append(
                    WorkspaceIssue(
                        "workspace.item_source_missing",
                        "WARNING",
                        "Workspace item should preserve source references.",
                        item_id=item.item_id,
                        section_id=section.section_id,
                    )
                )
            if item.item_kind in {"ATTENTION", "RISK", "ISSUE", "ACTION"} and item.state == "UNKNOWN":
                issues.append(
                    WorkspaceIssue(
                        "workspace.item_state_unknown",
                        "WARNING",
                        "Actionable workspace items should preserve pending/resolved state.",
                        item_id=item.item_id,
                        section_id=section.section_id,
                    )
                )
            if item.item_kind in {"ATTENTION", "RISK", "ISSUE", "ACTION"} and not item.actions and not item.drilldown_target:
                issues.append(
                    WorkspaceIssue(
                        "workspace.action_entry_missing",
                        "WARNING",
                        "Actionable workspace items should preserve an action or drill-down target.",
                        item_id=item.item_id,
                        section_id=section.section_id,
                    )
                )
            for action in item.actions:
                if not action.target_ref:
                    issues.append(
                        WorkspaceIssue(
                            "workspace.action_target_missing",
                            "ERROR",
                            "Workspace action entries require a target reference.",
                            item_id=item.item_id,
                            section_id=section.section_id,
                        )
                    )

    return issues
