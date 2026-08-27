from __future__ import annotations

from dataclasses import dataclass, field

from .models import UIQualityReview


@dataclass(frozen=True, slots=True)
class UIQualityShadowExpectation:
    id: str
    categories: tuple[str, ...]
    source_project: str
    provenance: str


@dataclass(slots=True)
class UIQualityShadowComparison:
    detected: int
    missed: int
    false_positive: int
    useful_recommendation: int
    matched_expectations: list[str] = field(default_factory=list)
    missed_expectations: list[str] = field(default_factory=list)


def compare_ui_quality(
    review: UIQualityReview,
    expectations: list[UIQualityShadowExpectation],
    *,
    acceptable_extra_categories: set[str] | None = None,
) -> UIQualityShadowComparison:
    acceptable = acceptable_extra_categories or set()
    review_categories = {issue.category for issue in review.issues}
    matched: list[str] = []
    missed: list[str] = []
    for expectation in expectations:
        if any(category in review_categories for category in expectation.categories):
            matched.append(expectation.id)
        else:
            missed.append(expectation.id)

    expected_categories = {category for expectation in expectations for category in expectation.categories}
    false_positive = sum(
        1
        for issue in review.issues
        if issue.recommendation_class == "MECHANICAL_FIX"
        and issue.category not in expected_categories
        and issue.category not in acceptable
    )
    useful = sum(1 for issue in review.issues if issue.suggested_fix)
    return UIQualityShadowComparison(
        detected=len(matched),
        missed=len(missed),
        false_positive=false_positive,
        useful_recommendation=useful,
        matched_expectations=matched,
        missed_expectations=missed,
    )
