from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_file_lifecycle_synthetic_example_runs():
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "examples" / "file-lifecycle-synthetic" / "run_example.py")],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert '"status": "MATCH"' in completed.stdout
    assert '"lost_metadata": 0' in completed.stdout


def test_operation_outcome_synthetic_example_runs():
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / "examples" / "operation-outcome-synthetic" / "run_example.py")],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert '"status": "PARTIAL"' in completed.stdout
    assert '"human_attention_required": true' in completed.stdout
