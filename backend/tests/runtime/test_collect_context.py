import pytest
from pydantic import ValidationError

from app.runtime.collect.schemas import (
    CollectContext,
    PlanningFact,
    PlanningNeed,
    collect_context_from_runtime_dict,
    collect_context_to_runtime_dict,
)
from app.runtime.context.schemas import BaseContext
from app.runtime.state import (
    create_initial_runtime_state,
    set_base_context,
    set_collect_context,
    set_planning_need,
)


def test_collect_context_round_trip_through_runtime_state() -> None:
    context = CollectContext(
        trip_spec={"destination": "成都"},
        conversation_state={"turn": 1},
        discovery_state={"hypotheses": []},
        readiness_state={"status": "continue_collect"},
        pending_clarification={"slot": "travel_days"},
        rejected_assumptions=[{"field": "budget_max", "reason": "user_rejected"}],
    )

    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    updated = set_collect_context(state, collect_context_to_runtime_dict(context))
    restored = collect_context_from_runtime_dict(updated["collect_context"])

    assert restored == context


def test_planning_need_requires_fact_provenance() -> None:
    with pytest.raises(ValidationError, match="fact_type and source"):
        PlanningNeed(
            confirmed_facts=[{"field": "destination", "value": "成都"}],
        )


def test_planning_need_round_trip_through_runtime_state() -> None:
    planning_need = PlanningNeed(
        confirmed_facts=[
            PlanningFact(
                field="destination",
                value="成都",
                fact_type="confirmed",
                source="user",
            ),
        ],
        derived_facts=[
            PlanningFact(
                field="end_date",
                value="2026-07-05",
                fact_type="derived",
                source="rule",
            ),
        ],
        approved_assumptions=[
            PlanningFact(
                field="budget_max",
                value=5000,
                fact_type="approved_assumption",
                source="explicit_draft_request",
            ),
        ],
        missing_but_accepted_fields=["must_visit"],
        risk_flags=["evidence_may_be_insufficient"],
    )

    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    updated = set_planning_need(state, planning_need.to_runtime_dict())
    restored = PlanningNeed.from_runtime_dict(updated["planning_need"])

    assert restored == planning_need


def test_base_context_round_trip_through_runtime_state() -> None:
    base_context = BaseContext(
        planning_need_summary={"destination": "成都", "travel_days": 3},
        session_facts=[{"field": "travel_style", "value": "低强度"}],
        memory_snippets=[{"type": "preference", "text": "不吃辣"}],
        decision_snippets=[{"type": "prior_trip", "destination": "重庆"}],
    )

    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    updated = set_base_context(state, base_context.to_runtime_dict())
    restored = BaseContext.from_runtime_dict(updated["base_context"])

    assert restored == base_context
