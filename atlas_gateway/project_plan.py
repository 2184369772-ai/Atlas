from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .adoption_profiles import get_profile
from .catalog import list_capabilities
from .inspector import inspect_project


def build_project_plan(project_path: str | Path) -> dict[str, Any]:
    inspection = inspect_project(project_path)
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
        return {
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

    recommendations = []
    for finding in inspection["findings"]:
        profile = get_profile(finding["capability_id"])
        recommendations.append(
            {
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
            }
        )

    return {
        "project_path": inspection["project_path"],
        "overall_recommendation": inspection["overall_recommendation"],
        "reason": "Project plan is derived from Gateway inspect and the capability catalog only. It does not call an LLM or infer business rules.",
        "recommended_capabilities": recommendations,
        "forbidden_capabilities": forbidden,
        "next_steps": [
            "Review each Candidate maturity before adding a dependency.",
            "Use adapter init only when the task explicitly requires Atlas adoption.",
            "Keep business rules, prompts, persistence, permissions, and production writes in the project.",
        ],
    }


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
