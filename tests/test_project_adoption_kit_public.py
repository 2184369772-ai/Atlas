from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def fixture_path(name: str) -> str:
    public_path = REPO_ROOT / "tests" / "fixtures" / name
    private_packaging_path = REPO_ROOT / "tests" / "fixtures" / "public_packaging" / name
    if public_path.exists():
        return f"tests/fixtures/{name}"
    return f"tests/fixtures/public_packaging/{name}"


def run_atlas(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "atlas_gateway", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_project_plan_public_knowledge_fixture():
    completed = run_atlas("project", "plan", fixture_path("project_knowledge_intake"), "--json")

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    item = next(entry for entry in payload["recommended_capabilities"] if entry["capability_id"] == "knowledge-intake")
    assert item["recommendation"] == "REFERENCE_ONLY"
    assert "embedding/vector DB" in item["project_must_own"]
    assert item["adapter_scaffold_supported"] is True


def test_project_plan_public_no_reuse_fixture():
    completed = run_atlas("project", "plan", fixture_path("project_no_reuse"), "--json")

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["overall_recommendation"] == "NO_ATLAS_REUSE"
    assert payload["recommended_capabilities"] == []


def test_adapter_init_public_boundary_and_no_overwrite(tmp_path: Path):
    first = run_atlas("adapter", "init", "ai-execution", "--target", str(tmp_path), "--json")
    second = run_atlas("adapter", "init", "ai-execution", "--target", str(tmp_path), "--json")

    assert first.returncode == 0
    payload = json.loads(first.stdout)
    assert payload["recommendation"] == "REFERENCE_ONLY"
    assert any(path.endswith("ai_execution_adapter.py") for path in payload["created_files"])
    assert second.returncode == 1
    assert "Refusing to overwrite" in second.stderr


def test_adapter_init_public_rejects_semantic_reference(tmp_path: Path):
    completed = run_atlas("adapter", "init", "operation-outcome", "--target", str(tmp_path))

    assert completed.returncode == 1
    assert "SEMANTIC_REFERENCE" in completed.stderr


def test_doctor_public_json():
    completed = run_atlas("doctor")

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["gateway_available"] is True
    assert payload["capability_catalog"]["available"] is True
    assert "packages" in payload


def test_skill_cli_install_status_uninstall(tmp_path: Path):
    target = tmp_path / "atlas-gateway"

    install = run_atlas("skill", "install", "--target", str(target), "--json")
    status = run_atlas("skill", "status", "--target", str(target), "--json")
    uninstall = run_atlas("skill", "uninstall", "--target", str(target), "--json")

    assert install.returncode == 0, install.stderr
    assert status.returncode == 0
    assert uninstall.returncode == 0
    assert json.loads(install.stdout)["mode"] == "copy"
    assert json.loads(status.stdout)["skill_md_exists"] is True
    assert json.loads(uninstall.stdout)["status"] == "REMOVED"


def test_setup_public_json():
    completed = run_atlas("setup", "--json")

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["doctor"]["gateway_available"] is True
    assert "atlas skill install" in payload["next_steps"][0]
