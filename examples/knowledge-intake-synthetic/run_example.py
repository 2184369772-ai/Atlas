from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
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


def to_plain(value: Any) -> Any:
    if is_dataclass(value):
        return {key: to_plain(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    return value


def main() -> int:
    approved_source = KnowledgeSource(
        source_id="SRC-SYN-001",
        title="Synthetic Maintenance Note",
        source_type="FILE",
        version="1.0",
        status="APPROVED",
        uri="synthetic://maintenance-note",
        checksum="synthetic-checksum-001",
    )
    draft_source = KnowledgeSource(
        source_id="SRC-SYN-002",
        title="Synthetic Draft Addendum",
        source_type="HUMAN_SUPPLIED",
        version="0.1",
        status="PENDING_REVIEW",
    )
    approved_unit = KnowledgeUnit(
        unit_id="UNIT-SYN-001",
        source_id=approved_source.source_id,
        title="Safe restart check",
        text="Synthetic instruction: verify local status before restart.",
        source_ref="section 1",
        status="APPROVED",
        confidence="HIGH",
    )
    draft_unit = KnowledgeUnit(
        unit_id="UNIT-SYN-002",
        source_id=draft_source.source_id,
        title="Draft exception note",
        text="Synthetic draft note that conflicts with the approved source.",
        source_ref="draft note",
        status="PENDING_REVIEW",
        confidence="LOW",
    )
    retrieval = build_retrieval_evidence(
        query="synthetic restart procedure",
        units=[approved_unit, draft_unit],
        issues=[
            KnowledgeIssue(
                code="SYNTHETIC_CONFLICT",
                severity="ERROR",
                message="Synthetic approved and draft sources conflict.",
                source_id=draft_source.source_id,
                unit_id=draft_unit.unit_id,
                scope="RETRIEVAL",
            )
        ],
        confidence="MEDIUM",
        conflict=True,
        metadata={"retrieval_mode": "synthetic-public"},
    )
    snapshot = build_knowledge_snapshot(
        source_project="synthetic-public",
        sources=[approved_source, draft_source],
        units=[approved_unit, draft_unit],
        retrievals=[retrieval],
        trace={"example": "knowledge-intake-synthetic"},
    )
    payload = {
        "summary": {
            "source_count": len(snapshot.sources),
            "unit_count": len(snapshot.units),
            "retrieval_count": len(snapshot.retrievals),
            "citation_count": len(snapshot.retrievals[0].citations),
            "issue_count": len(snapshot.issues) + len(snapshot.retrievals[0].issues),
            "retrieval_confidence": snapshot.retrievals[0].confidence,
            "conflict": snapshot.retrievals[0].conflict,
            "human_review_required": snapshot.human_review_required,
            "statuses": [source.status for source in snapshot.sources],
        },
        "snapshot": to_plain(snapshot),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
