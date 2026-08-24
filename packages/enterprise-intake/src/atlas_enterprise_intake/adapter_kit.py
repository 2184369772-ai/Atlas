from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .engine import build_intake_preview
from .models import IntakeIssue, IntakePreview, IntakeRequest, IntakeRowDecision, IntakeRowInput


FieldMappingHook = Callable[[list[Any]], dict[str, str]]
RowEvaluationHook = Callable[[IntakeRowInput], IntakeRowDecision]
DuplicateHook = Callable[[IntakeRowInput, IntakeRowDecision], "DuplicateCheckResult | None"]
TraceMetadataHook = Callable[[IntakeRowInput, IntakeRowDecision], dict[str, Any]]


@dataclass(slots=True)
class DuplicateCheckResult:
    decision: str | None = None
    issues: list[IntakeIssue] = field(default_factory=list)
    trace: dict[str, Any] = field(default_factory=dict)


class HookedAdapter:
    def __init__(
        self,
        *,
        row_evaluator: RowEvaluationHook,
        field_mapping_hook: FieldMappingHook | None = None,
        duplicate_hook: DuplicateHook | None = None,
        trace_metadata_hook: TraceMetadataHook | None = None,
    ) -> None:
        self._row_evaluator = row_evaluator
        self._field_mapping_hook = field_mapping_hook
        self._duplicate_hook = duplicate_hook
        self._trace_metadata_hook = trace_metadata_hook

    def resolve_field_mapping(self, headers: list[Any]) -> dict[str, str]:
        if self._field_mapping_hook is None:
            return {}
        return dict(self._field_mapping_hook(headers))

    def evaluate_row(self, row: IntakeRowInput) -> IntakeRowDecision:
        decision = self._row_evaluator(row)
        if self._duplicate_hook is not None:
            duplicate = self._duplicate_hook(row, decision)
            if duplicate is not None:
                if duplicate.decision is not None:
                    decision.decision = duplicate.decision
                decision.issues.extend(duplicate.issues)
                decision.trace.update(duplicate.trace)
        if self._trace_metadata_hook is not None:
            decision.trace.update(self._trace_metadata_hook(row, decision))
        return decision


def build_preview_with_adapter(
    tabular_result,
    adapter: HookedAdapter,
    *,
    preview_mode: bool = True,
    source_name: str | None = None,
    stop_on_structural_errors: bool = False,
) -> IntakePreview:
    request = IntakeRequest(
        source_name=source_name,
        preview_mode=preview_mode,
        field_mapping=adapter.resolve_field_mapping(tabular_result.headers),
        stop_on_structural_errors=stop_on_structural_errors,
    )
    return build_intake_preview(tabular_result, adapter, request=request)
