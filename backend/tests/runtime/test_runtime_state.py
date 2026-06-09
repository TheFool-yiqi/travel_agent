import pytest

from app.runtime.manifest import V1_STAGE_NAMES, is_valid_stage
from app.runtime.state import (
    create_initial_runtime_state,
    mark_stage_started,
    record_runtime_error,
    record_stage_output,
)


def test_v1_stage_names_are_frozen() -> None:
    assert V1_STAGE_NAMES == (
        "collect",
        "prepare_base_context",
        "retrieve_evidence",
        "tool_enrich",
        "domain_plan",
        "integrate",
        "verify",
        "approve_or_revise",
        "finalize",
    )


def test_old_graph_names_are_not_runtime_stages() -> None:
    for old_name in {
        "collect_requirements",
        "plan_destination",
        "plan_transport",
        "plan_stay_and_food",
        "plan_activities",
        "build_itinerary",
        "approval_node",
        "final_response",
    }:
        assert not is_valid_stage(old_name)


def test_create_initial_runtime_state_has_no_prompt_context() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        user_id="user_1",
        input_message="成都三天低强度",
    )

    assert state["run_id"] == "run_1"
    assert state["current_stage"] == "collect"
    assert state["completed_stages"] == []
    assert state["stage_outputs"] == {}
    assert "prompt" not in state
    assert "assembled_context" not in state


def test_mark_stage_started_updates_copy_and_validates_stage() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    updated = mark_stage_started(state, "retrieve_evidence")

    assert updated["current_stage"] == "retrieve_evidence"
    assert state["current_stage"] == "collect"

    with pytest.raises(ValueError, match="Unknown runtime stage"):
        mark_stage_started(state, "build_itinerary")


def test_record_stage_output_tracks_completion_without_mutating_input() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    updated = record_stage_output(
        state,
        stage="collect",
        output={"status": "completed"},
    )

    assert updated["completed_stages"] == ["collect"]
    assert updated["stage_outputs"]["collect"] == {"status": "completed"}
    assert state["completed_stages"] == []
    assert state["stage_outputs"] == {}


def test_record_runtime_error_appends_structured_error_copy() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    error = {"stage": "collect", "message": "failed"}

    updated = record_runtime_error(state, error=error)
    error["message"] = "changed"

    assert updated["errors"] == [{"stage": "collect", "message": "failed"}]
    assert state["errors"] == []
