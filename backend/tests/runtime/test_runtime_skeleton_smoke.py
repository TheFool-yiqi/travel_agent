import pytest

from app.runtime.executor.langgraph_executor import RuntimeLangGraphExecutor
from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.state import create_initial_runtime_state


@pytest.mark.asyncio
async def test_runtime_skeleton_happy_path() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        user_id="user_1",
        input_message="成都三天低强度，喜欢美食",
    )
    executor = RuntimeLangGraphExecutor(checkpointer=None)

    events = [event async for event in executor.stream(state)]

    assert [event.stage for event in events if event.type == "stage_started"] == list(
        V1_STAGE_NAMES
    )
    assert [
        event.stage for event in events if event.type == "stage_completed"
    ] == list(V1_STAGE_NAMES)
    assert events[-1].type == "runtime_completed"
