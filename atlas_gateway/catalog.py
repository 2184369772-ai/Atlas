from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = REPO_ROOT / "registry" / "capability-catalog.json"


def load_catalog() -> dict[str, Any]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def list_capabilities() -> list[dict[str, Any]]:
    payload = load_catalog()
    return sorted(payload["capabilities"], key=lambda item: item["id"])


def get_capability(identifier: str) -> dict[str, Any]:
    normalized = identifier.strip().lower()
    for capability in list_capabilities():
        aliases = {capability["id"].lower(), capability["name"].lower()}
        aliases.update(alias.lower() for alias in capability.get("aliases", []))
        if normalized in aliases:
            return capability
    raise KeyError(identifier)
