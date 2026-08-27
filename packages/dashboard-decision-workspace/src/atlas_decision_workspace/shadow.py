from __future__ import annotations

from dataclasses import dataclass

from .models import WorkspaceSnapshot
from .semantics import workspace_semantic_issues


@dataclass(slots=True)
class WorkspaceSemanticDifference:
    scope: str
    key: str
    message: str
    explained: bool = False


def compare_workspace_semantics(primary: WorkspaceSnapshot, atlas: WorkspaceSnapshot) -> list[WorkspaceSemanticDifference]:
    differences: list[WorkspaceSemanticDifference] = []
    primary_sections = {section.section_id: section for section in primary.sections}
    atlas_sections = {section.section_id: section for section in atlas.sections}

    for section_id in sorted(primary_sections.keys() - atlas_sections.keys()):
        differences.append(WorkspaceSemanticDifference("section", section_id, "Atlas lost a primary workspace section."))
    for section_id in sorted(atlas_sections.keys() - primary_sections.keys()):
        differences.append(WorkspaceSemanticDifference("section", section_id, "Atlas added a non-primary workspace section.", explained=True))
    for section_id in sorted(primary_sections.keys() & atlas_sections.keys()):
        if primary_sections[section_id].semantic_key() != atlas_sections[section_id].semantic_key():
            differences.append(WorkspaceSemanticDifference("section", section_id, "Workspace section/item/action semantics differ."))

    primary_items = {item.item_id: item for item in primary.items()}
    atlas_items = {item.item_id: item for item in atlas.items()}
    for item_id in sorted(primary_items.keys() - atlas_items.keys()):
        differences.append(WorkspaceSemanticDifference("item", item_id, "Atlas lost an actionable workspace item."))
    for item_id in sorted(primary_items.keys() & atlas_items.keys()):
        if primary_items[item_id].semantic_key() != atlas_items[item_id].semantic_key():
            differences.append(WorkspaceSemanticDifference("item", item_id, "Workspace item semantics differ."))

    primary_issue_keys = {issue.key() for issue in workspace_semantic_issues(primary)}
    atlas_issue_keys = {issue.key() for issue in workspace_semantic_issues(atlas)}
    for issue in sorted(primary_issue_keys - atlas_issue_keys):
        differences.append(WorkspaceSemanticDifference("issue", issue[2] or issue[0], "Atlas lost a workspace issue."))

    return differences
