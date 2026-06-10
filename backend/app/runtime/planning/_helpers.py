"""Shared helpers for domain planners."""

from __future__ import annotations

from typing import Any

from app.runtime.collect.schemas import PlanningNeed
from app.runtime.context.assembler import ContextAssembler
from app.runtime.state import RuntimeState


def assemble_agent_context(agent_name: str, state: RuntimeState) -> dict[str, Any]:
    return ContextAssembler().assemble(agent_name, state)


def load_planning_need(state: RuntimeState) -> PlanningNeed | None:
    raw = state.get("planning_need")
    if not raw:
        return None
    return PlanningNeed.from_runtime_dict(raw)


def destination_from_state(state: RuntimeState) -> str | None:
    need = load_planning_need(state)
    if need is None:
        return None
    for fact in (
        *need.confirmed_facts,
        *need.derived_facts,
        *need.approved_assumptions,
    ):
        if fact.field == "destination" and isinstance(fact.value, str):
            value = fact.value.strip()
            if value:
                return value
    base = state.get("base_context") or {}
    summary = base.get("planning_need_summary") or {}
    destination = summary.get("destination")
    if isinstance(destination, str) and destination.strip():
        return destination.strip()
    return None


def travel_days_from_state(state: RuntimeState) -> int:
    need = load_planning_need(state)
    if need is None:
        return 1
    for fact in (
        *need.confirmed_facts,
        *need.derived_facts,
        *need.approved_assumptions,
    ):
        if fact.field == "travel_days":
            try:
                days = int(fact.value)
                return max(days, 1)
            except (TypeError, ValueError):
                continue
    base = state.get("base_context") or {}
    summary = base.get("planning_need_summary") or {}
    try:
        return max(int(summary.get("travel_days") or 1), 1)
    except (TypeError, ValueError):
        return 1


def evidence_cards_from_context(agent_context: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = agent_context.get("evidence_cards") or {}
    cards = evidence.get("cards") or []
    return [card for card in cards if isinstance(card, dict)]


def evidence_card_ids(cards: list[dict[str, Any]]) -> list[str]:
    return [str(card["id"]) for card in cards if card.get("id")]


def cards_by_type(cards: list[dict[str, Any]], evidence_type: str) -> list[dict[str, Any]]:
    return [card for card in cards if card.get("evidence_type") == evidence_type]


def weather_risks_from_context(agent_context: dict[str, Any]) -> list[str]:
    weather = agent_context.get("weather_summary") or {}
    risks = weather.get("risks") or []
    if isinstance(risks, list):
        return [str(item) for item in risks if str(item).strip()]
    return []


def sufficiency_assumptions(state: RuntimeState) -> list[str]:
    sufficiency = state.get("sufficiency_result") or {}
    if sufficiency.get("is_sufficient") is False:
        missing_types = sufficiency.get("missing_evidence_types") or []
        if missing_types:
            return [
                f"证据类型 {', '.join(missing_types)} 未覆盖，相关安排需标记为假设",
            ]
    return []
