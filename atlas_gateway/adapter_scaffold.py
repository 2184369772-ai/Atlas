from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adoption_profiles import get_profile
from .catalog import get_capability


SUPPORTED_ADAPTERS = {"enterprise-intake", "ai-execution", "knowledge-intake"}


@dataclass(frozen=True, slots=True)
class ScaffoldFile:
    path: Path
    content: str


def init_adapter(capability_name: str, target: str | Path, *, force: bool = False) -> dict[str, Any]:
    if capability_name.strip().upper() == "NO_ATLAS_REUSE":
        return {
            "status": "NO_ATLAS_REUSE",
            "capability_id": "NO_ATLAS_REUSE",
            "target": str(Path(target).resolve()),
            "created_files": [],
            "reason": "NO_ATLAS_REUSE does not create adapter scaffold files.",
        }

    try:
        capability = get_capability(capability_name)
    except KeyError as exc:
        raise ValueError(f"Unknown capability: {capability_name}") from exc

    capability_id = capability["id"]
    recommendation = capability["recommendation"]
    if recommendation == "SEMANTIC_REFERENCE":
        raise ValueError(f"{capability_id} is SEMANTIC_REFERENCE only. Executable adapter scaffold is forbidden.")
    if recommendation == "INBOX_ONLY":
        raise ValueError(f"{capability_id} is INBOX_ONLY. Adapter scaffold is forbidden.")
    if capability_id not in SUPPORTED_ADAPTERS:
        raise ValueError(
            f"{capability_id} has recommendation {recommendation}, but Project Adoption Kit v0.1 has no adapter scaffold template for it."
        )

    target_path = Path(target).resolve()
    files = build_files(capability_id, target_path)
    existing = [file.path for file in files if file.path.exists()]
    if existing and not force:
        existing_list = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"Refusing to overwrite existing files without --force: {existing_list}")

    for file in files:
        file.path.parent.mkdir(parents=True, exist_ok=True)
        file.path.write_text(file.content, encoding="utf-8")

    profile = get_profile(capability_id)
    return {
        "status": "CREATED",
        "capability_id": capability_id,
        "maturity": capability["governance_status"],
        "recommendation": recommendation,
        "target": str(target_path),
        "created_files": [str(file.path) for file in files],
        "adapter_hooks": list(profile.adapter_hooks),
        "boundary": {
            "atlas_owns": list(profile.atlas_owns),
            "project_must_own": list(profile.project_owns),
            "risks": list(profile.risks),
        },
    }


def build_files(capability_id: str, target: Path) -> list[ScaffoldFile]:
    slug = capability_id.replace("-", "_")
    docs_name = capability_id.replace("-", "_")
    files = [
        ScaffoldFile(target / "docs" / f"atlas_{docs_name}_boundary.md", boundary_doc(capability_id)),
    ]
    if capability_id == "enterprise-intake":
        files.extend(
            [
                ScaffoldFile(target / "atlas_adapters" / "enterprise_intake_adapter.py", enterprise_intake_adapter()),
                ScaffoldFile(target / "tests" / "test_enterprise_intake_adapter.py", enterprise_intake_test()),
            ]
        )
    elif capability_id == "ai-execution":
        files.extend(
            [
                ScaffoldFile(target / "atlas_adapters" / "ai_execution_adapter.py", ai_execution_adapter()),
                ScaffoldFile(target / "tests" / "test_ai_execution_adapter.py", ai_execution_test()),
            ]
        )
    elif capability_id == "knowledge-intake":
        files.extend(
            [
                ScaffoldFile(target / "atlas_adapters" / "knowledge_intake_adapter.py", knowledge_intake_adapter()),
                ScaffoldFile(target / "tests" / "test_knowledge_intake_adapter.py", knowledge_intake_test()),
            ]
        )
    return files


def boundary_doc(capability_id: str) -> str:
    profile = get_profile(capability_id)
    lines = [
        f"# Atlas {capability_id} Adapter Boundary",
        "",
        "This scaffold is project-owned. Atlas does not generate business fields, prompts, SQL, database writes, permissions, RAG strategy, or production business rules.",
        "",
        "## Atlas owns",
        "",
    ]
    lines.extend(f"- {item}" for item in profile.atlas_owns)
    lines.extend(["", "## Project must own", ""])
    lines.extend(f"- {item}" for item in profile.project_owns)
    lines.extend(["", "## Adapter hooks", ""])
    lines.extend(f"- {item}" for item in profile.adapter_hooks)
    lines.extend(["", "## Risks and boundaries", ""])
    lines.extend(f"- {item}" for item in profile.risks)
    lines.append("")
    return "\n".join(lines)


def enterprise_intake_adapter() -> str:
    return '''from __future__ import annotations

from atlas_enterprise_intake import IntakeIssue, IntakeRowDecision, IntakeRowInput


class ProjectEnterpriseIntakeAdapter:
    """Project-owned Enterprise Intake adapter scaffold.

    TODO: map project headers, evaluate project business rows, and keep all
    duplicate policy, validation, persistence, transactions, and writes here.
    """

    def resolve_field_mapping(self, _headers: list[object]) -> dict[str, str]:
        # TODO(project): return explicit source-header to project-field mapping.
        return {}

    def evaluate_row(self, row: IntakeRowInput) -> IntakeRowDecision:
        # TODO(project): replace REVIEW with real project validation.
        return IntakeRowDecision(
            decision="REVIEW",
            issues=[
                IntakeIssue(
                    code="PROJECT_HOOK_TODO",
                    severity="WARNING",
                    scope="ADAPTER",
                    message="Implement project-owned Enterprise Intake row evaluation before commit.",
                    row=row.source_row_index,
                )
            ],
            trace={"adapter": "project-enterprise-intake"},
        )
'''


def enterprise_intake_test() -> str:
    return '''from atlas_enterprise_intake import IntakeRowInput
from atlas_adapters.enterprise_intake_adapter import ProjectEnterpriseIntakeAdapter


def test_enterprise_intake_adapter_scaffold_returns_review_until_business_hooks_exist():
    adapter = ProjectEnterpriseIntakeAdapter()
    row = IntakeRowInput(row_index=1, source_row_index=2, raw_values=[], values_by_header={}, mapped_values={})

    decision = adapter.evaluate_row(row)

    assert decision.decision == "REVIEW"
    assert decision.issues[0].code == "PROJECT_HOOK_TODO"
'''


def ai_execution_adapter() -> str:
    return '''from __future__ import annotations

import json

from atlas_ai_execution import AIExecutionRequest, ProviderResponse


class ProjectAIExecutionProvider:
    """Project-owned provider adapter scaffold.

    TODO: call the selected provider in the project layer. Keep provider
    request/response format, retry/timeout, prompts, model choice, RAG,
    business rules, and persistence outside Atlas.
    """

    name = "project-ai-provider"

    def invoke(self, _request: AIExecutionRequest) -> ProviderResponse:
        # TODO(project): replace this synthetic placeholder with project-owned provider invocation.
        return ProviderResponse(
            content=json.dumps(
                {
                    "answer": "TODO project provider response",
                    "confidence": "low",
                    "risk_level": "medium",
                    "manual_required": True,
                }
            ),
            provider=self.name,
            model="project-owned-model-placeholder",
            trace={"adapter": "project-ai-execution"},
        )


def project_fallback(_request: AIExecutionRequest, exc: BaseException) -> dict[str, object]:
    # TODO(project): map provider failures to a safe project fallback.
    return {
        "answer": "TODO project fallback",
        "confidence": "low",
        "risk_level": "medium",
        "manual_required": True,
        "fallback_reason": type(exc).__name__,
    }
'''


def ai_execution_test() -> str:
    return '''from atlas_ai_execution import AIExecutionRequest, execute_ai_request
from atlas_adapters.ai_execution_adapter import ProjectAIExecutionProvider


def test_ai_execution_adapter_scaffold_returns_human_review_result():
    request = AIExecutionRequest(input_payload={"task": "synthetic"}, expected_output="JSON_OBJECT")

    result = execute_ai_request(request, ProjectAIExecutionProvider())

    assert result.status == "SUCCESS"
    assert result.confidence == "LOW"
    assert result.human_escalation_required is True
'''


def knowledge_intake_adapter() -> str:
    return '''from __future__ import annotations

from atlas_knowledge_intake import (
    KnowledgeIssue,
    KnowledgeSource,
    KnowledgeUnit,
    build_knowledge_snapshot,
    build_retrieval_evidence,
)


def build_project_knowledge_snapshot():
    """Project-owned Knowledge Intake adapter scaffold.

    TODO: replace synthetic source/unit mapping with project-owned parser,
    chunking, retrieval/ranking, permissions, and persistence.
    """

    source = KnowledgeSource(
        source_id="PROJECT-SOURCE-TODO",
        title="Project source TODO",
        status="PENDING_REVIEW",
    )
    unit = KnowledgeUnit(
        unit_id="PROJECT-UNIT-TODO",
        source_id=source.source_id,
        source_ref="project-owned-reference",
        status="PENDING_REVIEW",
        confidence="LOW",
    )
    retrieval = build_retrieval_evidence(
        query="project-owned-query-placeholder",
        units=[unit],
        issues=[
            KnowledgeIssue(
                code="PROJECT_HOOK_TODO",
                severity="WARNING",
                message="Implement project-owned Knowledge Intake parser and retrieval hooks.",
                source_id=source.source_id,
                unit_id=unit.unit_id,
            )
        ],
        confidence="LOW",
        ambiguity=True,
    )
    return build_knowledge_snapshot(
        source_project="project-owned",
        sources=[source],
        units=[unit],
        retrievals=[retrieval],
        trace={"adapter": "project-knowledge-intake"},
    )
'''


def knowledge_intake_test() -> str:
    return '''from atlas_adapters.knowledge_intake_adapter import build_project_knowledge_snapshot


def test_knowledge_intake_adapter_scaffold_requires_human_review_until_hooks_exist():
    snapshot = build_project_knowledge_snapshot()

    assert snapshot.human_review_required is True
    assert snapshot.sources[0].status == "PENDING_REVIEW"
    assert snapshot.retrievals[0].human_review_required is True
'''


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
