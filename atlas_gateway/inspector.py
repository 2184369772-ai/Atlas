from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .catalog import get_capability


SKIP_DIRS = {
    ".codex_tmp",
    ".git",
    ".idea",
    ".mypy_cache",
    ".next",
    ".npm-cache",
    ".parcel-cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".turbo",
    ".venv",
    "__pycache__",
    "coverage",
    "build",
    "cache",
    "collectstatic",
    "generated",
    "out",
    "dist",
    "target",
    "node_modules",
    "review",
    "site-packages",
    "staticfiles",
    "var",
    "vendor",
}
MAX_SCAN_FILES = 2_500
MAX_SCAN_SECONDS = 5.0
TEXT_EXTENSIONS = {
    ".cfg",
    ".csv",
    ".css",
    ".env",
    ".html",
    ".ini",
    ".java",
    ".js",
    ".json",
    ".jsx",
    ".kt",
    ".md",
    ".properties",
    ".py",
    ".rb",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".xml",
    ".vue",
    ".yaml",
    ".yml",
}


@dataclass(slots=True)
class ProjectSignal:
    capability_id: str
    detected_signal: str
    reason: str
    confidence: str


def inspect_project(project_path: str | Path, *, max_scan_seconds: float | None = None) -> dict[str, Any]:
    root = Path(project_path).resolve()
    signals = detect_project_signals(root, max_scan_seconds=max_scan_seconds)
    if not signals:
        return {
            "project_path": str(root),
            "overall_recommendation": "NO_ATLAS_REUSE",
            "reason": "No conservative Atlas reuse signal was detected in the scanned project.",
            "findings": [],
        }

    findings = []
    for signal in signals:
        try:
            capability = get_capability(signal.capability_id)
        except KeyError:
            # Public distributions may intentionally omit non-runtime internal entries
            # such as Candidate Inbox records from the exposed capability catalog.
            continue
        findings.append(
            {
                "capability": capability["name"],
                "capability_id": capability["id"],
                "detected_signal": signal.detected_signal,
                "atlas_maturity": capability["governance_status"],
                "recommendation": capability["recommendation"],
                "reason": signal.reason,
                "confidence": signal.confidence,
            }
        )

    if not findings:
        return {
            "project_path": str(root),
            "overall_recommendation": "NO_ATLAS_REUSE",
            "reason": "No public Atlas capability matched the detected project signals.",
            "findings": [],
        }

    return {
        "project_path": str(root),
        "overall_recommendation": summarize_overall_recommendation(findings),
        "reason": "Atlas findings are conservative hints only. They do not upgrade Candidate maturity.",
        "findings": findings,
    }


def summarize_overall_recommendation(findings: list[dict[str, Any]]) -> str:
    priorities = {
        "CONTROLLED_REUSE": 4,
        "REFERENCE_ONLY": 3,
        "SEMANTIC_REFERENCE": 2,
        "INBOX_ONLY": 1,
    }
    return max(findings, key=lambda item: priorities[item["recommendation"]])["recommendation"]


def detect_project_signals(root: Path, *, max_scan_seconds: float | None = None) -> list[ProjectSignal]:
    files = list(iter_project_files(root, max_scan_seconds=max_scan_seconds))
    signals: list[ProjectSignal] = []

    if has_tabular_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="tabular-core",
                detected_signal="CSV/XLSX files or tabular reader code paths detected.",
                reason="The project appears to ingest tabular files. Atlas currently has its narrowest and most validated reuse path here.",
                confidence="MEDIUM",
            )
        )
    if has_runtime_config_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="runtime-config",
                detected_signal="Runtime configuration files or environment-resolution patterns detected.",
                reason="Runtime Config is controlled-reuse effective-config code. Use it for config semantics and comparison; keep framework structure, deployment, and secret management in the project adapter.",
                confidence="LOW",
            )
        )
    if has_enterprise_intake_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="enterprise-intake",
                detected_signal="Import preview, row decision, duplicate handling, or import issue patterns detected.",
                reason="Enterprise Intake is controlled-reuse middle-layer runtime code between Tabular Core and project-side writes. Reuse still requires a project adapter and caller-owned persistence boundary.",
                confidence="LOW",
            )
        )
    if has_ai_execution_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="ai-execution",
                detected_signal="AI provider invocation, timeout, structured result, fallback, or escalation patterns detected.",
                reason="AI Execution is controlled-reuse execution-result code around project-owned AI behavior. Reuse still requires a provider adapter and project-owned prompts, model strategy, persistence, and human workflow.",
                confidence="LOW",
            )
        )
    if has_business_rule_modeling_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="business-rule-modeling",
                detected_signal="Business constraints, warning/blocking decisions, responsibility boundaries, or formal-fact protection patterns detected.",
                reason="Business Rule Modeling is a reference-level rule-structure capability. Reuse still requires project-owned roles, fields, workflow, RBAC, persistence, and business decisions.",
                confidence="LOW",
            )
        )
    if has_knowledge_intake_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="knowledge-intake",
                detected_signal="Knowledge source, version, citation, retrieval evidence, or human-review patterns detected.",
                reason="Knowledge Intake is controlled-reuse source/provenance/evidence code around project-owned parsers, retrieval, vector stores, prompts, and persistence.",
                confidence="LOW",
            )
        )
    if has_file_lifecycle_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="file-lifecycle",
                detected_signal="Upload/temp/archive/retention style file-handling patterns detected.",
                reason="File Lifecycle is controlled-reuse file identity and lifecycle code. Upload, storage, permissions, ImportBatch, database transactions, and business rules stay project-owned.",
                confidence="LOW",
            )
        )
    if has_operation_outcome_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="operation-outcome",
                detected_signal="Structured action-result semantics detected.",
                reason="Operation Outcome is controlled-reuse result semantics code. Reuse still requires project-side mapping and must not replace API envelopes, workflow, approval, audit, or business state machines.",
                confidence="LOW",
            )
        )
    if has_ui_quality_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="ui-quality-interaction-reliability",
                detected_signal="Frontend UI files or interaction feedback patterns detected.",
                reason="UI Quality is a reference-level review capability for basic page and interaction reliability issues. Project teams still own brand, copy, product taste, and business-specific layout.",
                confidence="LOW",
            )
        )
    if has_cbi001_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="cbi-001-data-model-evolution-historical-compatibility",
                detected_signal="Migration/schema compatibility clues detected.",
                reason="CBI-001 remains Candidate Inbox only. The Gateway must not present it as an existing Atlas capability.",
                confidence="LOW",
            )
        )

    return signals


def iter_project_files(root: Path, *, max_scan_files: int | None = None, max_scan_seconds: float | None = None) -> list[Path]:
    if root.is_file():
        return [root]

    collected: list[Path] = []
    deadline = time.monotonic() + (MAX_SCAN_SECONDS if max_scan_seconds is None else max_scan_seconds)
    scan_limit = MAX_SCAN_FILES if max_scan_files is None else max_scan_files
    for current_root, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname.lower() not in SKIP_DIRS and not is_generated_dir_name(dirname)
        ]
        current = Path(current_root)
        for filename in filenames:
            if len(collected) >= scan_limit or time.monotonic() >= deadline:
                return collected
            path = current / filename
            if path.name.lower() in SKIP_DIRS or is_generated_dir_name(path.name):
                continue
            collected.append(path)
    return collected


def is_generated_dir_name(name: str) -> bool:
    lowered = name.lower()
    return (
        lowered.endswith(".egg-info")
        or lowered.endswith(".dist-info")
        or lowered in {"tmp", "temp", ".cache"}
        or "cache" in lowered
    )


def has_tabular_signal(files: list[Path]) -> bool:
    for path in files:
        if path.suffix.lower() in {".csv", ".xlsx", ".xls"}:
            return True
        content = read_text_if_supported(path)
        if content and any(token in content for token in ("read_excel", "read_csv", "openpyxl", "csv.DictReader")):
            return True
    return False


def has_runtime_config_signal(files: list[Path]) -> bool:
    for path in files:
        name = path.name.lower()
        if name.startswith(".env") or name in {"application.yml", "application.yaml", "application.properties", "settings.toml"}:
            return True
        content = read_text_if_supported(path)
        if content and any(token in content for token in ("os.environ", "getenv(", "process.env", "SPRING_APPLICATION_JSON")):
            return True
    return False


def has_enterprise_intake_signal(files: list[Path]) -> bool:
    keywords = (
        "importbatch",
        "import_issue",
        "importissue",
        "source_trace",
        "sourcetrace",
        "preview",
        "idempotent",
        "duplicate",
        "skip",
        "review_required",
    )
    for path in files:
        lower_name = path.name.lower()
        if "import" in lower_name and any(token in lower_name for token in ("batch", "issue", "preview", "trace")):
            return True
        content = read_text_if_supported(path)
        if content:
            lowered = content.lower()
            if sum(1 for token in keywords if token in lowered) >= 2:
                return True
    return False


def has_ai_execution_signal(files: list[Path]) -> bool:
    keywords = (
        "chat/completions",
        "response_format",
        "model_api_key",
        "ai_api_key",
        "model_unavailable",
        "safe-fallback",
        "manual_required",
        "escalation_reasons",
        "confidence",
    )
    for path in files:
        lower_name = path.name.lower()
        if lower_name in {"model_provider.py", "ai_service.py", "ai_.py"}:
            return True
        content = read_text_if_supported(path)
        if content:
            lowered = content.lower()
            if sum(1 for token in keywords if token in lowered) >= 2:
                return True
    return False


def has_business_rule_modeling_signal(files: list[Path]) -> bool:
    keywords = (
        "permissiondenied",
        "validationerror",
        "can_manage",
        "canmanage",
        "can_view",
        "canview",
        "permission",
        "access",
        "cannot edit",
        "review_required",
        "warning",
        "blocking",
        "proxy",
        "formal",
        "confirmed",
        "must not",
        "requires_trace",
    )
    for path in files:
        lower_name = path.name.lower()
        if any(token in lower_name for token in ("business_loop", "rules", "policy", "validation")):
            return True
        content = read_text_if_supported(path)
        if content:
            lowered = content.lower()
            if sum(1 for token in keywords if token in lowered) >= 3:
                return True
    return False


def has_knowledge_intake_signal(files: list[Path]) -> bool:
    keywords = (
        "knowledge_documents",
        "knowledge_versions",
        "knowledge_chunks",
        "source_ref",
        "source_quality",
        "citation",
        "citations",
        "retrieval",
        "evidence_conflict",
        "missing_key_evidence",
        "human_review",
    )
    for path in files:
        lower_name = path.name.lower()
        if "knowledge" in lower_name and any(token in lower_name for token in ("source", "chunk", "retrieval", "citation")):
            return True
        content = read_text_if_supported(path)
        if content:
            lowered = content.lower()
            if sum(1 for token in keywords if token in lowered) >= 3:
                return True
    return False


def has_file_lifecycle_signal(files: list[Path]) -> bool:
    keywords = ("upload", "archive", "retention", "cleanup", "tmp", "temp")
    for path in files:
        lower_name = path.name.lower()
        if any(keyword in lower_name for keyword in keywords):
            return True
        content = read_text_if_supported(path)
        if content and any(token in content for token in ("retention", "archive", "temporary file", "cleanup")):
            return True
    return False


def has_operation_outcome_signal(files: list[Path]) -> bool:
    for path in files:
        content = read_text_if_supported(path)
        if content and "review_required" in content and "warnings" in content and "errors" in content:
            return True
    return False


def has_ui_quality_signal(files: list[Path]) -> bool:
    ui_suffixes = {".css", ".html", ".jsx", ".tsx", ".vue"}
    frontend_markers = (
        "react",
        "vue",
        "vite",
        "next",
        "nuxt",
        "svelte",
        "angular",
        "@vitejs/",
        "tailwind",
        "element-plus",
    )
    ui_tokens = (
        "<button",
        "<form",
        "<input",
        "<template",
        "onclick",
        "@click",
        "className=",
        "aria-",
        "disabled",
        "loading",
        "empty-state",
        "modal",
    )
    layout_tokens = ("@media", "overflow", "height: 100vh", "width:", "display: flex", "display: grid")
    has_frontend_marker = False
    ui_evidence_count = 0

    for path in files:
        lower_name = path.name.lower()
        suffix = path.suffix.lower()
        content = read_text_if_supported(path)
        lowered = content.lower() if content else ""

        if lower_name in {"package.json", "vite.config.ts", "vite.config.js", "next.config.js", "nuxt.config.ts"}:
            if any(marker in lowered for marker in frontend_markers):
                has_frontend_marker = True

        if suffix in ui_suffixes and lowered:
            token_hits = sum(1 for token in ui_tokens if token in lowered)
            layout_hits = sum(1 for token in layout_tokens if token in lowered)
            if suffix in {".jsx", ".tsx", ".vue", ".html"} and token_hits >= 1:
                ui_evidence_count += 2
            elif suffix == ".css" and layout_hits >= 2:
                ui_evidence_count += 1
            elif token_hits + layout_hits >= 2:
                ui_evidence_count += 1

        if "src" in {part.lower() for part in path.parts} and suffix in {".jsx", ".tsx", ".vue"} and lowered:
            if any(token in lowered for token in ui_tokens):
                has_frontend_marker = True

    return has_frontend_marker and ui_evidence_count >= 2


def has_cbi001_signal(files: list[Path]) -> bool:
    for path in files:
        lower_name = path.name.lower()
        if "migration" in lower_name or "schema" in lower_name:
            return True
        content = read_text_if_supported(path)
        if content and any(token in content for token in ("alembic", "django.db.migrations", "schema evolution", "backward compatibility")):
            return True
    return False


@lru_cache(maxsize=5_000)
def read_text_if_supported(path: Path) -> str | None:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return None
    except OSError:
        return None
    return text[:200_000]


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
