import pytest

from app.runtime.manifest import V1_STAGE_NAMES, is_valid_stage
from app.runtime.state import (
    create_initial_runtime_state,
    mark_stage_started,
    record_collect_waiting,
    record_runtime_error,
    record_stage_output,
    set_base_context,
    set_collect_context,
    set_evidence_context,
    set_planning_need,
    set_sufficiency_result,
    set_tool_context,
    set_plan_proposals,
    set_itinerary_draft,
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
    assert state.get("collect_context") is None
    assert state.get("planning_need") is None
    assert state.get("base_context") is None
    assert state.get("awaiting_user") is False
    assert state.get("collect_turn_count") == 0
    assert state.get("evidence_context") is None
    assert state.get("sufficiency_result") is None
    assert state.get("tool_context") is None
    assert state.get("plan_proposals") is None
    assert state.get("itinerary_draft") is None


def test_set_plan_proposals_and_itinerary_draft_return_copies() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    proposals = [{"agent_name": "destination_planner", "summary": "成都"}]
    draft = {"destination": "成都", "travel_days": 3, "days": []}

    updated = set_itinerary_draft(set_plan_proposals(state, proposals), draft)
    proposals.append({"agent_name": "stay_food_planner", "summary": "food"})
    draft["travel_days"] = 5

    assert len(updated["plan_proposals"]) == 1
    assert updated["itinerary_draft"]["travel_days"] == 3
    assert state.get("plan_proposals") is None


def test_set_tool_context_returns_copy() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    tool_context = {"weather": {"status": "available", "summary": "多云"}}

    updated = set_tool_context(state, tool_context)
    tool_context["weather"]["summary"] = "晴"

    assert updated["tool_context"] == {"weather": {"status": "available", "summary": "多云"}}
    assert state.get("tool_context") is None


def test_set_evidence_context_and_sufficiency_result_return_copies() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    evidence_context = {"card_ids": ["card_1"], "cards": []}
    sufficiency_result = {"is_sufficient": False, "score": 0.5}

    updated = set_sufficiency_result(
        set_evidence_context(state, evidence_context),
        sufficiency_result,
    )
    evidence_context["card_ids"].append("card_2")

    assert updated["evidence_context"] == {"card_ids": ["card_1"], "cards": []}
    assert updated["sufficiency_result"] == sufficiency_result
    assert state.get("evidence_context") is None


def test_set_collect_context_returns_copy() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    collect_context = {"trip_spec": {"destination": "成都"}}

    updated = set_collect_context(state, collect_context)
    collect_context["trip_spec"]["destination"] = "重庆"

    assert updated["collect_context"] == {"trip_spec": {"destination": "成都"}}
    assert state.get("collect_context") is None


def test_set_planning_need_returns_copy() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    planning_need = {"confirmed_facts": [{"field": "destination", "value": "成都"}]}

    updated = set_planning_need(state, planning_need)
    planning_need["confirmed_facts"].append({"field": "travel_days", "value": 3})

    assert len(updated["planning_need"]["confirmed_facts"]) == 1
    assert state.get("planning_need") is None


def test_set_base_context_returns_copy() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    base_context = {"planning_need_summary": {"destination": "成都"}}

    updated = set_base_context(state, base_context)
    base_context["planning_need_summary"]["destination"] = "重庆"

    assert updated["base_context"] == {"planning_need_summary": {"destination": "成都"}}
    assert state.get("base_context") is None


def test_record_collect_waiting_sets_awaiting_user_without_mutating_input() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    updated = record_collect_waiting(state)

    assert updated["awaiting_user"] is True
    assert state.get("awaiting_user") is False


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
