"""Collect stage handler."""

from __future__ import annotations

from app.runtime.collect.runtime import CollectRuntime
from app.runtime.stages.base import StageResult
from app.runtime.state import (
    RuntimeState,
    record_collect_waiting,
    set_collect_context,
    set_planning_need,
)


class CollectStageHandler:
    stage_name = "collect"

    def __init__(self, *, collect_runtime: CollectRuntime | None = None) -> None:
        self._runtime = collect_runtime or CollectRuntime()

    async def handle(self, state: RuntimeState) -> StageResult:
        result = await self._runtime.process_turn(state)
        updated_state = set_collect_context(state, result.collect_context)

        if result.status == "ready" and result.planning_need is not None:
            updated_state = set_planning_need(updated_state, result.planning_need)
            return StageResult(
                stage=self.stage_name,
                status="completed",
                summary="collect completed with planning need",
                data={
                    "public_reply": result.public_reply,
                    "planning_need": result.planning_need,
                    "collect_context": result.collect_context,
                    "state": updated_state,
                },
            )

        updated_state = record_collect_waiting(updated_state)
        return StageResult(
            stage=self.stage_name,
            status="waiting",
            summary="collect awaiting user",
            data={
                "public_reply": result.public_reply,
                "collect_context": result.collect_context,
                "state": updated_state,
            },
        )
