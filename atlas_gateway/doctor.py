from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

from .catalog import CATALOG_PATH, REPO_ROOT, load_catalog


PACKAGE_PATHS = {
    "atlas_tabular": REPO_ROOT / "packages" / "tabular-input" / "src",
    "atlas_enterprise_intake": REPO_ROOT / "packages" / "enterprise-intake" / "src",
    "atlas_ai_execution": REPO_ROOT / "packages" / "ai-execution" / "src",
    "atlas_knowledge_intake": REPO_ROOT / "packages" / "knowledge-intake" / "src",
}


def run_doctor() -> dict[str, Any]:
    catalog_status = check_catalog()
    package_status = check_packages()
    skill_status = check_skill()
    issues = []
    if not catalog_status["available"]:
        issues.append("Capability catalog is unavailable.")
    issues.extend(f"Package is not importable: {name}" for name, status in package_status.items() if not status["importable"])
    if not skill_status["source_exists"]:
        issues.append("Bundled Atlas Gateway skill source was not found.")

    return {
        "atlas_version": catalog_status.get("catalog_version", "UNKNOWN"),
        "gateway_available": True,
        "repo_root": str(REPO_ROOT),
        "python": sys.executable,
        "capability_catalog": catalog_status,
        "packages": package_status,
        "skill": skill_status,
        "issues": issues,
        "status": "OK" if not issues else "ATTENTION",
    }


def check_catalog() -> dict[str, Any]:
    if not CATALOG_PATH.exists():
        return {"path": str(CATALOG_PATH), "available": False, "capability_count": 0}
    payload = load_catalog()
    return {
        "path": str(CATALOG_PATH),
        "available": True,
        "catalog_version": payload.get("catalog_version", "UNKNOWN"),
        "capability_count": len(payload.get("capabilities", [])),
    }


def check_packages() -> dict[str, dict[str, Any]]:
    statuses: dict[str, dict[str, Any]] = {}
    inserted: list[str] = []
    for source in PACKAGE_PATHS.values():
        source_text = str(source)
        if source.exists() and source_text not in sys.path:
            sys.path.insert(0, source_text)
            inserted.append(source_text)
    try:
        for package, source in PACKAGE_PATHS.items():
            spec = importlib.util.find_spec(package)
            statuses[package] = {
                "source_path": str(source),
                "source_exists": source.exists(),
                "importable": spec is not None,
                "origin": getattr(spec, "origin", None) if spec else None,
            }
    finally:
        for source_text in inserted:
            try:
                sys.path.remove(source_text)
            except ValueError:
                pass
    return statuses


def check_skill() -> dict[str, Any]:
    source = REPO_ROOT / "skills" / "atlas-gateway"
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    target = codex_home / "skills" / "atlas-gateway"
    return {
        "source_path": str(source),
        "source_exists": (source / "SKILL.md").exists(),
        "installed_path_checked": str(target),
        "installed": (target / "SKILL.md").exists(),
        "note": "Doctor only checks obvious local skill paths and does not install or modify anything.",
    }


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
