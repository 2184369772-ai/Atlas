from __future__ import annotations

import json
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Literal, get_args, get_origin


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SOURCE_PATHS = (
    REPO_ROOT / "packages" / "enterprise-intake" / "src",
    REPO_ROOT / "packages" / "operation-outcome" / "src",
)


JAVA_SUPPORTED_CAPABILITIES = {"enterprise-intake", "operation-outcome"}


def ensure_package_paths() -> None:
    for path in PACKAGE_SOURCE_PATHS:
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def contract_for(capability_id: str) -> dict[str, Any]:
    """Build a machine-readable contract from the Python contract source."""
    ensure_package_paths()
    if capability_id == "enterprise-intake":
        from atlas_enterprise_intake import models as models_module

        return {
            "capability_id": capability_id,
            "language": "neutral",
            "source": "atlas_enterprise_intake.models",
            "enums": {
                "IntakeDecision": list(get_args(models_module.Decision)),
                "CommitReadiness": list(get_args(models_module.CommitReadiness)),
            },
            "models": {
                name: dataclass_shape(getattr(models_module, name))
                for name in (
                    "IntakeIssue",
                    "IntakeRowInput",
                    "IntakeRowDecision",
                    "IntakeRowResult",
                    "IntakeSummary",
                    "IntakePreview",
                )
            },
            "golden_vectors": enterprise_intake_golden_vectors(),
        }
    if capability_id == "operation-outcome":
        from atlas_operation_outcome import models as models_module

        return {
            "capability_id": capability_id,
            "language": "neutral",
            "source": "atlas_operation_outcome.models",
            "enums": {
                "OutcomeStatus": list(get_args(models_module.OutcomeStatus)),
                "IssueSeverity": list(get_args(models_module.IssueSeverity)),
                "Confidence": list(get_args(models_module.Confidence)),
                "RiskLevel": list(get_args(models_module.RiskLevel)),
            },
            "models": {
                name: dataclass_shape(getattr(models_module, name))
                for name in ("EvidenceReference", "OutcomeIssue", "OperationOutcome")
            },
            "golden_vectors": operation_outcome_golden_vectors(),
        }
    raise ValueError(f"{capability_id} has no Java cross-language contract in v0.1.")


def dataclass_shape(model: type[Any]) -> list[dict[str, str]]:
    if not is_dataclass(model):
        raise TypeError(f"{model!r} is not a dataclass contract model.")
    return [{"name": item.name, "type": str(item.type)} for item in fields(model)]


def enterprise_intake_golden_vectors() -> list[dict[str, Any]]:
    return [
        {
            "name": "mixed_preview_requires_review",
            "row_decisions": ["ACCEPT", "REVIEW", "REJECT"],
            "issue_severities": ["WARNING"],
            "expected_summary": {
                "total_rows": 3,
                "accepted_rows": 1,
                "review_rows": 1,
                "rejected_rows": 1,
                "partial_completion": True,
                "commit_readiness": "REVIEW_REQUIRED",
            },
        },
        {
            "name": "all_rejected_blocks_commit",
            "row_decisions": ["REJECT", "REJECT"],
            "issue_severities": ["ERROR"],
            "expected_summary": {
                "total_rows": 2,
                "rejected_rows": 2,
                "partial_completion": False,
                "commit_readiness": "BLOCKED",
            },
        },
    ]


def operation_outcome_golden_vectors() -> list[dict[str, Any]]:
    return [
        {
            "name": "review_required_implies_human_attention",
            "input": {"status": "REVIEW_REQUIRED", "issue_severities": ["WARNING"]},
            "expected": {"human_attention_required": True, "has_errors": False},
        },
        {
            "name": "error_issue_implies_human_attention",
            "input": {"status": "PARTIAL", "issue_severities": ["ERROR"]},
            "expected": {"human_attention_required": True, "has_errors": True},
        },
        {
            "name": "unknown_confidence_normalizes",
            "input": {"status": "SUCCESS", "confidence": "unexpected", "risk_level": "odd"},
            "expected": {"confidence": "UNKNOWN", "risk_level": "UNKNOWN"},
        },
    ]


def to_json_contract(capability_id: str) -> str:
    return json.dumps(contract_for(capability_id), ensure_ascii=False, indent=2)

