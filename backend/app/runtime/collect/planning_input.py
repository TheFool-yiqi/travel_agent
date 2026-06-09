"""PlanningNeed compilation and validation."""

from __future__ import annotations

import re
from typing import Any

from app.graph.validators.requirements import validate_requirements
from app.runtime.collect.schemas import PlanningFact, PlanningNeed

_CONFIRM_PATTERN = re.compile(
    r"^(对|是的?|嗯|没错|是|好|确认|可以|没问题|ok|OK)[!.?？\s]*$",
    re.IGNORECASE,
)
_DRAFT_REQUEST_PATTERN = re.compile(
    r"(先给我|先出|先来)一版|先规划|先看看方案",
)


def detect_user_confirmed(*, user_message: str, conversation_state: dict[str, Any]) -> bool:
    if conversation_state.get("user_confirmed"):
        return True
    return bool(_CONFIRM_PATTERN.match(user_message.strip()))


def detect_explicit_draft_request(user_message: str) -> bool:
    return bool(_DRAFT_REQUEST_PATTERN.search(user_message))


def validate_planning_input(
    trip_spec: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> list[str]:
    return validate_requirements(trip_spec, dialogue_text=dialogue_text)


def compile_planning_need(
    trip_spec: dict[str, Any],
    *,
    user_confirmed: bool,
    explicit_draft_request: bool,
) -> PlanningNeed:
    """Compile only structured trip-spec facts; never invent missing values."""
    confirmed_fields = (
        "destination",
        "departure_city",
        "departure_date",
        "travel_days",
        "adult_count",
        "children_count",
        "budget_min",
        "budget_max",
        "travel_styles",
        "special_needs",
    )
    confirmed_facts: list[PlanningFact] = []
    for field in confirmed_fields:
        value = trip_spec.get(field)
        if value is None or value == "" or value == []:
            continue
        confirmed_facts.append(
            PlanningFact(
                field=field,
                value=value,
                fact_type="confirmed",
                source="user",
            ),
        )

    derived_facts: list[PlanningFact] = []
    if trip_spec.get("start_date") and trip_spec.get("departure_date") is None:
        derived_facts.append(
            PlanningFact(
                field="departure_date",
                value=trip_spec["start_date"],
                fact_type="derived",
                source="rule",
            ),
        )

    approved_assumptions: list[PlanningFact] = []
    missing_but_accepted: list[str] = []
    risk_flags: list[str] = []

    if explicit_draft_request:
        risk_flags.append("explicit_draft_request")
        for field in ("must_visit", "avoid", "intensity_preference"):
            if trip_spec.get(field) in (None, "", []):
                missing_but_accepted.append(field)

    if not user_confirmed and explicit_draft_request:
        approved_assumptions.append(
            PlanningFact(
                field="planning_mode",
                value="draft_without_full_confirmation",
                fact_type="approved_assumption",
                source="explicit_draft_request",
            ),
        )

    return PlanningNeed(
        confirmed_facts=confirmed_facts,
        derived_facts=derived_facts,
        approved_assumptions=approved_assumptions,
        constraints=list(trip_spec.get("constraints") or []),
        preferences=[
            item
            for item in (
                {"field": "travel_styles", "value": trip_spec.get("travel_styles")}
                if trip_spec.get("travel_styles")
                else None,
                {"field": "special_needs", "value": trip_spec.get("special_needs")}
                if trip_spec.get("special_needs")
                else None,
            )
            if item is not None
        ],
        missing_but_accepted_fields=missing_but_accepted,
        risk_flags=risk_flags,
    )
