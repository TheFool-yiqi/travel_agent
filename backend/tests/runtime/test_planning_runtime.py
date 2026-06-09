import pytest

from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import (
    SkeletonStageHandler,
    StageResult,
    build_default_stage_handlers,
)
from app.runtime.state import RuntimeState, create_initial_runtime_state


@pytest.mark.asyncio
async def test_runtime_emits_9_stage_pairs_and_runtime_completed() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    runtime = PlanningRuntime(build_default_stage_handlers())

    events = [event async for event in runtime.run(state)]

    stage_started = [event.stage for event in events if event.type == "stage_started"]
    stage_completed = [
        event.stage for event in events if event.type == "stage_completed"
    ]

    assert tuple(stage_started) == V1_STAGE_NAMES
    assert tuple(stage_completed) == V1_STAGE_NAMES
    assert events[-1].type == "runtime_completed"


@pytest.mark.asyncio
async def test_runtime_orders_handlers_by_manifest() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    runtime = PlanningRuntime(tuple(reversed(build_default_stage_handlers())))

    events = [event async for event in runtime.run(state)]

    assert tuple(
        event.stage for event in events if event.type == "stage_started"
    ) == V1_STAGE_NAMES


@pytest.mark.asyncio
async def test_runtime_passes_recorded_stage_output_to_next_handler() -> None:
    observed_outputs: dict[str, dict[str, object]] = {}

    class ObservingHandler(SkeletonStageHandler):
        stage_name = "prepare_base_context"
        summary = "observed"

        async def handle(self, state: RuntimeState) -> StageResult:
            observed_outputs.update(state["stage_outputs"])
            return await super().handle(state)

    handlers = list(build_default_stage_handlers())
    handlers[1] = ObservingHandler()
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    events = [event async for event in PlanningRuntime(handlers).run(state)]

    assert observed_outputs["collect"]["status"] == "completed"
    assert events[-1].type == "runtime_completed"


@pytest.mark.asyncio
async def test_runtime_emits_runtime_failed_and_stops() -> None:
    class FailingHandler(SkeletonStageHandler):
        stage_name = "retrieve_evidence"
        summary = "never completed"

        async def handle(self, state: RuntimeState) -> StageResult:
            raise RuntimeError("retrieval failed")

    handlers = list(build_default_stage_handlers())
    handlers[2] = FailingHandler()
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    events = [event async for event in PlanningRuntime(handlers).run(state)]

    assert events[-1].type == "runtime_failed"
    assert events[-1].stage == "retrieve_evidence"
    assert events[-1].payload["error"]["message"] == "retrieval failed"
    assert not any(event.stage == "tool_enrich" for event in events)


def test_runtime_rejects_incomplete_handler_set() -> None:
    with pytest.raises(ValueError, match="exactly one handler"):
        PlanningRuntime(build_default_stage_handlers()[:-1])
