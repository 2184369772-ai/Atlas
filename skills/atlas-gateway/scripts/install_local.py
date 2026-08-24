from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_NAME = "atlas-gateway"
SKILL_SOURCE = Path(__file__).resolve().parents[1]
DEFAULT_SKILLS_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"
DEFAULT_TARGET = DEFAULT_SKILLS_HOME / SKILL_NAME


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install or remove the local Atlas Gateway skill.")
    parser.add_argument("action", choices=["install", "status", "uninstall"])
    parser.add_argument("--target", default=str(DEFAULT_TARGET), help="Installed skill directory path.")
    parser.add_argument(
        "--mode",
        choices=["junction", "copy"],
        default="junction",
        help="Install as a Windows junction by default, or copy the directory instead.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = Path(args.target).expanduser()

    if args.action == "status":
        return print_status(target)
    if args.action == "uninstall":
        return uninstall(target)
    return install(target, args.mode)


def install(target: Path, mode: str) -> int:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        print(f"Skill target already exists: {target}")
        return 1

    if mode == "copy":
        shutil.copytree(SKILL_SOURCE, target)
        print(f"Installed Atlas Gateway skill by copy: {target}")
        return 0

    if os.name != "nt":
        print("Junction install is only supported on Windows. Use --mode copy instead.")
        return 1

    completed = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(target), str(SKILL_SOURCE)],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr or completed.stdout)
        return completed.returncode

    print(f"Installed Atlas Gateway skill by junction: {target}")
    return 0


def uninstall(target: Path) -> int:
    if not target.exists():
        print(f"Skill target not found: {target}")
        return 0

    if os.name == "nt":
        completed = subprocess.run(
            ["cmd", "/c", "rmdir", "/s", "/q", str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            sys.stderr.write(completed.stderr or completed.stdout)
            return completed.returncode
        print(f"Removed installed skill: {target}")
        return 0

    if target.is_symlink() or target.is_dir():
        shutil.rmtree(target)
        print(f"Removed installed skill: {target}")
        return 0

    print(f"Unsupported target type: {target}")
    return 1


def print_status(target: Path) -> int:
    print(f"SKILL_SOURCE={SKILL_SOURCE}")
    print(f"SKILL_TARGET={target}")
    print(f"TARGET_EXISTS={target.exists()}")
    print(f"SKILL_MD_EXISTS={(target / 'SKILL.md').exists()}")
    print(f"OPENAI_YAML_EXISTS={(target / 'agents' / 'openai.yaml').exists()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
