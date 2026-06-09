"""ContextAssembler visibility tests."""

from __future__ import annotations

import pytest

from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.assembler import ContextAssembler
from app.runtime.context.schemas import BaseContext
from app.runtime.state import (
    create_initial_runtime_state,
    set_base_context,
    set_collect_context,
    set_evidence_context,
    set_planning_need,
)


def _planning_need_dict() -> dict:
    planning_need = PlanningNeed(
        confirmed_facts=[
            PlanningFact(
                field="destination",
                value="成都",
                fact_type="confirmed",
                source="user",
            ),
        ],
        preferences=[{"field": "travel_styles", "value": ["food"]}],
        constraints=[{"field": "intensity", "value": "low"}],
    )
    return planning_need.to_runtime_dict()


def _base_context_dict() -> dict:
    return BaseContext(
        planning_need_summary={"destination": "成都", "travel_days": 3},
        session_facts=[{"field": "travel_style", "value": "低强度"}],
    ).to_runtime_dict()


def test_destination_planner_receives_planning_need_without_collect_context() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_collect_context(state, {"trip_spec": {"destination": "成都"}})
    state = set_planning_need(state, _planning_need_dict())
    state = set_base_context(state, _base_context_dict())

    agent_context = ContextAssembler().assemble("destination_planner", state)

    assert agent_context["agent_name"] == "destination_planner"
    assert agent_context["planning_need"]["confirmed_facts"][0]["value"] == "成都"
    assert agent_context["planning_need_summary"]["destination"] == "成都"
    assert "collect_context" not in agent_context
    assert "public_messages" not in agent_context


def _evidence_context_dict() -> dict:
    return {
        "card_ids": ["card_chengdu_route_1", "card_chengdu_food_1"],
        "cards": [
            {
                "id": "card_chengdu_route_1",
                "claim": "武侯祠和锦里距离较近，适合组合为半日文化游路线",
                "evidence_type": "route_relation",
                "city": "成都",
                "entities": ["武侯祠", "锦里"],
                "applies_to": ["第一次到访"],
                "time_hint": "半日",
                "intensity": "低",
                "confidence": 0.92,
                "status": "approved",
                "embedding_text": "hidden",
            },
        ],
        "query_summary": {"city": "成都"},
        "retrieval_trace": {
            "vector_ranked_ids": ["card_chengdu_route_1"],
            "bm25_ranked_ids": ["card_chengdu_food_1"],
            "fused_ids": ["card_chengdu_route_1"],
            "filters": {"city": "成都"},
        },
    }


def test_destination_planner_receives_evidence_card_summaries_without_retrieval_trace() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_collect_context(state, {"trip_spec": {"destination": "成都"}})
    state = set_planning_need(state, _planning_need_dict())
    state = set_base_context(state, _base_context_dict())
    state = set_evidence_context(state, _evidence_context_dict())

    agent_context = ContextAssembler().assemble("destination_planner", state)

    assert agent_context["evidence_cards"]["card_ids"] == [
        "card_chengdu_route_1",
        "card_chengdu_food_1",
    ]
    assert agent_context["evidence_cards"]["cards"][0]["claim"].startswith("武侯祠")
    assert "embedding_text" not in agent_context["evidence_cards"]["cards"][0]
    assert "retrieval_trace" not in agent_context
    assert "evidence_context" not in agent_context
    assert "collect_context" not in agent_context


def test_collect_agent_may_read_collect_context_only() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_collect_context(state, {"trip_spec": {"destination": "成都"}})
    state = set_planning_need(state, _planning_need_dict())

    agent_context = ContextAssembler().assemble("collect_agent", state)

    assert agent_context["collect_context"]["trip_spec"]["destination"] == "成都"
    assert "planning_need" not in agent_context
    assert "base_context" not in agent_context


def test_formal_planning_spec_rejects_unknown_agent() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )

    with pytest.raises(ValueError, match="Unknown context spec"):
        ContextAssembler().assemble("unknown_agent", state)


def test_agent_context_contains_no_prompt_like_keys() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(state, _planning_need_dict())
    state = set_base_context(state, _base_context_dict())

    agent_context = ContextAssembler().assemble("itinerary_integrator", state)

    serialized = str(agent_context).lower()
    assert "prompt" not in serialized
    assert "assembled_context" not in serialized
