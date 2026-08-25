from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdoptionProfile:
    atlas_owns: tuple[str, ...]
    project_owns: tuple[str, ...]
    adapter_hooks: tuple[str, ...]
    risks: tuple[str, ...]
    can_scaffold_adapter: bool = False


PROFILES: dict[str, AdoptionProfile] = {
    "tabular-core": AdoptionProfile(
        atlas_owns=(
            "read-only CSV/XLSX structure",
            "workbook/sheet/header/row/cell semantics",
            "general value semantics and structural issues",
        ),
        project_owns=(
            "business sheet selection",
            "field mapping",
            "business validation",
            "workflow and persistence",
        ),
        adapter_hooks=(
            "project field mapping",
            "project validation",
            "project import/write boundary",
        ),
        risks=(
            "Do not treat a spreadsheet file alone as proof that Atlas is required.",
            "Do not move business rules into Tabular Core.",
        ),
    ),
    "enterprise-intake": AdoptionProfile(
        atlas_owns=(
            "tabular preview semantics",
            "row decision shape",
            "issue aggregation",
            "partial completion",
            "commit readiness signal",
        ),
        project_owns=(
            "business fields",
            "duplicate policy",
            "business validation",
            "persistence, transactions, and database writes",
            "permissions",
        ),
        adapter_hooks=(
            "resolve_field_mapping(headers)",
            "evaluate_row(row)",
            "optional duplicate check",
            "optional trace metadata",
        ),
        risks=(
            "Candidate only: use as reference implementation, not stable platform promise.",
            "The scaffold must not generate business fields, SQL, transactions, or writes.",
        ),
        can_scaffold_adapter=True,
    ),
    "ai-execution": AdoptionProfile(
        atlas_owns=(
            "execution request/result semantics",
            "failure normalization",
            "fallback signal",
            "evidence reference",
            "confidence/risk",
            "human escalation",
            "trace/outcome",
        ),
        project_owns=(
            "provider invocation",
            "provider request/response formats",
            "retry/timeout implementation",
            "prompts",
            "model choice",
            "RAG/Knowledge",
            "business rules",
            "persistence",
        ),
        adapter_hooks=(
            "ProviderInvocation.invoke(request)",
            "fallback builder",
            "project trace mapping",
            "project evidence mapping",
        ),
        risks=(
            "Candidate only: not an AI Agent platform, prompt framework, RAG framework, model SDK replacement, or workflow system.",
            "The scaffold must not call external providers or generate prompts.",
        ),
        can_scaffold_adapter=True,
    ),
    "knowledge-intake": AdoptionProfile(
        atlas_owns=(
            "source identity",
            "version/status",
            "knowledge unit to source linkage",
            "citation/provenance",
            "retrieval evidence",
            "issue/conflict",
            "human-review signal",
        ),
        project_owns=(
            "OCR/parser",
            "chunking",
            "embedding/vector DB",
            "retrieval/ranking strategy",
            "prompts and LLMs",
            "business knowledge",
            "persistence and permissions",
        ),
        adapter_hooks=(
            "build sources",
            "build knowledge units",
            "build retrieval evidence",
            "map project issues/conflicts",
            "map human-review signal",
        ),
        risks=(
            "Candidate only: not a RAG platform, knowledge base platform, or search engine.",
            "The scaffold must not generate chunking, embedding, ranking, prompts, or persistence.",
        ),
        can_scaffold_adapter=True,
    ),
    "runtime-config": AdoptionProfile(
        atlas_owns=("reference boundary for runtime configuration comparison",),
        project_owns=("environment loading", "secrets", "deployment configuration", "runtime mutation policy"),
        adapter_hooks=(),
        risks=("Candidate only. No public stable runtime package is promised.",),
    ),
    "file-lifecycle": AdoptionProfile(
        atlas_owns=("reference boundary for file lifecycle semantics",),
        project_owns=("upload handling", "storage", "retention", "cleanup", "permissions"),
        adapter_hooks=(),
        risks=("Candidate only. Use as reference, not a forced dependency.",),
    ),
    "operation-outcome": AdoptionProfile(
        atlas_owns=("semantic vocabulary only",),
        project_owns=("DTOs", "workflow state", "persistence", "business outcome rules"),
        adapter_hooks=(),
        risks=("Semantic reference only. Do not generate executable adapters.",),
    ),
    "cbi-001-data-model-evolution-historical-compatibility": AdoptionProfile(
        atlas_owns=("Candidate Inbox note only",),
        project_owns=("schema migration", "historical compatibility", "data repair", "deployment rollout"),
        adapter_hooks=(),
        risks=("Inbox only. It is not a Candidate and must not be called as an Atlas capability.",),
    ),
}


def get_profile(capability_id: str) -> AdoptionProfile:
    return PROFILES.get(
        capability_id,
        AdoptionProfile(
            atlas_owns=("Catalog facts only.",),
            project_owns=("Project-specific implementation.",),
            adapter_hooks=(),
            risks=("No adoption profile is defined for this capability.",),
        ),
    )
