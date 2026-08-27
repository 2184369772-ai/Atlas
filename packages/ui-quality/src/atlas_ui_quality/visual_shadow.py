from __future__ import annotations

from dataclasses import dataclass, field

from .models import UIQualityReview


@dataclass(frozen=True, slots=True)
class UIVisualReplayExpectation:
    id: str
    category: str
    source_project: str
    provenance: str
    business_only: bool = False


@dataclass(slots=True)
class UIVisualReplayComparison:
    useful_recommendation: int
    missed: int
    misleading: int
    business_only: int
    matched_expectations: list[str] = field(default_factory=list)
    missed_expectations: list[str] = field(default_factory=list)
    unexpected_categories: list[str] = field(default_factory=list)


def compare_visual_recommendations(
    review: UIQualityReview,
    expectations: list[UIVisualReplayExpectation],
) -> UIVisualReplayComparison:
    visual_categories = {
        issue.category
        for issue in review.issues
        if issue.recommendation_class == "VISUAL_RECOMMENDATION"
    }
    expected_categories = {
        expectation.category
        for expectation in expectations
        if not expectation.business_only
    }
    matched: list[str] = []
    missed: list[str] = []
    business_only = 0
    for expectation in expectations:
        if expectation.business_only:
            business_only += 1
        elif expectation.category in visual_categories:
            matched.append(expectation.id)
        else:
            missed.append(expectation.id)

    unexpected = sorted(visual_categories - expected_categories)
    return UIVisualReplayComparison(
        useful_recommendation=len(matched),
        missed=len(missed),
        misleading=len(unexpected),
        business_only=business_only,
        matched_expectations=matched,
        missed_expectations=missed,
        unexpected_categories=unexpected,
    )
