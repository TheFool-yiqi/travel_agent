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
    record_runtime_error,
    record_stage_output,
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

        yield make_runtime_completed_event(run_id=run_id)


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
