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
            "Controlled reuse: use the public package API only with a project-owned adapter and persistence boundary.",
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
            "Controlled reuse requires a project-side provider adapter and caller-owned prompt / model strategy.",
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
            "Controlled reuse requires project-owned parser, retrieval, vector DB, prompt, persistence, and permission boundaries.",
            "The scaffold must not generate chunking, embedding, ranking, prompts, or persistence.",
        ),
        can_scaffold_adapter=True,
    ),
    "traceability-audit": AdoptionProfile(
        atlas_owns=("controlled trace-chain source, actor, event, change, reference, relation, and comparison semantics",),
        project_owns=("log storage", "permissions", "business audit content", "workflow", "compliance retention", "query platform"),
        adapter_hooks=(),
        risks=("Controlled reuse still requires project-side event/source mapping and must not replace logs, storage, workflow, RBAC, or compliance retention.",),
    ),
    "report-export-semantics": AdoptionProfile(
        atlas_owns=("controlled report/export source, dimension, metric-role, snapshot, issue, projection, and source-trace semantics",),
        project_owns=("metric formulas", "business definitions", "SQL/ORM", "BI tooling", "permissions", "pages", "Excel templates and styling"),
        adapter_hooks=(),
        risks=("Controlled reuse still requires project-side report/export mapping and must not replace formulas, queries, BI, permissions, pages, or Excel styling.",),
    ),
    "notification-attention-routing": AdoptionProfile(
        atlas_owns=("controlled event-triggered attention, target, level, reason, timing, acknowledgement, resolution, dismissal, escalation, repeated-notice, source-reference, and comparison semantics",),
        project_owns=("delivery channels", "message templates", "users and organization hierarchy", "workflow", "permissions", "scheduling", "storage", "business escalation rules"),
        adapter_hooks=(),
        risks=("Controlled reuse still requires project-side attention mapping and must not replace delivery, workflow, scheduling, permissions, message storage, or business escalation rules.",),
    ),
    "runtime-config": AdoptionProfile(
        atlas_owns=("controlled effective-configuration resolution and comparison semantics",),
        project_owns=("environment loading", "secrets", "deployment configuration", "runtime mutation policy"),
        adapter_hooks=(),
        risks=("Controlled reuse requires a project-side framework adapter; do not use it as a Config Center or secret manager.",),
    ),
    "file-lifecycle": AdoptionProfile(
        atlas_owns=("controlled file identity, lifecycle state, retention, issue, transition, and comparison semantics",),
        project_owns=("upload handling", "storage", "retention", "cleanup", "permissions"),
        adapter_hooks=(),
        risks=("Controlled reuse still requires project-side storage, permission, ImportBatch, transaction, and business version boundaries.",),
    ),
    "operation-outcome": AdoptionProfile(
        atlas_owns=("controlled operation-result vocabulary and comparison semantics",),
        project_owns=("DTOs", "workflow state", "persistence", "business outcome rules"),
        adapter_hooks=(),
        risks=("Controlled reuse still requires project-side result mapping; do not replace API envelopes, workflow, audit, or business state machines.",),
    ),
    "ui-quality-interaction-reliability": AdoptionProfile(
        atlas_owns=(
            "UI issue taxonomy",
            "severity, location, evidence, and suggested-fix shape",
            "basic static review for accessibility labels, form labels, state feedback, overflow, and action protection",
        ),
        project_owns=(
            "brand style",
            "visual taste",
            "business copy",
            "business flow",
            "special page layout",
            "manual design judgement",
        ),
        adapter_hooks=(),
        risks=(
            "Candidate only: use as a review aid, not a design system or automatic UI fixer.",
            "Visual quality recommendations require human judgement and project context.",
        ),
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
