"""Runtime ToolService for allowlisted tool enrichment."""

from __future__ import annotations

from typing import Any

from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.schemas import BaseContext
from app.runtime.tools.schemas import ToolContext, ToolWarning
from app.runtime.tools.weather_adapter import WeatherToolAdapter


class ToolService:
    """Unified Runtime entry for V1 allowlisted tools."""

    def __init__(self, *, weather_adapter: WeatherToolAdapter | None = None) -> None:
        self._weather_adapter = weather_adapter or WeatherToolAdapter()

    def enrich(
        self,
        planning_need: dict[str, Any],
        base_context: dict[str, Any] | None = None,
    ) -> ToolContext:
        need = PlanningNeed.from_runtime_dict(planning_need)
        context = (
            BaseContext.from_runtime_dict(base_context)
            if base_context
            else None
        )
        destination = _resolve_destination(need, context)
        date_range = _resolve_date_range(need, context)

        weather, warnings = self._weather_adapter.fetch_forecast(
            destination or "",
            date_range=date_range,
        )
        return ToolContext(weather=weather, tool_warnings=warnings)


def _resolve_destination(
    planning_need: PlanningNeed,
    base_context: BaseContext | None,
) -> str | None:
    summary = dict(base_context.planning_need_summary) if base_context else {}
    facts = (
        *planning_need.confirmed_facts,
        *planning_need.derived_facts,
        *planning_need.approved_assumptions,
    )
    destination = _fact_value(facts, "destination") or summary.get("destination")
    if isinstance(destination, str):
        destination = destination.strip()
        return destination or None
    return None


def _resolve_date_range(
    planning_need: PlanningNeed,
    base_context: BaseContext | None,
) -> str | None:
    summary = dict(base_context.planning_need_summary) if base_context else {}
    facts = (
        *planning_need.confirmed_facts,
        *planning_need.derived_facts,
        *planning_need.approved_assumptions,
    )
    start_date = (
        _fact_value(facts, "departure_date")
        or _fact_value(facts, "start_date")
        or summary.get("departure_date")
        or summary.get("start_date")
    )
    travel_days = _fact_value(facts, "travel_days") or summary.get("travel_days")
    if start_date and travel_days is not None:
        return f"{start_date} ~ {travel_days}天"
    if start_date:
        return str(start_date)
    return None


def _fact_value(facts: tuple[PlanningFact, ...], field: str) -> Any:
    for fact in facts:
        if fact.field == field:
            return fact.value
    return None
