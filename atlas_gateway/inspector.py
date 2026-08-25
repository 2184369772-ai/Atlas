from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import get_capability


SKIP_DIRS = {
    ".git",
    ".idea",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
}
TEXT_EXTENSIONS = {
    ".cfg",
    ".csv",
    ".env",
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
    ".yaml",
    ".yml",
}


@dataclass(slots=True)
class ProjectSignal:
    capability_id: str
    detected_signal: str
    reason: str
    confidence: str


def inspect_project(project_path: str | Path) -> dict[str, Any]:
    root = Path(project_path).resolve()
    signals = detect_project_signals(root)
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


def detect_project_signals(root: Path) -> list[ProjectSignal]:
    files = list(iter_project_files(root))
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
                reason="Runtime Config remains a Candidate. It can guide comparison or adapter design, but should not be treated as a stable package promise.",
                confidence="LOW",
            )
        )
    if has_enterprise_intake_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="enterprise-intake",
                detected_signal="Import preview, row decision, duplicate handling, or import issue patterns detected.",
                reason="Enterprise Intake is only the middle layer between Tabular Core and project-side writes. Reuse still requires a project adapter and caller-owned persistence boundary.",
                confidence="LOW",
            )
        )
    if has_ai_execution_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="ai-execution",
                detected_signal="AI provider invocation, timeout, structured result, fallback, or escalation patterns detected.",
                reason="AI Execution is only the execution-result layer around project-owned AI behavior. Reuse still requires a provider adapter and project-owned prompts, persistence, and human workflow.",
                confidence="LOW",
            )
        )
    if has_knowledge_intake_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="knowledge-intake",
                detected_signal="Knowledge source, version, citation, retrieval evidence, or human-review patterns detected.",
                reason="Knowledge Intake is only the source/provenance/evidence semantics around project-owned parsers, retrieval, vector stores, prompts, and persistence.",
                confidence="LOW",
            )
        )
    if has_file_lifecycle_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="file-lifecycle",
                detected_signal="Upload/temp/archive/retention style file-handling patterns detected.",
                reason="File Lifecycle is a reference-level package for file identity, metadata, reference, lifecycle state, retention intent, and file-level issues. Upload, storage, permissions, ImportBatch, and business rules stay project-owned.",
                confidence="LOW",
            )
        )
    if has_operation_outcome_signal(files):
        signals.append(
            ProjectSignal(
                capability_id="operation-outcome",
                detected_signal="Structured action-result semantics detected.",
                reason="Operation Outcome is a reference-level result semantics package. Reuse still requires project-side mapping and must not replace API envelopes, workflow, approval, audit, or business state machines.",
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


def iter_project_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root]

    collected: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            collected.append(path)
    return collected


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


def has_cbi001_signal(files: list[Path]) -> bool:
    for path in files:
        lower_name = path.name.lower()
        if "migration" in lower_name or "schema" in lower_name:
            return True
        content = read_text_if_supported(path)
        if content and any(token in content for token in ("alembic", "django.db.migrations", "schema evolution", "backward compatibility")):
            return True
    return False


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
