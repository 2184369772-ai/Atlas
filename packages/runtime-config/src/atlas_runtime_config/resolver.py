from __future__ import annotations

from typing import Any, Iterable

from .models import ConfigEntry, ConfigIssue, ConfigKeySpec, ConfigSource, EffectiveConfig


def resolve_config(specs: Iterable[ConfigKeySpec], sources: Iterable[ConfigSource]) -> EffectiveConfig:
    ordered_sources = sorted(sources, key=lambda source: source.priority)
    entries: dict[str, ConfigEntry] = {}
    issues: list[ConfigIssue] = []

    for spec in specs:
        raw_value: str | None = None
        source_name: str | None = None

        for source in ordered_sources:
            if spec.key in source.values:
                raw_value = source.values[spec.key]
                source_name = source.name
                break

        entry_issues: list[ConfigIssue] = []
        used_default = False

        if raw_value is None:
            if spec.has_default:
                value = spec.default
                used_default = True
            elif spec.required:
                issue = ConfigIssue(
                    code="missing_required",
                    severity="error",
                    key=spec.key,
                    message=f"Required config '{spec.key}' is missing.",
                    suggestion="Provide a value from a configured source.",
                )
                entry_issues.append(issue)
                issues.append(issue)
                entries[spec.key] = ConfigEntry(
                    key=spec.key,
                    value=None,
                    source=None,
                    used_default=False,
                    is_secret=spec.secret,
                    is_valid=False,
                    issues=entry_issues,
                )
                continue
            else:
                entries[spec.key] = ConfigEntry(
                    key=spec.key,
                    value=None,
                    source=None,
                    used_default=False,
                    is_secret=spec.secret,
                    is_valid=True,
                )
                continue
        else:
            converted = _convert_value(raw_value, spec.value_type, spec.key, source_name)
            if isinstance(converted, ConfigIssue):
                entry_issues.append(converted)
                issues.append(converted)
                entries[spec.key] = ConfigEntry(
                    key=spec.key,
                    value=None,
                    source=source_name,
                    used_default=False,
                    is_secret=spec.secret,
                    is_valid=False,
                    issues=entry_issues,
                )
                continue
            value = converted

        entries[spec.key] = ConfigEntry(
            key=spec.key,
            value=value,
            source=source_name,
            used_default=used_default,
            is_secret=spec.secret,
            is_valid=True,
            issues=entry_issues,
        )

    return EffectiveConfig(entries=entries, issues=issues)


def _convert_value(value: Any, value_type: str, key: str, source: str | None) -> Any | ConfigIssue:
    if value_type == "string":
        return str(value)
    if value_type == "number":
        return _convert_number(value, key, source)
    if value_type == "boolean":
        return _convert_boolean(value, key, source)
    return ConfigIssue(
        code="unsupported_type",
        severity="error",
        key=key,
        source=source,
        message=f"Config '{key}' has unsupported type '{value_type}'.",
        suggestion="Use string, number, or boolean.",
    )


def _convert_number(value: Any, key: str, source: str | None) -> int | float | ConfigIssue:
    text = str(value).strip()
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return ConfigIssue(
            code="invalid_number",
            severity="error",
            key=key,
            source=source,
            message=f"Config '{key}' must be a number.",
            suggestion="Provide a numeric value.",
        )


def _convert_boolean(value: Any, key: str, source: str | None) -> bool | ConfigIssue:
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return ConfigIssue(
        code="invalid_boolean",
        severity="error",
        key=key,
        source=source,
        message=f"Config '{key}' must be a boolean.",
        suggestion="Use true/false, yes/no, on/off, or 1/0.",
    )
