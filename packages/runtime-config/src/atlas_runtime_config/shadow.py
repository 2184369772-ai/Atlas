from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from .models import EffectiveConfig


@dataclass(frozen=True, slots=True)
class RuntimeConfigDiff:
    status: str
    differences: tuple[dict[str, Any], ...]
    lost_config_issues: tuple[str, ...]
    unsafe_secret_fields: tuple[str, ...]
    unexplained_differences: tuple[dict[str, Any], ...]

    @property
    def is_match(self) -> bool:
        return self.status == "MATCH"


def project_config(config: EffectiveConfig) -> dict[str, Any]:
    return {
        "entries": {
            key: {
                "value": entry.safe_value,
                "source": entry.source,
                "used_default": entry.used_default,
                "is_secret": entry.is_secret,
                "is_valid": entry.is_valid,
                "issue_codes": tuple(issue.code for issue in entry.issues),
            }
            for key, entry in config.entries.items()
        },
        "issue_codes": tuple(issue.code for issue in config.issues),
        "is_valid": config.is_valid,
    }


def compare_runtime_config(
    primary: dict[str, Any],
    atlas: EffectiveConfig | dict[str, Any],
    *,
    explained_fields: Iterable[str] = (),
) -> RuntimeConfigDiff:
    atlas_projection = project_config(atlas) if isinstance(atlas, EffectiveConfig) else atlas
    explained = set(explained_fields)
    differences: list[dict[str, Any]] = []
    lost_issues: list[str] = []
    unsafe_secret_fields: list[str] = []

    primary_entries = primary.get("entries", {})
    atlas_entries = atlas_projection.get("entries", {})
    all_keys = sorted(set(primary_entries) | set(atlas_entries))
    for key in all_keys:
        primary_entry = primary_entries.get(key)
        atlas_entry = atlas_entries.get(key)
        if primary_entry is None or atlas_entry is None:
            differences.append({"field": f"entries.{key}", "primary": primary_entry, "atlas": atlas_entry})
            continue

        if atlas_entry.get("is_secret") and atlas_entry.get("value") not in {None, "<redacted>"}:
            unsafe_secret_fields.append(key)

        for field in ("value", "source", "used_default", "is_secret", "is_valid", "issue_codes"):
            primary_value = _normalize(primary_entry.get(field))
            atlas_value = _normalize(atlas_entry.get(field))
            if primary_value != atlas_value:
                differences.append(
                    {
                        "field": f"entries.{key}.{field}",
                        "primary": primary_entry.get(field),
                        "atlas": atlas_entry.get(field),
                    }
                )

    for field in ("issue_codes", "is_valid"):
        primary_value = _normalize(primary.get(field))
        atlas_value = _normalize(atlas_projection.get(field))
        if primary_value != atlas_value:
            differences.append({"field": field, "primary": primary.get(field), "atlas": atlas_projection.get(field)})

    primary_issue_codes = set(primary.get("issue_codes", ()))
    atlas_issue_codes = set(atlas_projection.get("issue_codes", ()))
    for code in sorted(primary_issue_codes - atlas_issue_codes):
        lost_issues.append(code)

    unexplained = tuple(diff for diff in differences if diff["field"] not in explained)
    status = "MATCH" if not unexplained and not unsafe_secret_fields and not lost_issues else "DIFFERENCE"
    return RuntimeConfigDiff(
        status=status,
        differences=tuple(differences),
        lost_config_issues=tuple(lost_issues),
        unsafe_secret_fields=tuple(unsafe_secret_fields),
        unexplained_differences=unexplained,
    )


def _normalize(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(value)
    return value
