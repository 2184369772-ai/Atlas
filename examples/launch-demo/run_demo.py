from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


TASK_REUSE_TEXT = "add Excel import preview with row-level validation"
NO_REUSE_TEXT = "update README wording"
EXPECTED_CAPABILITIES = ["Tabular Core", "Enterprise Intake"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the public-safe Atlas 60-second launch demo.")
    parser.add_argument(
        "--target",
        default=str(Path(__file__).resolve().parent / ".demo-output"),
        help="New directory for generated Enterprise Intake adapter scaffold.",
    )
    return parser.parse_args()


def run_json(command: list[str], *, cwd: Path) -> dict[str, object]:
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise SystemExit(
            f"Command failed: {' '.join(command)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return json.loads(completed.stdout)


def main() -> int:
    args = parse_args()
    atlas = shutil.which("atlas")
    if not atlas:
        raise SystemExit("Atlas CLI was not found. Install it with: pip install git+https://github.com/2184369772-ai/Atlas.git")

    repo_root = Path(__file__).resolve().parents[2]
    reuse_project = repo_root / "examples" / "enterprise-intake-synthetic"
    no_reuse_project = repo_root / "examples" / "no-atlas-reuse"
    target = Path(args.target).expanduser().resolve()
    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing demo target: {target}")
    target.mkdir(parents=True)

    print("DEMO A - Atlas finds reusable engineering contracts")
    print(f'$ atlas project plan . --task "{TASK_REUSE_TEXT}"')
    plan = run_json(
        [atlas, "project", "plan", ".", "--task", TASK_REUSE_TEXT, "--json"],
        cwd=reuse_project,
    )
    capabilities = [item["capability"] for item in plan["recommended_capabilities"]]
    if plan.get("task_overall_decision") != "TASK_REUSE" or capabilities != EXPECTED_CAPABILITIES:
        raise SystemExit(f"Unexpected Demo A routing result: {plan}")
    print("TASK_REUSE")
    for capability in capabilities:
        print(f"- {capability}")

    print(f"\n$ atlas adapter init enterprise-intake --target {target}")
    scaffold = run_json(
        [atlas, "adapter", "init", "enterprise-intake", "--target", str(target), "--json"],
        cwd=repo_root,
    )
    if scaffold.get("status") != "CREATED":
        raise SystemExit(f"Unexpected adapter result: {scaffold}")
    print("Adapter scaffold: CREATED")
    print("Reusable: row decisions, preview issues, partial completion, commit readiness")
    print("Project-owned: business validation, permissions, DB writes")

    print("\nDEMO B - Atlas exits when reuse is not worthwhile")
    print(f'$ atlas project plan . --task "{NO_REUSE_TEXT}"')
    no_reuse = run_json(
        [atlas, "project", "plan", ".", "--task", NO_REUSE_TEXT, "--json"],
        cwd=no_reuse_project,
    )
    if no_reuse.get("task_overall_decision") != "NO_ATLAS_REUSE":
        raise SystemExit(f"Unexpected Demo B routing result: {no_reuse}")
    print("NO_ATLAS_REUSE")
    print("Continue normal development without adding Atlas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
