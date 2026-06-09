import pytest

from app.runtime.executor.graph_builder import build_runtime_graph
from app.runtime.executor.langgraph_executor import RuntimeLangGraphExecutor
from app.runtime.events import RuntimeEvent
from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.state import create_initial_runtime_state

from .test_planning_runtime import _handlers_with_completed_collect


def test_runtime_graph_builder_uses_v1_stage_names() -> None:
    graph = build_runtime_graph(checkpointer=None)

    graph_nodes = set(graph.get_graph().nodes)

    assert set(V1_STAGE_NAMES).issubset(graph_nodes)
    assert not {
        "collect_requirements",
        "plan_destination",
        "plan_transport",
        "plan_stay_and_food",
        "plan_activities",
        "build_itinerary",
        "approval_node",
        "final_response",
    }.intersection(graph_nodes)


@pytest.mark.asyncio
async def test_runtime_graph_executes_happy_path_without_checkpointer() -> None:
    graph = build_runtime_graph(checkpointer=None)
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    result = await graph.ainvoke(state)

    assert result["completed_stages"] == list(V1_STAGE_NAMES)
    assert tuple(result["stage_outputs"]) == V1_STAGE_NAMES
    assert result["current_stage"] == "finalize"


@pytest.mark.asyncio
async def test_runtime_langgraph_executor_streams_runtime_events() -> None:
    executor = RuntimeLangGraphExecutor(
        checkpointer=None,
        handlers=_handlers_with_completed_collect(),
    )
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    events = [event async for event in executor.stream(state)]

    assert all(isinstance(event, RuntimeEvent) for event in events)
    assert tuple(
        event.stage for event in events if event.type == "stage_started"
    ) == V1_STAGE_NAMES
    assert events[-1].type == "runtime_completed"


def test_runtime_langgraph_executor_accepts_optional_checkpointer() -> None:
    checkpointer = object()

    executor = RuntimeLangGraphExecutor(checkpointer=checkpointer)

    assert executor.checkpointer is checkpointer
