"""LangGraph builder for the PlanningRuntime stage skeleton."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.stages.base import StageHandler, build_default_stage_handlers
from app.runtime.state import RuntimeState, mark_stage_started, record_stage_output


def build_runtime_graph(*, checkpointer: BaseCheckpointSaver | None = None):
    """Compile the independent 9-stage PlanningRuntime execution graph."""
    builder = StateGraph(RuntimeState)
    handlers = build_default_stage_handlers()

    for handler in handlers:
        builder.add_node(handler.stage_name, _build_stage_node(handler))

    builder.add_edge(START, V1_STAGE_NAMES[0])
    for current_stage, next_stage in zip(V1_STAGE_NAMES, V1_STAGE_NAMES[1:]):
        builder.add_edge(current_stage, next_stage)
    builder.add_edge(V1_STAGE_NAMES[-1], END)

    return builder.compile(checkpointer=checkpointer)


def _build_stage_node(
    handler: StageHandler,
) -> Callable[[RuntimeState], Any]:
    async def stage_node(state: RuntimeState) -> RuntimeState:
        stage = handler.stage_name
        started_state = mark_stage_started(state, stage)
        result = await handler.handle(started_state)
        return record_stage_output(
            started_state,
            stage=stage,
            output=dict(result),
        )

    return stage_node
