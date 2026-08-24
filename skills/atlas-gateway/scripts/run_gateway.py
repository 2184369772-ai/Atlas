from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


REQUIRED_MARKERS = (
    "atlas_gateway",
    "atlas_consumer",
    "registry/capability-catalog.json",
    "skills/atlas-gateway/SKILL.md",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Locate Atlas Gateway safely and forward commands to it.",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print the resolved Atlas repository and exit.",
    )
    parser.add_argument(
        "gateway_args",
        nargs=argparse.REMAINDER,
        help="Arguments forwarded to python -m atlas_gateway.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    repo_root = resolve_repo_root()

    if args.status:
        print(f"ATLAS_REPO_ROOT={repo_root}")
        print("ATLAS_GATEWAY=available")
        return 0

    if not args.gateway_args:
        print("Atlas Gateway runner requires Gateway arguments, or use --status.", file=sys.stderr)
        return 2

    completed = subprocess.run(
        [sys.executable, "-m", "atlas_gateway", *args.gateway_args],
        cwd=repo_root,
        text=True,
        check=False,
        capture_output=False,
    )
    return completed.returncode


def resolve_repo_root() -> Path:
    env_root = os.environ.get("ATLAS_REPO_ROOT")
    if env_root:
        candidate = Path(env_root).expanduser().resolve()
        if is_repo_root(candidate):
            return candidate

    cwd_root = find_repo_root(Path.cwd())
    if cwd_root is not None:
        return cwd_root

    script_root = find_repo_root(Path(__file__).resolve())
    if script_root is not None:
        return script_root

    raise SystemExit(
        "Atlas Gateway could not be located. Set ATLAS_REPO_ROOT to the Atlas repository root, "
        "or run this command from inside the Atlas repository or a project where Atlas can be discovered."
    )


def find_repo_root(start: Path) -> Path | None:
    current = start if start.is_dir() else start.parent
    for candidate in (current, *current.parents):
        if is_repo_root(candidate):
            return candidate
    return None


def is_repo_root(path: Path) -> bool:
    return all((path / marker).exists() for marker in REQUIRED_MARKERS)


if __name__ == "__main__":
    raise SystemExit(main())
