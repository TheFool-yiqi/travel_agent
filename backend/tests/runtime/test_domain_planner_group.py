"""Domain planner group tests."""

from __future__ import annotations

from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.schemas import BaseContext
from app.runtime.planning.planner_group import DomainPlannerGroup
from app.runtime.state import (
    create_initial_runtime_state,
    set_base_context,
    set_evidence_context,
    set_planning_need,
    set_sufficiency_result,
)


def _state_with_chengdu_context() -> dict:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    planning_need = PlanningNeed(
        confirmed_facts=[
            PlanningFact(
                field="destination",
                value="成都",
                fact_type="confirmed",
                source="user",
            ),
            PlanningFact(
                field="travel_days",
                value=3,
                fact_type="confirmed",
                source="user",
            ),
        ],
    )
    state = set_planning_need(state, planning_need.to_runtime_dict())
    state = set_base_context(
        state,
        BaseContext(
            planning_need_summary={"destination": "成都", "travel_days": 3},
        ).to_runtime_dict(),
    )
    state = set_evidence_context(
        state,
        {
            "card_ids": ["card_chengdu_route_1", "card_chengdu_food_1"],
            "cards": [
                {
                    "id": "card_chengdu_route_1",
                    "claim": "武侯祠和锦里适合组合为半日文化游",
                    "evidence_type": "route_relation",
                    "city": "成都",
                    "entities": ["武侯祠", "锦里"],
                },
                {
                    "id": "card_chengdu_food_1",
                    "claim": "奎星楼街和玉林路适合美食探索",
                    "evidence_type": "food_option",
                    "city": "成都",
                    "entities": ["奎星楼街", "玉林路"],
                },
            ],
        },
    )
    state = set_sufficiency_result(
        state,
        {
            "is_sufficient": False,
            "score": 0.5,
            "missing_evidence_types": ["area_strategy"],
            "suggested_action": "mark_assumptions_and_continue",
        },
    )
    return state


def test_domain_planner_group_runs_destination_first_and_returns_three_proposals() -> None:
    proposals = DomainPlannerGroup().run(_state_with_chengdu_context())

    assert [proposal.agent_name for proposal in proposals] == [
        "destination_planner",
        "route_transport_activity_planner",
        "stay_food_planner",
    ]
    assert proposals[0].detail["destination"] == "成都"
    assert proposals[0].evidence_card_ids
    assert any("area_strategy" in item for item in proposals[0].assumptions)


def test_route_planner_includes_evidence_backed_activity_sequence() -> None:
    proposals = DomainPlannerGroup().run(_state_with_chengdu_context())
    route = proposals[1]

    assert route.detail["activity_sequence"]
    assert "card_chengdu_route_1" in route.evidence_card_ids
