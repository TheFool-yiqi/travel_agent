"""Slice 3 collect and context integration smoke tests."""

from __future__ import annotations

import pytest

from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.stages.prepare_base_context import PrepareBaseContextStageHandler
from app.runtime.collect.runtime import CollectRuntime, CollectTurnResult
from app.runtime.state import (
    RuntimeState,
    create_initial_runtime_state,
    set_collect_context,
    set_planning_need,
)

_COLLECT_TURN_SEQUENCE = (
    "你好",
    "成都",
    "北京",
    "2026-07-01",
    "3天",
    "2大人",
    "一般党",
    "确认",
)


def _append_public_message(
    state: RuntimeState,
    *,
    role: str,
    content: str,
) -> RuntimeState:
    updated = dict(state)
    messages = list(updated.get("public_messages") or [])
    messages.append({"role": role, "content": content})
    updated["public_messages"] = messages
    return RuntimeState(**updated)


async def _run_collect_sequence(
    turns: tuple[str, ...] | list[str],
    *,
    initial_state: RuntimeState | None = None,
) -> tuple[RuntimeState, CollectTurnResult]:
    collect = CollectRuntime()
    state = initial_state or create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message=turns[0],
    )
    public_messages: list[dict[str, str]] = list(state.get("public_messages") or [])
    last_result: CollectTurnResult | None = None

    for message in turns:
        state = RuntimeState(
            **{
                **state,
                "input_message": message,
                "public_messages": list(public_messages),
            },
        )
        last_result = await collect.process_turn(state)
        state = set_collect_context(state, last_result.collect_context)
        public_messages.append({"role": "assistant", "content": last_result.public_reply})
        public_messages.append({"role": "user", "content": message})

    assert last_result is not None
    return state, last_result


@pytest.mark.asyncio
async def test_planning_runtime_stops_on_first_collect_waiting_turn() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="你好",
    )
    runtime = PlanningRuntime(build_default_stage_handlers())

    events = [event async for event in runtime.run(state)]

    assert [event.stage for event in events if event.type == "stage_started"] == ["collect"]
    assert events[-1].type == "stage_completed"
    assert events[-1].payload["output"]["status"] == "waiting"
    assert not any(event.type == "runtime_completed" for event in events)


@pytest.mark.asyncio
async def test_multiturn_collect_reaches_planning_need_and_base_context() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)

    assert ready_turn.status == "ready"
    assert ready_turn.planning_need is not None

    state = set_planning_need(state, ready_turn.planning_need)
    base_result = await PrepareBaseContextStageHandler().handle(state)

    assert base_result["status"] == "completed"
    summary = base_result["data"]["base_context"]["planning_need_summary"]
    assert summary["destination"] == "成都"
    assert summary["departure_city"] == "北京"
    assert summary["travel_days"] == 3


@pytest.mark.asyncio
async def test_collect_ready_path_runs_prepare_base_context_and_skeleton_finalize() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    assert ready_turn.status == "ready"

    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(**{**state, "input_message": "确认"})

    events = [event async for event in PlanningRuntime(build_default_stage_handlers()).run(state)]

    started = [event.stage for event in events if event.type == "stage_started"]
    assert started[0] == "collect"
    assert started[1:] == list(V1_STAGE_NAMES[1:])
    assert events[-1].type == "runtime_completed"

    completed = [event.stage for event in events if event.type == "stage_completed"]
    assert completed == list(V1_STAGE_NAMES)
    assert any(
        event.stage == "prepare_base_context" and event.payload["output"]["status"] == "completed"
        for event in events
        if event.type == "stage_completed"
    )
