from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adoption_profiles import get_profile
from .catalog import get_capability
from .cross_language_bridge import JAVA_SUPPORTED_CAPABILITIES, contract_for


SUPPORTED_ADAPTERS = {"enterprise-intake", "ai-execution", "knowledge-intake"}
SUPPORTED_LANGUAGES = {"python", "java"}


@dataclass(frozen=True, slots=True)
class ScaffoldFile:
    path: Path
    content: str


def init_adapter(
    capability_name: str,
    target: str | Path,
    *,
    force: bool = False,
    language: str = "python",
) -> dict[str, Any]:
    language = language.lower().strip()
    if language not in SUPPORTED_LANGUAGES:
        raise ValueError(f"Unsupported adapter scaffold language: {language}. Supported languages: python, java.")

    if capability_name.strip().upper() == "NO_ATLAS_REUSE":
        return {
            "status": "NO_ATLAS_REUSE",
            "capability_id": "NO_ATLAS_REUSE",
            "language": language,
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
    if language == "java":
        if capability_id not in JAVA_SUPPORTED_CAPABILITIES:
            raise ValueError(
                f"{capability_id} has no Java cross-language scaffold in v0.1. "
                "Supported Java capabilities: enterprise-intake, operation-outcome."
            )
    elif capability_id not in SUPPORTED_ADAPTERS:
        raise ValueError(
            f"{capability_id} has recommendation {recommendation}, but Project Adoption Kit v0.1 has no adapter scaffold template for it."
        )

    target_path = Path(target).resolve()
    files = build_java_files(capability_id, target_path) if language == "java" else build_files(capability_id, target_path)
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
        "language": language,
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


def build_java_files(capability_id: str, target: Path) -> list[ScaffoldFile]:
    contract = contract_for(capability_id)
    base = target / "atlas-adapters-java"
    source = base / "src" / "main" / "java" / "com" / "atlas" / "adoption"
    tests = base / "src" / "test" / "java" / "com" / "atlas" / "adoption"
    resources = base / "src" / "main" / "resources" / "atlas-contracts"
    docs_name = capability_id.replace("-", "_")
    files = [
        ScaffoldFile(target / "docs" / f"atlas_{docs_name}_java_boundary.md", java_boundary_doc(capability_id)),
        ScaffoldFile(resources / f"{capability_id}.json", json.dumps(contract, ensure_ascii=False, indent=2) + "\n"),
    ]
    if capability_id == "enterprise-intake":
        files.extend(enterprise_intake_java_files(source, tests, contract))
    elif capability_id == "operation-outcome":
        files.extend(operation_outcome_java_files(source, tests, contract))
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


def java_boundary_doc(capability_id: str) -> str:
    profile = get_profile(capability_id)
    lines = [
        f"# Atlas {capability_id} Java Cross-language Adapter Boundary",
        "",
        "This scaffold is generated from Atlas Python contract metadata for Java projects that cannot directly depend on the Python runtime.",
        "",
        "Generated Java code is project-owned after creation. It carries Atlas vocabulary and semantics only; it does not call Atlas CLI, does not import Python, and does not implement project business rules.",
        "",
        "## Atlas owns",
        "",
    ]
    lines.extend(f"- {item}" for item in profile.atlas_owns)
    lines.extend(["", "## Java project must own", ""])
    lines.extend(f"- {item}" for item in profile.project_owns)
    if capability_id == "enterprise-intake":
        lines.extend(
            [
                "- Excel parsing",
                "- field mapping",
                "- business validation",
                "- duplicate policy",
                "- Spring services, persistence, transactions, and database writes",
            ]
        )
    elif capability_id == "operation-outcome":
        lines.extend(
            [
                "- Spring DTO/API envelope mapping",
                "- workflow state transitions",
                "- persistence and audit records",
                "- business outcome rules",
            ]
        )
    lines.extend(["", "## Drift guard", ""])
    lines.append("Regenerate this scaffold from Atlas Gateway when Atlas contract metadata changes; do not hand-maintain a separate Java contract.")
    lines.append("")
    return "\n".join(lines)


def java_enum(package_name: str, enum_name: str, values: list[str]) -> str:
    body = ",\n    ".join(values)
    return f"""package {package_name};

public enum {enum_name} {{
    {body}
}}
"""


def enterprise_intake_java_files(source: Path, tests: Path, contract: dict[str, Any]) -> list[ScaffoldFile]:
    package_dir = source / "enterpriseintake"
    test_dir = tests / "enterpriseintake"
    enums = contract["enums"]
    return [
        ScaffoldFile(package_dir / "IntakeDecision.java", java_enum("com.atlas.adoption.enterpriseintake", "IntakeDecision", enums["IntakeDecision"])),
        ScaffoldFile(package_dir / "CommitReadiness.java", java_enum("com.atlas.adoption.enterpriseintake", "CommitReadiness", enums["CommitReadiness"])),
        ScaffoldFile(package_dir / "IntakeIssue.java", enterprise_intake_issue_java()),
        ScaffoldFile(package_dir / "IntakeRowInput.java", enterprise_intake_row_input_java()),
        ScaffoldFile(package_dir / "IntakeRowDecision.java", enterprise_intake_row_decision_java()),
        ScaffoldFile(package_dir / "IntakeRowResult.java", enterprise_intake_row_result_java()),
        ScaffoldFile(package_dir / "IntakeSummary.java", enterprise_intake_summary_java()),
        ScaffoldFile(package_dir / "IntakePreview.java", enterprise_intake_preview_java()),
        ScaffoldFile(package_dir / "EnterpriseIntakeAdapter.java", enterprise_intake_adapter_interface_java()),
        ScaffoldFile(package_dir / "ProjectEnterpriseIntakeAdapter.java", project_enterprise_intake_adapter_java()),
        ScaffoldFile(test_dir / "EnterpriseIntakeScaffoldSmoke.java", enterprise_intake_smoke_java()),
    ]


def operation_outcome_java_files(source: Path, tests: Path, contract: dict[str, Any]) -> list[ScaffoldFile]:
    package_dir = source / "operationoutcome"
    test_dir = tests / "operationoutcome"
    enums = contract["enums"]
    return [
        ScaffoldFile(package_dir / "OutcomeStatus.java", java_enum("com.atlas.adoption.operationoutcome", "OutcomeStatus", enums["OutcomeStatus"])),
        ScaffoldFile(package_dir / "IssueSeverity.java", java_enum("com.atlas.adoption.operationoutcome", "IssueSeverity", enums["IssueSeverity"])),
        ScaffoldFile(package_dir / "Confidence.java", java_enum("com.atlas.adoption.operationoutcome", "Confidence", enums["Confidence"])),
        ScaffoldFile(package_dir / "RiskLevel.java", java_enum("com.atlas.adoption.operationoutcome", "RiskLevel", enums["RiskLevel"])),
        ScaffoldFile(package_dir / "EvidenceReference.java", evidence_reference_java()),
        ScaffoldFile(package_dir / "OutcomeIssue.java", outcome_issue_java()),
        ScaffoldFile(package_dir / "OperationOutcome.java", operation_outcome_java()),
        ScaffoldFile(package_dir / "ProjectOperationOutcomeMapper.java", project_operation_outcome_mapper_java()),
        ScaffoldFile(test_dir / "OperationOutcomeScaffoldSmoke.java", operation_outcome_smoke_java()),
    ]


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


def enterprise_intake_issue_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

public final class IntakeIssue {
    public final String code;
    public final String severity;
    public final String scope;
    public final String message;
    public final Integer row;
    public final String field;
    public final Integer column;
    public final String sourceColumn;
    public final String canonicalCode;
    public final Object originalValue;

    public IntakeIssue(String code, String severity, String scope, String message) {
        this(code, severity, scope, message, null, null, null, null, null, null);
    }

    public IntakeIssue(
            String code,
            String severity,
            String scope,
            String message,
            Integer row,
            String field,
            Integer column,
            String sourceColumn,
            String canonicalCode,
            Object originalValue) {
        this.code = code;
        this.severity = severity;
        this.scope = scope;
        this.message = message;
        this.row = row;
        this.field = field;
        this.column = column;
        this.sourceColumn = sourceColumn;
        this.canonicalCode = canonicalCode;
        this.originalValue = originalValue;
    }
}
"""


def enterprise_intake_row_input_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.List;
import java.util.Map;

public final class IntakeRowInput {
    public final int rowIndex;
    public final int sourceRowIndex;
    public final List<Object> rawValues;
    public final Map<String, Object> valuesByHeader;
    public final Map<String, Object> mappedValues;

    public IntakeRowInput(
            int rowIndex,
            int sourceRowIndex,
            List<Object> rawValues,
            Map<String, Object> valuesByHeader,
            Map<String, Object> mappedValues) {
        this.rowIndex = rowIndex;
        this.sourceRowIndex = sourceRowIndex;
        this.rawValues = List.copyOf(rawValues);
        this.valuesByHeader = Map.copyOf(valuesByHeader);
        this.mappedValues = Map.copyOf(mappedValues);
    }
}
"""


def enterprise_intake_row_decision_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.List;
import java.util.Map;

public final class IntakeRowDecision {
    public final IntakeDecision decision;
    public final List<IntakeIssue> issues;
    public final Map<String, Object> normalizedValues;
    public final Map<String, Object> trace;

    public IntakeRowDecision(IntakeDecision decision) {
        this(decision, List.of(), Map.of(), Map.of());
    }

    public IntakeRowDecision(
            IntakeDecision decision,
            List<IntakeIssue> issues,
            Map<String, Object> normalizedValues,
            Map<String, Object> trace) {
        this.decision = decision;
        this.issues = List.copyOf(issues);
        this.normalizedValues = Map.copyOf(normalizedValues);
        this.trace = Map.copyOf(trace);
    }
}
"""


def enterprise_intake_row_result_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.List;
import java.util.Map;

public final class IntakeRowResult {
    public final int rowIndex;
    public final int sourceRowIndex;
    public final IntakeDecision decision;
    public final Map<String, Object> mappedValues;
    public final Map<String, Object> normalizedValues;
    public final List<IntakeIssue> issues;
    public final Map<String, Object> trace;

    public IntakeRowResult(
            int rowIndex,
            int sourceRowIndex,
            IntakeDecision decision,
            Map<String, Object> mappedValues,
            Map<String, Object> normalizedValues,
            List<IntakeIssue> issues,
            Map<String, Object> trace) {
        this.rowIndex = rowIndex;
        this.sourceRowIndex = sourceRowIndex;
        this.decision = decision;
        this.mappedValues = Map.copyOf(mappedValues);
        this.normalizedValues = Map.copyOf(normalizedValues);
        this.issues = List.copyOf(issues);
        this.trace = Map.copyOf(trace);
    }
}
"""


def enterprise_intake_summary_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.EnumMap;
import java.util.List;
import java.util.Map;

public final class IntakeSummary {
    public final int totalRows;
    public final int acceptedRows;
    public final int skippedRows;
    public final int rejectedRows;
    public final int reviewRows;
    public final int issueCount;
    public final int errorCount;
    public final int warningCount;
    public final boolean partialCompletion;
    public final boolean previewMode;
    public final CommitReadiness commitReadiness;

    public IntakeSummary(
            int totalRows,
            int acceptedRows,
            int skippedRows,
            int rejectedRows,
            int reviewRows,
            int issueCount,
            int errorCount,
            int warningCount,
            boolean partialCompletion,
            boolean previewMode,
            CommitReadiness commitReadiness) {
        this.totalRows = totalRows;
        this.acceptedRows = acceptedRows;
        this.skippedRows = skippedRows;
        this.rejectedRows = rejectedRows;
        this.reviewRows = reviewRows;
        this.issueCount = issueCount;
        this.errorCount = errorCount;
        this.warningCount = warningCount;
        this.partialCompletion = partialCompletion;
        this.previewMode = previewMode;
        this.commitReadiness = commitReadiness;
    }

    public static IntakeSummary fromRows(List<IntakeRowResult> rows, List<IntakeIssue> issues, boolean previewMode) {
        Map<IntakeDecision, Integer> counts = new EnumMap<>(IntakeDecision.class);
        for (IntakeRowResult row : rows) {
            counts.put(row.decision, counts.getOrDefault(row.decision, 0) + 1);
        }
        int errorCount = 0;
        int warningCount = 0;
        for (IntakeIssue issue : issues) {
            if ("ERROR".equals(issue.severity)) {
                errorCount++;
            }
            if ("WARNING".equals(issue.severity)) {
                warningCount++;
            }
        }
        int nonZeroBuckets = 0;
        for (IntakeDecision decision : IntakeDecision.values()) {
            if (counts.getOrDefault(decision, 0) > 0) {
                nonZeroBuckets++;
            }
        }
        boolean partial = nonZeroBuckets > 1
                || counts.getOrDefault(IntakeDecision.SKIP, 0) > 0
                || counts.getOrDefault(IntakeDecision.REVIEW, 0) > 0;
        return new IntakeSummary(
                rows.size(),
                counts.getOrDefault(IntakeDecision.ACCEPT, 0),
                counts.getOrDefault(IntakeDecision.SKIP, 0),
                counts.getOrDefault(IntakeDecision.REJECT, 0),
                counts.getOrDefault(IntakeDecision.REVIEW, 0),
                issues.size(),
                errorCount,
                warningCount,
                partial,
                previewMode,
                determineCommitReadiness(rows, issues));
    }

    public static CommitReadiness determineCommitReadiness(List<IntakeRowResult> rows, List<IntakeIssue> issues) {
        for (IntakeIssue issue : issues) {
            if ("ERROR".equals(issue.severity) && ("STRUCTURE".equals(issue.scope) || "SOURCE".equals(issue.scope))) {
                return CommitReadiness.BLOCKED;
            }
        }
        boolean allRejectedOrSkipped = !rows.isEmpty();
        for (IntakeRowResult row : rows) {
            if (row.decision == IntakeDecision.REVIEW) {
                return CommitReadiness.REVIEW_REQUIRED;
            }
            if (row.decision != IntakeDecision.REJECT && row.decision != IntakeDecision.SKIP) {
                allRejectedOrSkipped = false;
            }
        }
        return allRejectedOrSkipped ? CommitReadiness.BLOCKED : CommitReadiness.READY_TO_COMMIT;
    }
}
"""


def enterprise_intake_preview_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.List;

public final class IntakePreview {
    public final String sourceName;
    public final String tableName;
    public final List<IntakeRowResult> rows;
    public final List<IntakeIssue> issues;
    public final IntakeSummary summary;

    public IntakePreview(
            String sourceName,
            String tableName,
            List<IntakeRowResult> rows,
            List<IntakeIssue> issues,
            boolean previewMode) {
        this.sourceName = sourceName;
        this.tableName = tableName;
        this.rows = List.copyOf(rows);
        this.issues = List.copyOf(issues);
        this.summary = IntakeSummary.fromRows(this.rows, this.issues, previewMode);
    }
}
"""


def enterprise_intake_adapter_interface_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.Map;

public interface EnterpriseIntakeAdapter {
    Map<String, String> resolveFieldMapping();

    IntakeRowDecision evaluateRow(IntakeRowInput row);
}
"""


def project_enterprise_intake_adapter_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.List;
import java.util.Map;

public final class ProjectEnterpriseIntakeAdapter implements EnterpriseIntakeAdapter {
    @Override
    public Map<String, String> resolveFieldMapping() {
        // TODO(project): map Excel headers to project-owned fields.
        return Map.of();
    }

    @Override
    public IntakeRowDecision evaluateRow(IntakeRowInput row) {
        // TODO(project): replace REVIEW with project-owned validation and duplicate policy.
        IntakeIssue issue = new IntakeIssue(
                "PROJECT_HOOK_TODO",
                "WARNING",
                "ADAPTER",
                "Implement project-owned Enterprise Intake row evaluation before commit.",
                row.sourceRowIndex,
                null,
                null,
                null,
                null,
                null);
        return new IntakeRowDecision(
                IntakeDecision.REVIEW,
                List.of(issue),
                Map.of(),
                Map.of("adapter", "project-enterprise-intake-java"));
    }
}
"""


def enterprise_intake_smoke_java() -> str:
    return """package com.atlas.adoption.enterpriseintake;

import java.util.List;
import java.util.Map;

public final class EnterpriseIntakeScaffoldSmoke {
    public static void main(String[] args) {
        IntakeRowResult accepted = new IntakeRowResult(1, 2, IntakeDecision.ACCEPT, Map.of(), Map.of(), List.of(), Map.of());
        IntakeIssue reviewIssue = new IntakeIssue("BUSINESS_REVIEW", "WARNING", "ADAPTER", "Needs human review", 3, null, null, null, null, null);
        IntakeRowResult review = new IntakeRowResult(2, 3, IntakeDecision.REVIEW, Map.of(), Map.of(), List.of(reviewIssue), Map.of());
        IntakeIssue rejectIssue = new IntakeIssue("BUSINESS_REJECT", "ERROR", "ADAPTER", "Rejected by project validation", 4, null, null, null, null, null);
        IntakeRowResult rejected = new IntakeRowResult(3, 4, IntakeDecision.REJECT, Map.of(), Map.of(), List.of(rejectIssue), Map.of());
        IntakePreview preview = new IntakePreview("synthetic-import-preview.xlsx", "sheet1", List.of(accepted, review, rejected), List.of(reviewIssue, rejectIssue), true);

        require(preview.summary.acceptedRows == 1, "accepted row count");
        require(preview.summary.reviewRows == 1, "review row count");
        require(preview.summary.rejectedRows == 1, "rejected row count");
        require(preview.summary.partialCompletion, "partial completion");
        require(preview.summary.commitReadiness == CommitReadiness.REVIEW_REQUIRED, "commit readiness");

        ProjectEnterpriseIntakeAdapter adapter = new ProjectEnterpriseIntakeAdapter();
        IntakeRowDecision decision = adapter.evaluateRow(new IntakeRowInput(1, 2, List.of(), Map.of(), Map.of()));
        require(decision.decision == IntakeDecision.REVIEW, "adapter default decision");
    }

    private static void require(boolean condition, String label) {
        if (!condition) {
            throw new IllegalStateException(label);
        }
    }
}
"""


def evidence_reference_java() -> str:
    return """package com.atlas.adoption.operationoutcome;

import java.util.Map;

public final class EvidenceReference {
    public final String id;
    public final String source;
    public final String reference;
    public final Map<String, Object> metadata;

    public EvidenceReference(String id, String source, String reference, Map<String, Object> metadata) {
        this.id = id;
        this.source = source == null ? "" : source;
        this.reference = reference == null ? "" : reference;
        this.metadata = Map.copyOf(metadata);
    }
}
"""


def outcome_issue_java() -> str:
    return """package com.atlas.adoption.operationoutcome;

public final class OutcomeIssue {
    public final String code;
    public final IssueSeverity severity;
    public final String message;
    public final String scope;
    public final String evidenceId;

    public OutcomeIssue(String code, IssueSeverity severity, String message) {
        this(code, severity, message, "OPERATION", null);
    }

    public OutcomeIssue(String code, IssueSeverity severity, String message, String scope, String evidenceId) {
        this.code = code;
        this.severity = severity;
        this.message = message;
        this.scope = scope == null ? "OPERATION" : scope;
        this.evidenceId = evidenceId;
    }
}
"""


def operation_outcome_java() -> str:
    return """package com.atlas.adoption.operationoutcome;

import java.util.List;
import java.util.Map;

public final class OperationOutcome {
    public final OutcomeStatus status;
    public final String summary;
    public final List<OutcomeIssue> issues;
    public final List<EvidenceReference> evidence;
    public final List<String> affectedScope;
    public final List<String> remainingScope;
    public final Confidence confidence;
    public final RiskLevel riskLevel;
    public final boolean humanAttentionRequired;
    public final boolean fallbackUsed;
    public final Map<String, Object> trace;

    public OperationOutcome(
            OutcomeStatus status,
            String summary,
            List<OutcomeIssue> issues,
            List<EvidenceReference> evidence,
            List<String> affectedScope,
            List<String> remainingScope,
            Confidence confidence,
            RiskLevel riskLevel,
            Boolean humanAttentionRequired,
            boolean fallbackUsed,
            Map<String, Object> trace) {
        this.status = status;
        this.summary = summary == null ? "" : summary;
        this.issues = List.copyOf(issues);
        this.evidence = List.copyOf(evidence);
        this.affectedScope = List.copyOf(affectedScope);
        this.remainingScope = List.copyOf(remainingScope);
        this.confidence = confidence == null ? Confidence.UNKNOWN : confidence;
        this.riskLevel = riskLevel == null ? RiskLevel.UNKNOWN : riskLevel;
        this.humanAttentionRequired = humanAttentionRequired == null ? defaultHumanAttention(status, issues) : humanAttentionRequired;
        this.fallbackUsed = fallbackUsed;
        this.trace = Map.copyOf(trace);
    }

    public boolean hasErrors() {
        for (OutcomeIssue issue : issues) {
            if (issue.severity == IssueSeverity.ERROR) {
                return true;
            }
        }
        return false;
    }

    public static boolean defaultHumanAttention(OutcomeStatus status, List<OutcomeIssue> issues) {
        if (status == OutcomeStatus.BLOCKED || status == OutcomeStatus.REVIEW_REQUIRED) {
            return true;
        }
        for (OutcomeIssue issue : issues) {
            if (issue.severity == IssueSeverity.ERROR) {
                return true;
            }
        }
        return false;
    }

    public static Confidence normalizeConfidence(String value) {
        try {
            return Confidence.valueOf((value == null ? "UNKNOWN" : value).toUpperCase());
        } catch (IllegalArgumentException exc) {
            return Confidence.UNKNOWN;
        }
    }

    public static RiskLevel normalizeRiskLevel(String value) {
        try {
            return RiskLevel.valueOf((value == null ? "UNKNOWN" : value).toUpperCase());
        } catch (IllegalArgumentException exc) {
            return RiskLevel.UNKNOWN;
        }
    }
}
"""


def project_operation_outcome_mapper_java() -> str:
    return """package com.atlas.adoption.operationoutcome;

import java.util.List;
import java.util.Map;

public final class ProjectOperationOutcomeMapper {
    public OperationOutcome reviewRequired(String summary, List<OutcomeIssue> issues, List<String> affectedScope, List<String> remainingScope) {
        // TODO(project): map project service/import outcomes to Atlas operation semantics.
        return new OperationOutcome(
                OutcomeStatus.REVIEW_REQUIRED,
                summary,
                issues,
                List.of(),
                affectedScope,
                remainingScope,
                Confidence.UNKNOWN,
                RiskLevel.UNKNOWN,
                null,
                false,
                Map.of("adapter", "project-operation-outcome-java"));
    }
}
"""


def operation_outcome_smoke_java() -> str:
    return """package com.atlas.adoption.operationoutcome;

import java.util.List;
import java.util.Map;

public final class OperationOutcomeScaffoldSmoke {
    public static void main(String[] args) {
        OutcomeIssue issue = new OutcomeIssue("ROW_REVIEW", IssueSeverity.WARNING, "Some rows need human attention");
        OperationOutcome outcome = new OperationOutcome(
                OutcomeStatus.REVIEW_REQUIRED,
                "Import preview needs review",
                List.of(issue),
                List.of(new EvidenceReference("SYNTHETIC-IMPORT-PREVIEW", "synthetic", "row-preview", Map.of())),
                List.of("accepted rows"),
                List.of("review rows"),
                OperationOutcome.normalizeConfidence("medium"),
                OperationOutcome.normalizeRiskLevel("low"),
                null,
                false,
                Map.of());

        require(outcome.humanAttentionRequired, "human attention");
        require(!outcome.hasErrors(), "warning only should not be error");
        require(OperationOutcome.normalizeConfidence("unexpected") == Confidence.UNKNOWN, "confidence normalization");
        require(OperationOutcome.normalizeRiskLevel("odd") == RiskLevel.UNKNOWN, "risk normalization");
    }

    private static void require(boolean condition, String label) {
        if (!condition) {
            throw new IllegalStateException(label);
        }
    }
}
"""


def to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)
