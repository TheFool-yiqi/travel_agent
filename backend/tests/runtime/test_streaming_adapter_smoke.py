"""Slice 9 frontend adapter integration smoke tests."""

from __future__ import annotations

import asyncio

import pytest

from app.runtime.finalization.persistence import StubItineraryPersistenceAdapter
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.state import RuntimeState, set_planning_need
from app.services.runtime_chat_stream import iter_frontend_transport_events

from .test_approval_finalize_smoke import _handlers_with_stub_weather_and_persistence
from .test_collect_context_smoke import _COLLECT_TURN_SEQUENCE, _run_collect_sequence


@pytest.mark.asyncio
async def test_runtime_frontend_events_pause_at_approval() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(**{**state, "input_message": "请先给我看看"})

    runtime = PlanningRuntime(
        _handlers_with_stub_weather_and_persistence(StubItineraryPersistenceAdapter()),
    )
    token_queue: asyncio.Queue[str] = asyncio.Queue()

    payloads = [
        item
        async for item in iter_frontend_transport_events(runtime.run(state), token_queue)
    ]

    assert any(item.get("type") == "step" for item in payloads)
    assert any(item.get("type") == "itinerary" for item in payloads)
    assert any(item.get("type") == "approval_required" for item in payloads)
    assert not any(item.get("type") == "done" for item in payloads)


@pytest.mark.asyncio
async def test_runtime_frontend_events_complete_after_confirm() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(
        **{
            **state,
            "input_message": "确认",
            "conversation_id": "conv_1",
            "user_id": "user_1",
        },
    )

    runtime = PlanningRuntime(
        _handlers_with_stub_weather_and_persistence(StubItineraryPersistenceAdapter()),
    )
    token_queue: asyncio.Queue[str] = asyncio.Queue()

    payloads = [
        item
        async for item in iter_frontend_transport_events(runtime.run(state), token_queue)
    ]

    assert any(item.get("type") == "order" for item in payloads)
    assert payloads[-1] == {"type": "done"}
