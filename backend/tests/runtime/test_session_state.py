"""PlanningRuntime session state persistence tests."""

from __future__ import annotations

from app.runtime.session_state import (
    load_runtime_state_from_session,
    prepare_runtime_turn,
    should_reset_runtime_state,
)
from app.runtime.state import create_initial_runtime_state, record_collect_waiting


def test_should_reset_after_finalize_completed() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="确认",
    )
    state = {
        **state,
        "completed_stages": ["finalize"],
        "order_id": "ORDER-1",
    }
    assert should_reset_runtime_state(state) is True


def test_should_not_reset_while_awaiting_user() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="你好",
    )
    state = record_collect_waiting(state)
    assert should_reset_runtime_state(state) is False


def test_load_runtime_state_resumes_from_session_extra_info() -> None:
    persisted = create_initial_runtime_state(
        run_id="run_old",
        conversation_id="conv_1",
        input_message="成都",
        user_id="user_1",
    )
    persisted = record_collect_waiting({**persisted, "collect_context": {"trip_spec": {}}})

    loaded = load_runtime_state_from_session(
        {"planning_runtime": dict(persisted)},
        run_id="run_new",
        conversation_id="conv_1",
        user_id="user_1",
        input_message="3天",
    )

    assert loaded["run_id"] == "run_old"
    assert loaded["input_message"] == "3天"
    assert loaded.get("collect_context") == {"trip_spec": {}}


def test_prepare_runtime_turn_appends_user_public_message() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="",
    )
    updated = prepare_runtime_turn(
        state,
        input_message="成都",
        user_message_record={"role": "user", "content": "成都"},
    )
    assert updated["input_message"] == "成都"
    assert updated["public_messages"] == [{"role": "user", "content": "成都"}]
