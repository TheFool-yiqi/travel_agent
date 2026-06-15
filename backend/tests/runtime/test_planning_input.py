"""PlanningNeed compilation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.runtime.collect.planning_input import (
    compile_planning_need,
    detect_user_confirmed,
    validate_planning_input,
)
from app.runtime.collect.schemas import PlanningNeed


def test_detect_user_confirmed_accepts_dui_de() -> None:
    assert detect_user_confirmed(user_message="对的", conversation_state={})


def test_compile_planning_need_only_uses_trip_spec_values() -> None:
    trip_spec = {
        "destination": "成都",
        "departure_city": "北京",
        "departure_date": "2026-07-01",
        "travel_days": 3,
        "adult_count": 2,
        "children_count": 0,
        "budget_min": 1000.0,
        "budget_max": 3000.0,
    }

    planning_need = compile_planning_need(
        trip_spec,
        user_confirmed=True,
        explicit_draft_request=False,
    )

    assert {fact.field for fact in planning_need.confirmed_facts} >= {
        "destination",
        "departure_city",
        "departure_date",
    }
    assert all(fact.fact_type and fact.source for fact in planning_need.confirmed_facts)


def test_compile_planning_need_records_explicit_draft_request() -> None:
    trip_spec = {
        "destination": "成都",
        "departure_city": "北京",
        "departure_date": "2026-07-01",
        "travel_days": 3,
        "adult_count": 2,
        "children_count": 0,
        "budget_min": 1000.0,
        "budget_max": 3000.0,
    }

    planning_need = compile_planning_need(
        trip_spec,
        user_confirmed=False,
        explicit_draft_request=True,
    )

    assert "explicit_draft_request" in planning_need.risk_flags
    assert planning_need.approved_assumptions


def test_validate_planning_input_rejects_missing_required_fields() -> None:
    errors = validate_planning_input({"destination": "成都"})
    assert errors


def test_planning_need_rejects_fact_without_provenance() -> None:
    with pytest.raises(ValidationError):
        PlanningNeed(confirmed_facts=[{"field": "destination", "value": "成都"}])
