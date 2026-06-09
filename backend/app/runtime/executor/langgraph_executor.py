"""PlanningRuntime event-stream adapter for LangGraph execution integration."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from langgraph.checkpoint.base import BaseCheckpointSaver

from app.runtime.events import RuntimeEvent
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import StageHandler, build_default_stage_handlers
from app.runtime.state import RuntimeState


class RuntimeLangGraphExecutor:
    """Expose the stable RuntimeEvent stream before raw graph event bridging."""

    def __init__(
        self,
        *,
        checkpointer: BaseCheckpointSaver | None = None,
        handlers: Sequence[StageHandler] | None = None,
    ) -> None:
        self.checkpointer = checkpointer
        self._runtime = PlanningRuntime(handlers or build_default_stage_handlers())

    async def stream(self, state: RuntimeState) -> AsyncIterator[RuntimeEvent]:
        """Yield internal RuntimeEvents without exposing raw LangGraph events."""
        async for event in self._runtime.run(state):
            yield event
