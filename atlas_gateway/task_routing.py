from __future__ import annotations

import re
from dataclasses import dataclass


TASK_REUSE = "TASK_REUSE"
TASK_REFERENCE = "TASK_REFERENCE"
PROJECT_RELEVANT = "PROJECT_RELEVANT"
NO_ATLAS_REUSE = "NO_ATLAS_REUSE"


@dataclass(frozen=True, slots=True)
class TaskDecision:
    decision: str
    reason: str


def route_task_for_capability(capability_id: str, recommendation: str, task: str, *, is_java_project: bool = False) -> TaskDecision:
    text = normalize(task)
    if not text:
        return TaskDecision(PROJECT_RELEVANT, "No task description was provided; keeping project-level discovery only.")

    if is_access_control_task(text):
        if capability_id == "business-rule-modeling":
            return TaskDecision(
                TASK_REFERENCE,
                "The task is permission/access-boundary work; Atlas can only provide business-rule boundary reference.",
            )
        return TaskDecision(
            PROJECT_RELEVANT,
            "The capability is project-relevant, but this task is permission/access-control closeout rather than Atlas reusable semantics.",
        )

    if is_local_tabular_compatibility_fix(text) and capability_id in {"tabular-core", "enterprise-intake"}:
        return TaskDecision(
            PROJECT_RELEVANT,
            "The project has tabular/import capability signals, but the task is a local compatibility fix in an existing import chain.",
        )

    if is_existing_page_or_approval_task(text):
        if capability_id == "business-rule-modeling":
            return TaskDecision(
                TASK_REFERENCE,
                "The task overlaps approval/business-rule boundary language, but implementation remains project-owned.",
            )
        if capability_id == "ui-quality-interaction-reliability" and has_any(text, UI_EXPLICIT_TERMS):
            return TaskDecision(TASK_REFERENCE, "The task is a UI closeout/review task; use UI Quality as a review aid only.")
        return TaskDecision(
            PROJECT_RELEVANT,
            "The capability is project-relevant, but this task is an existing approval/page workflow change rather than a reusable Atlas boundary.",
        )

    if capability_id == "enterprise-intake":
        if has_any(text, ENTERPRISE_INTAKE_REUSE_TERMS) and has_any(text, ENTERPRISE_IMPORT_CONTEXT_TERMS):
            return TaskDecision(TASK_REUSE, "The task explicitly needs import preview, row decision, issue, or commit-readiness semantics.")
        return TaskDecision(PROJECT_RELEVANT, "Enterprise Intake is project-relevant, but this task does not need its reusable intake semantics.")

    if capability_id == "tabular-core":
        if has_tabular_reuse_signal(text) and not is_local_tabular_compatibility_fix(text):
            return TaskDecision(TASK_REUSE, "The task explicitly needs CSV/XLSX structure reading or tabular semantics.")
        return TaskDecision(PROJECT_RELEVANT, "Tabular Core is project-relevant, but this task does not need Atlas tabular parsing.")

    if capability_id == "operation-outcome":
        if has_any(text, OPERATION_OUTCOME_TERMS):
            return TaskDecision(TASK_REUSE, "The task explicitly needs operation result, issue, scope, evidence, or human-attention semantics.")
        return TaskDecision(PROJECT_RELEVANT, "Operation Outcome is project-relevant, but this task does not need result-semantics reuse.")

    if capability_id == "report-export-semantics":
        if has_any(text, REPORT_EXPORT_REUSE_TERMS) and not is_existing_page_or_approval_task(text):
            return TaskDecision(TASK_REUSE, "The task explicitly needs report/export source, dimension, metric, or projection semantics.")
        return TaskDecision(PROJECT_RELEVANT, "Report/export is project-relevant, but this task is not report/export semantic work.")

    if capability_id == "runtime-config":
        if has_any(text, RUNTIME_CONFIG_TERMS):
            return TaskDecision(TASK_REUSE, "The task explicitly needs runtime config, effective value, or environment comparison semantics.")
        return TaskDecision(PROJECT_RELEVANT, "Runtime Config is project-relevant, but this task is not configuration semantics work.")

    if capability_id == "file-lifecycle":
        if has_any(text, FILE_LIFECYCLE_TERMS):
            return TaskDecision(TASK_REUSE, "The task explicitly needs file identity, upload/archive/retention, or lifecycle semantics.")
        return TaskDecision(PROJECT_RELEVANT, "File Lifecycle is project-relevant, but this task is not file lifecycle semantics work.")

    if capability_id == "ai-execution":
        if has_any(text, AI_EXECUTION_TERMS):
            return TaskDecision(TASK_REUSE, "The task explicitly needs AI execution result, fallback, confidence/risk, or escalation semantics.")
        return TaskDecision(PROJECT_RELEVANT, "AI Execution is project-relevant, but this task is not AI execution semantics work.")

    if capability_id == "knowledge-intake":
        if has_any(text, KNOWLEDGE_INTAKE_TERMS):
            return TaskDecision(TASK_REUSE, "The task explicitly needs source identity, citation, retrieval evidence, conflict, or review semantics.")
        return TaskDecision(PROJECT_RELEVANT, "Knowledge Intake is project-relevant, but this task is not knowledge intake semantics work.")

    if capability_id == "business-rule-modeling":
        if has_any(text, BUSINESS_RULE_TERMS):
            return TaskDecision(TASK_REFERENCE, "The task overlaps business-rule semantics, but Atlas should only be used as reference.")
        return TaskDecision(PROJECT_RELEVANT, "Business Rule Modeling is project-relevant, but this task does not need rule-boundary reference.")

    if capability_id == "ui-quality-interaction-reliability":
        if has_any(text, UI_EXPLICIT_TERMS) and has_any(text, UI_CLOSEOUT_TERMS):
            return TaskDecision(TASK_REFERENCE, "The task is function-complete, phase acceptance, or UI closeout work.")
        return TaskDecision(PROJECT_RELEVANT, "UI Quality is project-relevant, but this task is not a UI closeout/review stage.")

    if recommendation == "REFERENCE_ONLY" and has_any(text, REFERENCE_ONLY_TERMS):
        return TaskDecision(TASK_REFERENCE, "The task overlaps this reference-only capability boundary.")

    return TaskDecision(PROJECT_RELEVANT, "The capability may matter to the project, but the current task does not justify Atlas adoption.")


def summarize_task_decisions(decisions: list[str]) -> str:
    if TASK_REUSE in decisions:
        return TASK_REUSE
    if TASK_REFERENCE in decisions:
        return TASK_REFERENCE
    if PROJECT_RELEVANT in decisions:
        return PROJECT_RELEVANT
    return NO_ATLAS_REUSE


def normalize(value: str) -> str:
    return value.lower().replace("_", " ").replace("-", " ")


def has_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term in text for term in terms)


def has_word(text: str, term: str) -> bool:
    return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None


def has_tabular_reuse_signal(text: str) -> bool:
    if has_any(text, TABULAR_LITERAL_TERMS):
        return True
    return any(has_word(text, term) for term in TABULAR_WORD_TERMS)


def is_access_control_task(text: str) -> bool:
    return has_any(text, ACCESS_CONTROL_TERMS) and has_any(text, ACCESS_TASK_TERMS)


def is_local_tabular_compatibility_fix(text: str) -> bool:
    if not (has_any(text, LOCAL_FIX_TERMS) and has_any(text, TABULAR_COMPAT_TERMS)):
        return False
    if has_any(text, NO_NEW_REUSE_TERMS):
        return True
    return not has_any(text, NEW_IMPORT_TERMS)


def is_existing_page_or_approval_task(text: str) -> bool:
    return has_any(text, PAGE_OR_WORKFLOW_TERMS) and has_any(text, APPROVAL_TERMS) and not has_any(text, REPORT_EXPORT_REUSE_TERMS)


LOCAL_FIX_TERMS = (
    "已有",
    "现有",
    "局部",
    "兼容",
    "修复",
    "bug",
    "fix",
    "compat",
    "compatibility",
    "只修",
)
TABULAR_COMPAT_TERMS = (
    "sheet",
    "表头",
    "header",
    "模板",
    "template",
    "excel",
    "xlsx",
)
NEW_IMPORT_TERMS = (
    "新增导入",
    "新建导入",
    "导入预检",
    "导入预览",
    "初始化导入",
    "import preview",
    "intake",
    "dry run",
)
NO_NEW_REUSE_TERMS = (
    "不新增",
    "不新建",
    "不是新增",
    "不增加",
    "no new",
    "not add",
    "without adding",
)
IMPORT_OR_PREVIEW_TERMS = (
    "导入",
    "预检",
    "预览",
    "import",
    "preview",
    "intake",
    "dry run",
)
ENTERPRISE_IMPORT_CONTEXT_TERMS = (
    "导入",
    "预检",
    "预览",
    "import",
    "preview",
    "intake",
)
ENTERPRISE_INTAKE_REUSE_TERMS = (
    "行级",
    "row decision",
    "accept",
    "review",
    "reject",
    "skip",
    "partial completion",
    "commit readiness",
    "提交就绪",
    "重复",
    "duplicate",
    "校验",
    "validation",
    "issue",
    "问题",
)
TABULAR_REUSE_TERMS = (
    "csv",
    "xlsx",
    "excel",
    "读取",
    "解析",
    "parse",
    "read",
    "sheet",
    "表头",
    "单元格",
)
TABULAR_LITERAL_TERMS = (
    "csv",
    "xlsx",
    "excel",
    "读取",
    "解析",
    "表头",
    "单元格",
)
TABULAR_WORD_TERMS = (
    "parse",
    "read",
    "sheet",
    "header",
    "row",
    "column",
    "tabular",
)
OPERATION_OUTCOME_TERMS = (
    "处理结果",
    "结果回写",
    "回写",
    "operation outcome",
    "operation result",
    "affected",
    "remaining",
    "evidence",
    "人工关注",
    "human attention",
    "status",
    "issue",
    "问题报告",
    "commit readiness",
)
REPORT_EXPORT_REUSE_TERMS = (
    "报表",
    "报告",
    "导出",
    "export",
    "report",
    "月报聚合",
    "聚合",
    "metric",
    "variance",
    "projection",
)
RUNTIME_CONFIG_TERMS = (
    "配置",
    "环境变量",
    "env",
    "runtime config",
    "application.yml",
    "secret",
    "effective config",
)
FILE_LIFECYCLE_TERMS = (
    "上传",
    "归档",
    "retention",
    "archive",
    "upload",
    "cleanup",
    "临时文件",
    "文件生命周期",
)
AI_EXECUTION_TERMS = (
    "ai调用",
    "模型调用",
    "provider",
    "fallback",
    "confidence",
    "risk",
    "escalation",
    "llm",
    "timeout",
)
KNOWLEDGE_INTAKE_TERMS = (
    "知识",
    "引用",
    "citation",
    "retrieval",
    "检索",
    "source identity",
    "provenance",
    "conflict",
    "人工审核",
)
BUSINESS_RULE_TERMS = (
    "审批",
    "确认",
    "办理",
    "权限",
    "规则",
    "流程",
    "责任",
    "warning",
    "blocking",
    "business rule",
)
ACCESS_CONTROL_TERMS = (
    "权限",
    "授权",
    "访问",
    "access",
    "permission",
    "permissions",
    "rbac",
    "auth",
    "authorize",
    "authorization",
    "lock",
    "unlock",
    "锁定",
    "解锁",
)
ACCESS_TASK_TERMS = (
    "接口",
    "查询",
    "后端",
    "收口",
    "api",
    "endpoint",
    "query",
    "backend",
    "closeout",
    "access control",
)
PAGE_OR_WORKFLOW_TERMS = (
    "页面",
    "办理页",
    "收口",
    "路径",
    "流程",
    "page",
    "workflow",
    "screen",
)
APPROVAL_TERMS = (
    "审批",
    "确认",
    "财务",
    "业务确认",
    "办理",
    "approval",
    "finance",
)
UI_CLOSEOUT_TERMS = (
    "ui",
    "界面",
    "视觉",
    "前端",
    "收口",
    "验收",
    "review",
    "closeout",
)
UI_EXPLICIT_TERMS = (
    "ui",
    "前端",
    "视觉",
    "界面",
    "ui review",
    "visual",
    "frontend",
)
REFERENCE_ONLY_TERMS = BUSINESS_RULE_TERMS + UI_CLOSEOUT_TERMS
