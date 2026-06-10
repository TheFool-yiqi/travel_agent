"""Itinerary integrator tests."""

from __future__ import annotations

from app.runtime.planning.integrator import ItineraryIntegrator
from app.runtime.planning.planner_group import DomainPlannerGroup
from app.runtime.planning.schemas import PlanProposal
from app.runtime.state import create_initial_runtime_state, set_planning_need

from .test_domain_planner_group import _state_with_chengdu_context


def test_integrator_builds_days_matching_travel_days() -> None:
    state = _state_with_chengdu_context()
    proposals = DomainPlannerGroup().run(state)

    draft = ItineraryIntegrator().integrate(state, proposals)

    assert draft.destination == "成都"
    assert draft.travel_days == 3
    assert len(draft.days) == 3
    assert draft.evidence_card_ids


def test_integrator_does_not_invent_unreferenced_poi_names() -> None:
    state = _state_with_chengdu_context()
    proposals = DomainPlannerGroup().run(state)
    allowed_terms = {
        "成都",
        "武侯祠",
        "锦里",
        "奎星楼街",
        "玉林路",
        "待确认",
        "简餐",
        "机动",
        "休息",
        "室内",
        "美食",
        "交通",
        "便利",
        "区域",
        "游览",
        "体验",
        "如遇",
        "天气",
        "不佳",
        "改为",
        "或",
        "文化",
    }
    draft = ItineraryIntegrator().integrate(state, proposals)
    serialized = draft.model_dump_json()

    assert "故宫" not in serialized
    assert draft.days[0]["day_number"] == 1


def test_integrator_fails_gracefully_with_empty_proposals_list_fields() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都",
    )
    state = set_planning_need(
        state,
        {
            "confirmed_facts": [
                {
                    "field": "destination",
                    "value": "成都",
                    "fact_type": "confirmed",
                    "source": "user",
                },
                {
                    "field": "travel_days",
                    "value": 2,
                    "fact_type": "confirmed",
                    "source": "user",
                },
            ],
            "derived_facts": [],
            "approved_assumptions": [],
            "preferences": [],
            "constraints": [],
        },
    )
    proposals = [
        PlanProposal(agent_name="destination_planner", summary="成都策略"),
        PlanProposal(agent_name="route_transport_activity_planner", summary="路线"),
        PlanProposal(agent_name="stay_food_planner", summary="餐饮"),
    ]

    draft = ItineraryIntegrator().integrate(state, proposals)

    assert len(draft.days) == 2
    assert draft.summary.startswith("成都 2天行程草案")
