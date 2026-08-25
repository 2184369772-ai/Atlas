from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .models import FileItem


@dataclass(frozen=True, slots=True)
class FileLifecycleDiff:
    status: str
    differences: tuple[dict[str, Any], ...]
    lost_metadata: tuple[str, ...]
    lost_issues: tuple[str, ...]
    unexplained_differences: tuple[dict[str, Any], ...]

    @property
    def is_match(self) -> bool:
        return self.status == "MATCH"


def project_file_item(item: FileItem) -> dict[str, Any]:
    reference = item.reference
    return {
        "id": item.id,
        "source_kind": item.source.source_kind,
        "source_label": item.source.source_label,
        "state": item.state.value,
        "state_reason": item.state.reason,
        "retention_mode": item.retention.mode,
        "retention_reason": item.retention.reason,
        "reference_kind": reference.reference_kind if reference else None,
        "locator": reference.locator if reference else None,
        "display_locator": reference.display_locator if reference else None,
        "original_name": item.metadata.original_name,
        "display_name": item.metadata.display_name,
        "extension": item.metadata.extension,
        "media_type": item.metadata.media_type,
        "size_bytes": item.metadata.size_bytes,
        "checksum": item.metadata.checksum,
        "issue_codes": tuple(issue.code for issue in item.issues),
        "issue_severities": tuple(issue.severity for issue in item.issues),
    }


def compare_file_lifecycle(
    primary: dict[str, Any],
    atlas: FileItem | dict[str, Any],
    *,
    explained_fields: Iterable[str] = (),
) -> FileLifecycleDiff:
    atlas_projection = project_file_item(atlas) if isinstance(atlas, FileItem) else atlas
    explained = set(explained_fields)
    differences: list[dict[str, Any]] = []
    lost_metadata: list[str] = []
    lost_issues: list[str] = []

    for key, primary_value in primary.items():
        atlas_value = atlas_projection.get(key)
        if _normalize(primary_value) == _normalize(atlas_value):
            continue
        diff = {"field": key, "primary": primary_value, "atlas": atlas_value}
        differences.append(diff)
        if key not in explained:
            if key.startswith("issue_"):
                lost_issues.append(key)
            else:
                lost_metadata.append(key)

    unexplained = tuple(diff for diff in differences if diff["field"] not in explained)
    return FileLifecycleDiff(
        status="MATCH" if not unexplained else "DIFFERENCE",
        differences=tuple(differences),
        lost_metadata=tuple(lost_metadata),
        lost_issues=tuple(lost_issues),
        unexplained_differences=unexplained,
    )


def to_public_dict(item: FileItem) -> dict[str, Any]:
    return asdict(item)


def _normalize(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(value)
    return value
