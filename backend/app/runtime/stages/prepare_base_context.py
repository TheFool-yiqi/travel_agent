"""Prepare-base-context stage."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from app.runtime.collect.schemas import PlanningNeed
from app.runtime.context.builder import build_base_context_from_planning_need
from app.runtime.stages.base import StageResult
from app.runtime.state import RuntimeState, set_base_context

STAGE_NAME = "prepare_base_context"

MemorySnippetLoader = Callable[[RuntimeState], Awaitable[list[dict[str, Any]]]]


async def _default_memory_snippet_loader(state: RuntimeState) -> list[dict[str, Any]]:
    """V1 stub: long-term memory enters BaseContext in a later slice."""
    _ = state
    return []


class PrepareBaseContextStageHandler:
    stage_name = STAGE_NAME

    def __init__(
        self,
        *,
        memory_snippet_loader: MemorySnippetLoader | None = None,
    ) -> None:
        self._memory_snippet_loader = memory_snippet_loader or _default_memory_snippet_loader

    async def handle(self, state: RuntimeState) -> StageResult:
        planning_need_raw = state.get("planning_need")
        if not planning_need_raw:
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="prepare_base_context requires planning_need",
                data={
                    "error": {
                        "type": "missing_planning_need",
                        "message": "prepare_base_context requires planning_need",
                    },
                },
            )

        planning_need = PlanningNeed.from_runtime_dict(planning_need_raw)
        memory_snippets = await self._memory_snippet_loader(state)
        base_context = build_base_context_from_planning_need(
            planning_need,
            memory_snippets=memory_snippets,
        )
        base_context_dict = base_context.to_runtime_dict()
        updated_state = set_base_context(state, base_context_dict)

        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary="base context prepared from planning need",
            data={
                "base_context": base_context_dict,
                "state": updated_state,
            },
        )
