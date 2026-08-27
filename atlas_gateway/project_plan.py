from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from .adoption_profiles import get_profile
from .catalog import list_capabilities
from .cross_language_bridge import JAVA_SUPPORTED_CAPABILITIES
from .inspector import SKIP_DIRS, inspect_project, is_generated_dir_name
from .task_routing import PROJECT_RELEVANT, summarize_task_decisions, route_task_for_capability


UI_CLOSEOUT_CAPABILITY = "ui-quality-interaction-reliability"
UI_CLOSEOUT_WORKFLOW = [
    "Function complete",
    "Run atlas ui review <project-path>",
    "Run atlas ui fix <project-path> --dry-run",
    "Apply safe items only after explicit authorization",
    "Review visual recommendations",
    "Let Codex optimize project-owned UI where appropriate",
    "Human final aesthetic confirmation",
]
UI_CLOSEOUT_COMMANDS = [
    "atlas ui review <project-path>",
    "atlas ui fix <project-path> --dry-run",
]
UI_VISUAL_RECOMMENDATIONS = [
    "Use review items with recommendation_class=VISUAL_RECOMMENDATION as Codex implementation prompts.",
    "Keep BUSINESS_JUDGMENT items for human/product-owner decision.",
    "Do not route visual recommendations into atlas ui fix --safe.",
]
JAVA_SIGNAL_FILES = {"pom.xml", "build.gradle", "build.gradle.kts", "settings.gradle", "settings.gradle.kts"}
JAVA_SOURCE_SUFFIXES = {".java"}


def build_project_plan(project_path: str | Path, *, task: str | None = None) -> dict[str, Any]:
    task_description = task.strip() if task else ""
    inspection = inspect_project(project_path, max_scan_seconds=2.0 if task_description else None)
    project_languages = detect_project_languages(project_path)
    forbidden = []
    for capability in list_capabilities():
        if capability["recommendation"] in {"SEMANTIC_REFERENCE", "INBOX_ONLY"}:
            forbidden.append(
                {
                    "capability_id": capability["id"],
                    "name": capability["name"],
                    "recommendation": capability["recommendation"],
                    "reason": capability["notes"],
                }
            )

    if inspection["overall_recommendation"] == "NO_ATLAS_REUSE":
        payload = {
            "project_path": inspection["project_path"],
            "overall_recommendation": "NO_ATLAS_REUSE",
            "reason": inspection["reason"],
            "recommended_capabilities": [],
            "forbidden_capabilities": forbidden,
            "next_steps": [
                "Continue normal project development without adding Atlas-specific adapter layers.",
                "Re-run project inspect/plan only if the project gains relevant CSV/XLSX, intake, AI execution, or knowledge intake signals.",
            ],
        }
        if task_description:
            payload["task"] = task_description
            payload["project_overall_recommendation"] = inspection["overall_recommendation"]
            payload["task_overall_decision"] = "NO_ATLAS_REUSE"
            payload["project_relevant_capabilities"] = []
        return payload

    recommendations = []
    project_relevant = []
    task_decisions = []
    for finding in inspection["findings"]:
        profile = get_profile(finding["capability_id"])
        task_decision = None
        item = {
            "capability": finding["capability"],
            "capability_id": finding["capability_id"],
            "detected_signal": finding["detected_signal"],
            "maturity": finding["atlas_maturity"],
            "recommendation": finding["recommendation"],
            "confidence": finding["confidence"],
            "atlas_owns": list(profile.atlas_owns),
            "project_must_own": list(profile.project_owns),
            "adapter_hooks": list(profile.adapter_hooks),
            "risks_and_boundaries": list(profile.risks),
            "adapter_scaffold_supported": profile.can_scaffold_adapter,
            "cross_language_bridge_supported": {},
        }
        if task_description:
            task_decision = route_task_for_capability(
                finding["capability_id"],
                finding["recommendation"],
                task_description,
                is_java_project="java" in project_languages,
            )
            item["task_decision"] = task_decision.decision
            item["task_reason"] = task_decision.reason
            task_decisions.append(task_decision.decision)
        if "java" in project_languages and finding["capability_id"] in JAVA_SUPPORTED_CAPABILITIES:
            item["cross_language_bridge_supported"]["java"] = True
            item.setdefault("recommended_commands", [])
            item["recommended_commands"].append(f"atlas adapter init {finding['capability_id']} --target <project-path> --language java")
            item["risks_and_boundaries"].append(
                "Java bridge generates local project-owned contract/scaffold code; runtime must not depend on Python, Atlas CLI, or Atlas package imports."
            )
        if finding["capability_id"] == UI_CLOSEOUT_CAPABILITY:
            item["workflow_trigger"] = "Only when the project is in function-complete, phase acceptance, or UI closeout work."
            item["recommended_commands"] = list(UI_CLOSEOUT_COMMANDS)
            item["ui_closeout_workflow"] = list(UI_CLOSEOUT_WORKFLOW)
            item["visual_recommendations"] = list(UI_VISUAL_RECOMMENDATIONS)
        if task_description and task_decision and task_decision.decision == PROJECT_RELEVANT:
            project_relevant.append(item)
        else:
            recommendations.append(item)

    overall = inspection["overall_recommendation"]
    reason = "Project plan is derived from Gateway inspect and the capability catalog only. It does not call an LLM or infer business rules."
    if task_description:
        overall = summarize_task_decisions(task_decisions)
        if overall == PROJECT_RELEVANT:
            reason = "Atlas capabilities are project-relevant, but the current task does not justify direct reuse or reference adoption."
        elif overall == "NO_ATLAS_REUSE":
            reason = "The current task has no Atlas reuse fit."
        else:
            reason = "Task-aware plan is derived from Gateway inspect, task text, capability maturity, boundaries, and adoption requirements only."

    payload = {
        "project_path": inspection["project_path"],
        "overall_recommendation": overall,
        "reason": reason,
        "recommended_capabilities": recommendations,
        "forbidden_capabilities": forbidden,
        "next_steps": [
            "Review each Candidate maturity before adding a dependency.",
            "Use adapter init only when the task explicitly requires Atlas adoption.",
            "Keep business rules, prompts, persistence, permissions, and production writes in the project.",
            "For UI projects, run UI closeout only at function-complete, phase acceptance, or UI closeout stage; default ui fix to --dry-run.",
        ],
    }
    if task_description:
        payload["task"] = task_description
        payload["project_overall_recommendation"] = inspection["overall_recommendation"]
        payload["task_overall_decision"] = overall
        payload["project_relevant_capabilities"] = project_relevant
    return payload


def detect_project_languages(project_path: str | Path) -> list[str]:
    path = Path(project_path)
    if path.is_file():
        return ["java"] if path.suffix in JAVA_SOURCE_SUFFIXES else []
    if not path.exists():
        return []
    for marker in (
        path / "pom.xml",
        path / "backend" / "pom.xml",
        path / "build.gradle",
        path / "backend" / "build.gradle",
        path / "settings.gradle",
    ):
        if marker.exists():
            return ["java"]
    java_files = 0
    deadline = time.monotonic() + 0.5
    scanned = 0
    for current_root, dirnames, filenames in os.walk(path):
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname.lower() not in SKIP_DIRS and not is_generated_dir_name(dirname)
        ]
        for filename in filenames:
            scanned += 1
            child = Path(current_root) / filename
            if child.name in JAVA_SIGNAL_FILES or child.suffix in JAVA_SOURCE_SUFFIXES:
                java_files += 1
            if scanned >= 300 or time.monotonic() >= deadline:
                return ["java"] if java_files else []
        if java_files >= 2:
            return ["java"]
    return ["java"] if java_files else []


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
