from __future__ import annotations

import os
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


_MISSING = object()


@dataclass(frozen=True, slots=True)
class ConfigSource:
    name: str
    values: Mapping[str, str]
    source_type: str = "mapping"
    priority: int = 100

    @classmethod
    def from_environ(
        cls,
        name: str = "environment",
        environ: Mapping[str, str] | None = None,
        priority: int = 100,
    ) -> "ConfigSource":
        values = dict(os.environ if environ is None else environ)
        return cls(name=name, values=MappingProxyType(values), source_type="environment", priority=priority)


@dataclass(frozen=True, slots=True)
class ConfigKeySpec:
    key: str
    value_type: str = "string"
    required: bool = False
    default: Any = _MISSING
    secret: bool = False
    description: str = ""

    @property
    def has_default(self) -> bool:
        return self.default is not _MISSING


@dataclass(slots=True)
class ConfigIssue:
    code: str
    severity: str
    message: str
    key: str | None = None
    source: str | None = None
    suggestion: str | None = None


@dataclass(slots=True)
class ConfigEntry:
    key: str
    value: Any
    source: str | None = None
    used_default: bool = False
    is_secret: bool = False
    is_valid: bool = True
    issues: list[ConfigIssue] = field(default_factory=list)

    @property
    def safe_value(self) -> Any:
        if self.is_secret and self.value is not None:
            return "<redacted>"
        return self.value


@dataclass(slots=True)
class EffectiveConfig:
    entries: dict[str, ConfigEntry] = field(default_factory=dict)
    issues: list[ConfigIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def get(self, key: str, default: Any = None) -> Any:
        entry = self.entries.get(key)
        if entry is None:
            return default
        return entry.value

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "entries": {
                key: {
                    "key": entry.key,
                    "value": entry.safe_value,
                    "source": entry.source,
                    "used_default": entry.used_default,
                    "is_secret": entry.is_secret,
                    "is_valid": entry.is_valid,
                    "issues": [
                        {
                            "code": issue.code,
                            "severity": issue.severity,
                            "message": issue.message,
                            "key": issue.key,
                            "source": issue.source,
                            "suggestion": issue.suggestion,
                        }
                        for issue in entry.issues
                    ],
                }
                for key, entry in self.entries.items()
            },
            "issues": [
                {
                    "code": issue.code,
                    "severity": issue.severity,
                    "message": issue.message,
                    "key": issue.key,
                    "source": issue.source,
                    "suggestion": issue.suggestion,
                }
                for issue in self.issues
            ],
            "is_valid": self.is_valid,
        }
