"""Collect stage behavior tests."""

from __future__ import annotations

import pytest

from app.runtime.collect.greeting import GreetingPolicy, GreetingResponder
from app.runtime.collect.readiness import evaluate_readiness
from app.runtime.collect.runtime import CollectRuntime
from app.runtime.state import create_initial_runtime_state


def test_greeting_policy_blocks_planning_on_first_greeting() -> None:
    assert GreetingPolicy.should_greet(
        user_message="你好",
        has_prior_assistant_message=False,
    )
    assert not GreetingPolicy.should_greet(
        user_message="你好",
        has_prior_assistant_message=True,
    )


def test_greeting_responder_does_not_emit_planning_need_fields() -> None:
    reply = GreetingResponder.build_reply()
    assert "成都" not in reply or "例如" in reply


def test_readiness_requires_confirmation_before_planning() -> None:
    fields = {
        "departure_city": "北京",
        "departure_date": "2026-07-01",
        "travel_days": 3,
        "adult_count": 2,
        "children_count": 0,
        "party_confirmed": True,
        "budget_min": 1000.0,
        "budget_max": 3000.0,
    }

    status, _ = evaluate_readiness(fields, user_confirmed=False)
    assert status == "ready_for_confirmation"

    status, _ = evaluate_readiness(fields, user_confirmed=True)
    assert status == "ready_for_planning"


def test_readiness_rejects_unconfirmed_discovery_hypothesis() -> None:
    fields = {
        "departure_city": "北京",
        "departure_date": "2026-07-01",
        "travel_days": 3,
        "adult_count": 2,
        "children_count": 0,
        "party_confirmed": True,
        "budget_min": 1000.0,
        "budget_max": 3000.0,
    }

    status, meta = evaluate_readiness(
        fields,
        user_confirmed=True,
        has_unconfirmed_discovery=True,
    )
    assert status == "continue_collect"
    assert meta["reason"] == "unconfirmed_discovery"


@pytest.mark.asyncio
async def test_collect_runtime_greeting_turn_waits_without_planning_need() -> None:
    runtime = CollectRuntime()
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="你好",
    )

    result = await runtime.process_turn(state)

    assert result.status == "waiting"
    assert result.planning_need is None
    assert result.public_reply


@pytest.mark.asyncio
async def test_collect_runtime_incomplete_trip_spec_waits() -> None:
    runtime = CollectRuntime()
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )

    result = await runtime.process_turn(state)

    assert result.status == "waiting"
    assert result.planning_need is None
    assert result.collect_context["trip_spec"].get("destination") == "成都"
    assert result.collect_context["readiness_state"]["status"] == "continue_collect"
