"""Sequential PlanningRuntime dispatcher."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from typing import Any

from app.runtime.events import (
    RuntimeEvent,
    make_runtime_completed_event,
    make_runtime_failed_event,
    make_stage_completed_event,
    make_stage_started_event,
)
from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.stages.base import StageHandler
from app.runtime.state import (
    RuntimeState,
    mark_stage_started,
    record_collect_waiting,
    record_runtime_error,
    record_stage_output,
    set_base_context,
    set_collect_context,
    set_evidence_context,
    set_planning_need,
    set_sufficiency_result,
    set_tool_context,
    set_plan_proposals,
    set_itinerary_draft,
    set_quality_report,
    set_pending_approval,
    set_approval_status,
    set_order_id,
    set_finalization_result,
)


class PlanningRuntime:
    def __init__(self, handlers: Sequence[StageHandler]) -> None:
        self._handlers = _order_handlers(handlers)

    async def run(self, state: RuntimeState) -> AsyncIterator[RuntimeEvent]:
        """Run all V1 stages sequentially and emit internal RuntimeEvents."""
        current_state = RuntimeState(**state)
        run_id = current_state["run_id"]

        for handler in self._handlers:
            stage = handler.stage_name
            current_state = mark_stage_started(current_state, stage)
            yield make_stage_started_event(run_id=run_id, stage=stage)

            try:
                result = await handler.handle(current_state)
            except Exception as exc:
                error = {
                    "type": type(exc).__name__,
                    "message": str(exc),
                }
                current_state = record_runtime_error(current_state, error=error)
                yield make_runtime_failed_event(
                    run_id=run_id,
                    stage=stage,
                    error=error,
                )
                return

            output = dict(result)
            current_state = _apply_stage_state_updates(current_state, output)
            current_state = record_stage_output(
                current_state,
                stage=stage,
                output=output,
            )
            yield make_stage_completed_event(
                run_id=run_id,
                stage=stage,
                output=output,
            )

            if output.get("status") == "waiting":
                current_state = record_collect_waiting(current_state)
                return

        yield make_runtime_completed_event(run_id=run_id)


def _apply_stage_state_updates(
    state: RuntimeState,
    output: dict[str, Any],
) -> RuntimeState:
    data = output.get("data")
    if not isinstance(data, dict):
        return state

    updated = RuntimeState(**state)
    nested_state = data.get("state")
    if isinstance(nested_state, dict):
        updated = RuntimeState(**nested_state)

    if "collect_context" in data:
        updated = set_collect_context(updated, data["collect_context"])
    if data.get("planning_need") is not None:
        updated = set_planning_need(updated, data["planning_need"])
    if data.get("base_context") is not None:
        updated = set_base_context(updated, data["base_context"])
    if data.get("evidence_context") is not None:
        updated = set_evidence_context(updated, data["evidence_context"])
    if data.get("sufficiency_result") is not None:
        updated = set_sufficiency_result(updated, data["sufficiency_result"])
    if data.get("tool_context") is not None:
        updated = set_tool_context(updated, data["tool_context"])
    if data.get("plan_proposals") is not None:
        updated = set_plan_proposals(updated, data["plan_proposals"])
    if data.get("itinerary_draft") is not None:
        updated = set_itinerary_draft(updated, data["itinerary_draft"])
    if data.get("quality_report") is not None:
        updated = set_quality_report(updated, data["quality_report"])
    if data.get("pending_approval") is not None:
        updated = set_pending_approval(updated, data["pending_approval"])
    if data.get("approval_status") is not None:
        updated = set_approval_status(updated, str(data["approval_status"]))
    if data.get("order_id") is not None:
        updated = set_order_id(updated, str(data["order_id"]))
    if data.get("finalization_result") is not None:
        updated = set_finalization_result(updated, data["finalization_result"])
    return updated


def _order_handlers(handlers: Sequence[StageHandler]) -> tuple[StageHandler, ...]:
    handlers_by_stage: dict[str, StageHandler] = {}
    for handler in handlers:
        stage = handler.stage_name
        if stage in handlers_by_stage:
            raise ValueError(f"PlanningRuntime requires exactly one handler for stage: {stage}")
        handlers_by_stage[stage] = handler

    if set(handlers_by_stage) != set(V1_STAGE_NAMES):
        missing = sorted(set(V1_STAGE_NAMES) - set(handlers_by_stage))
        unexpected = sorted(set(handlers_by_stage) - set(V1_STAGE_NAMES))
        details: dict[str, Any] = {
            "missing": missing,
            "unexpected": unexpected,
        }
        raise ValueError(
            f"PlanningRuntime requires exactly one handler for each V1 stage: {details}"
        )

    return tuple(handlers_by_stage[stage] for stage in V1_STAGE_NAMES)
