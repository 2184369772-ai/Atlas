from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_SRC = REPO_ROOT / "packages" / "knowledge-intake" / "src"
if str(KNOWLEDGE_SRC) not in sys.path:
    sys.path.insert(0, str(KNOWLEDGE_SRC))

from atlas_knowledge_intake import (  # noqa: E402
    KnowledgeIssue,
    KnowledgeSource,
    KnowledgeUnit,
    build_knowledge_snapshot,
    build_retrieval_evidence,
)


def test_source_unit_citation_and_retrieval_evidence_are_preserved():
    source = KnowledgeSource(source_id="SRC-SYN-001", title="Synthetic Note", version="1", status="APPROVED")
    unit = KnowledgeUnit(unit_id="UNIT-SYN-001", source_id=source.source_id, source_ref="section 1", status="APPROVED")
    retrieval = build_retrieval_evidence(query="synthetic query", units=[unit], confidence="HIGH")

    snapshot = build_knowledge_snapshot(source_project="synthetic-public", sources=[source], units=[unit], retrievals=[retrieval])

    assert snapshot.sources[0].source_id == "SRC-SYN-001"
    assert snapshot.units[0].source_id == source.source_id
    assert snapshot.retrievals[0].citations[0].reference == "section 1"
    assert snapshot.human_review_required is False


def test_conflict_and_unapproved_source_trigger_human_review():
    source = KnowledgeSource(source_id="SRC-SYN-002", title="Draft", status="PENDING_REVIEW")
    unit = KnowledgeUnit(unit_id="UNIT-SYN-002", source_id=source.source_id, status="PENDING_REVIEW")
    retrieval = build_retrieval_evidence(
        query="synthetic query",
        units=[unit],
        issues=[KnowledgeIssue(code="SYNTHETIC_CONFLICT", severity="ERROR", message="conflict")],
        confidence="LOW",
        conflict=True,
    )

    snapshot = build_knowledge_snapshot(source_project="synthetic-public", sources=[source], units=[unit], retrievals=[retrieval])

    assert snapshot.human_review_required is True
    assert any(issue.code == "SOURCE_PENDING_REVIEW" for issue in snapshot.issues)


def test_public_example_runs_with_synthetic_sources_only():
    completed = subprocess.run(
        [sys.executable, "examples/knowledge-intake-synthetic/run_example.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["summary"]["source_count"] == 2
    assert payload["summary"]["unit_count"] == 2
    assert payload["summary"]["conflict"] is True
    assert payload["summary"]["human_review_required"] is True
