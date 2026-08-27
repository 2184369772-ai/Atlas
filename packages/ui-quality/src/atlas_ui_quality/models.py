from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


UISeverity = Literal["INFO", "WARNING", "ERROR"]
UIConfidence = Literal["LOW", "MEDIUM", "HIGH"]
UIRecommendationClass = Literal["MECHANICAL_FIX", "VISUAL_RECOMMENDATION", "BUSINESS_JUDGMENT"]
UIExecutionMode = Literal["safe_auto_fix", "codex_edit", "human_judgment"]


@dataclass(frozen=True, slots=True)
class UIQualityIssue:
    category: str
    severity: UISeverity
    file: str
    line: int
    component: str = ""
    evidence: str = ""
    reason: str = ""
    suggested_fix: str = ""
    auto_fix_safe: bool = False
    confidence: UIConfidence = "MEDIUM"
    recommendation_class: UIRecommendationClass = "MECHANICAL_FIX"
    execution_mode: UIExecutionMode = "codex_edit"


@dataclass(slots=True)
class UIQualityReview:
    project_path: str
    issues: list[UIQualityIssue] = field(default_factory=list)

    @property
    def summary(self) -> dict[str, int]:
        counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for issue in self.issues:
            counts[issue.severity] += 1
        return counts

    @property
    def recommendation_summary(self) -> dict[str, int]:
        counts = {
            "MECHANICAL_FIX": 0,
            "VISUAL_RECOMMENDATION": 0,
            "BUSINESS_JUDGMENT": 0,
            "safe_auto_fix": 0,
            "codex_edit": 0,
            "human_judgment": 0,
        }
        for issue in self.issues:
            counts[issue.recommendation_class] += 1
            counts[issue.execution_mode] += 1
        return counts

    def to_dict(self) -> dict[str, object]:
        return {
            "project_path": self.project_path,
            "summary": self.summary,
            "recommendation_summary": self.recommendation_summary,
            "issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "file": issue.file,
                    "line": issue.line,
                    "component": issue.component,
                    "evidence": issue.evidence,
                    "reason": issue.reason,
                    "suggested_fix": issue.suggested_fix,
                    "auto_fix_safe": issue.auto_fix_safe,
                    "confidence": issue.confidence,
                    "recommendation_class": issue.recommendation_class,
                    "execution_mode": issue.execution_mode,
                }
                for issue in self.issues
            ],
        }
