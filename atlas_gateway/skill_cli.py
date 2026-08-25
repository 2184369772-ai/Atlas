from __future__ import annotations

import os
import shutil
from importlib import resources
from pathlib import Path
from typing import Any

from .catalog import REPO_ROOT


SKILL_NAME = "atlas-gateway"


def default_skill_target() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills" / SKILL_NAME


def skill_source_kind() -> str:
    if filesystem_skill_source().exists():
        return "filesystem"
    return "package-resource"


def filesystem_skill_source() -> Path:
    return REPO_ROOT / "skills" / SKILL_NAME


def skill_status(target: str | Path | None = None) -> dict[str, Any]:
    target_path = Path(target).expanduser() if target is not None else default_skill_target()
    source_kind = skill_source_kind()
    source_label = str(filesystem_skill_source()) if source_kind == "filesystem" else "package-resource:atlas_gateway/resources/skills/atlas-gateway"
    return {
        "skill": SKILL_NAME,
        "source_kind": source_kind,
        "source": source_label,
        "target": str(target_path),
        "target_exists": target_path.exists(),
        "skill_md_exists": (target_path / "SKILL.md").exists(),
        "openai_yaml_exists": (target_path / "agents" / "openai.yaml").exists(),
    }


def install_skill(target: str | Path | None = None, *, force: bool = False) -> dict[str, Any]:
    target_path = Path(target).expanduser() if target is not None else default_skill_target()
    if target_path.exists():
        if not force:
            raise FileExistsError(f"Skill target already exists. Use --force to replace it: {target_path}")
        if target_path.name != SKILL_NAME:
            raise ValueError(f"Refusing to replace a target whose final path segment is not {SKILL_NAME}: {target_path}")
        shutil.rmtree(target_path)

    target_path.parent.mkdir(parents=True, exist_ok=True)
    source = filesystem_skill_source()
    if (source / "SKILL.md").exists():
        shutil.copytree(source, target_path)
        source_kind = "filesystem"
    else:
        copy_resource_tree(resource_skill_source(), target_path)
        source_kind = "package-resource"

    return {
        "status": "INSTALLED",
        "mode": "copy",
        "skill": SKILL_NAME,
        "source_kind": source_kind,
        "target": str(target_path),
    }


def uninstall_skill(target: str | Path | None = None) -> dict[str, Any]:
    target_path = Path(target).expanduser() if target is not None else default_skill_target()
    if not target_path.exists():
        return {"status": "NOT_FOUND", "skill": SKILL_NAME, "target": str(target_path)}
    if target_path.name != SKILL_NAME:
        raise ValueError(f"Refusing to remove a target whose final path segment is not {SKILL_NAME}: {target_path}")
    shutil.rmtree(target_path)
    return {"status": "REMOVED", "skill": SKILL_NAME, "target": str(target_path)}


def resource_skill_source():
    return resources.files("atlas_gateway").joinpath("resources/skills/atlas-gateway")


def copy_resource_tree(source, target: Path) -> None:
    if source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        return

    target.mkdir(parents=True, exist_ok=True)
    for child in source.iterdir():
        copy_resource_tree(child, target / child.name)
