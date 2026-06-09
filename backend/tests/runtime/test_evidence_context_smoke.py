"""Slice 4 evidence retrieval integration smoke tests."""

from __future__ import annotations

import pytest

from app.runtime.context.assembler import ContextAssembler
from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.stages.prepare_base_context import PrepareBaseContextStageHandler
from app.runtime.stages.retrieve_evidence import RetrieveEvidenceStageHandler
from app.runtime.state import RuntimeState, set_planning_need

from .test_collect_context_smoke import _COLLECT_TURN_SEQUENCE, _run_collect_sequence


@pytest.mark.asyncio
async def test_collect_ready_state_retrieves_evidence_context_and_sufficiency() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    assert ready_turn.status == "ready"
    assert ready_turn.planning_need is not None

    state = set_planning_need(state, ready_turn.planning_need)
    base_result = await PrepareBaseContextStageHandler().handle(state)
    assert base_result["status"] == "completed"

    state = RuntimeState(**base_result["data"]["state"])
    retrieve_result = await RetrieveEvidenceStageHandler().handle(state)

    assert retrieve_result["status"] == "completed"
    evidence_context = retrieve_result["data"]["evidence_context"]
    sufficiency_result = retrieve_result["data"]["sufficiency_result"]

    assert evidence_context["card_ids"]
    assert all(card["status"] == "approved" for card in evidence_context["cards"])
    assert sufficiency_result["suggested_action"] == "mark_assumptions_and_continue"
    assert sufficiency_result["is_sufficient"] is False
    assert "area_strategy" in sufficiency_result["missing_evidence_types"]


@pytest.mark.asyncio
async def test_collect_ready_path_runs_through_retrieve_evidence_and_completes_runtime() -> None:
    state, ready_turn = await _run_collect_sequence(_COLLECT_TURN_SEQUENCE)
    assert ready_turn.status == "ready"

    state = set_planning_need(state, ready_turn.planning_need)
    state = RuntimeState(**{**state, "input_message": "确认"})

    events = [event async for event in PlanningRuntime(build_default_stage_handlers()).run(state)]

    started = [event.stage for event in events if event.type == "stage_started"]
    assert started == list(V1_STAGE_NAMES)
    assert events[-1].type == "runtime_completed"

    retrieve_completed = next(
        event
        for event in events
        if event.type == "stage_completed" and event.stage == "retrieve_evidence"
    )
    output = retrieve_completed.payload["output"]
    assert output["status"] == "completed"
    assert output["data"]["evidence_context"]["card_ids"]
    assert output["data"]["sufficiency_result"]["suggested_action"] == "mark_assumptions_and_continue"

    agent_context = ContextAssembler().assemble(
        "destination_planner",
        RuntimeState(**output["data"]["state"]),
    )
    assert agent_context["evidence_cards"]["card_ids"]
    assert "retrieval_trace" not in agent_context
    assert "collect_context" not in agent_context
