"""Build retrieval queries from validated planning inputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.schemas import BaseContext

DEFAULT_REQUIRED_EVIDENCE_TYPES: tuple[str, ...] = (
    "route_relation",
    "time_intensity",
    "food_option",
    "area_strategy",
)


class RetrievalQuery(BaseModel):
    city: str | None = None
    duration: int | None = None
    must_visit: list[str] = Field(default_factory=list)
    preferences: list[str] = Field(default_factory=list)
    required_evidence_types: list[str] = Field(
        default_factory=lambda: list(DEFAULT_REQUIRED_EVIDENCE_TYPES),
    )
    search_text: str = ""


def build_retrieval_query(
    planning_need: PlanningNeed,
    base_context: BaseContext | None = None,
) -> RetrievalQuery:
    """Derive retrieval filters from PlanningNeed and optional BaseContext."""
    summary = dict(base_context.planning_need_summary) if base_context else {}
    facts = (
        *planning_need.confirmed_facts,
        *planning_need.derived_facts,
        *planning_need.approved_assumptions,
    )

    city = _fact_value(facts, "destination") or summary.get("destination")
    if isinstance(city, str):
        city = city.strip() or None
    else:
        city = None

    duration = _fact_value(facts, "travel_days") or summary.get("travel_days")
    if duration is not None:
        try:
            duration = int(duration)
        except (TypeError, ValueError):
            duration = None

    must_visit = _collect_string_tags(facts, field_names=("must_visit", "destination"))
    preferences = _collect_preference_tags(planning_need, summary)
    search_text = _build_search_text(city=city, duration=duration, preferences=preferences, must_visit=must_visit)

    return RetrievalQuery(
        city=city,
        duration=duration,
        must_visit=must_visit,
        preferences=preferences,
        required_evidence_types=list(DEFAULT_REQUIRED_EVIDENCE_TYPES),
        search_text=search_text,
    )


def _fact_value(facts: tuple[PlanningFact, ...], field: str) -> Any:
    for fact in facts:
        if fact.field == field:
            return fact.value
    return None


def _collect_string_tags(
    facts: tuple[PlanningFact, ...],
    *,
    field_names: tuple[str, ...],
) -> list[str]:
    tags: list[str] = []
    for fact in facts:
        if fact.field not in field_names:
            continue
        value = fact.value
        if isinstance(value, str) and value.strip():
            tags.append(value.strip())
        elif isinstance(value, list):
            tags.extend(str(item).strip() for item in value if str(item).strip())
    return tags


def _collect_preference_tags(
    planning_need: PlanningNeed,
    summary: dict[str, Any],
) -> list[str]:
    tags: list[str] = []
    for item in planning_need.preferences:
        value = item.get("value")
        if isinstance(value, str) and value.strip():
            tags.append(value.strip())
        elif isinstance(value, list):
            tags.extend(str(part).strip() for part in value if str(part).strip())
    summary_preferences = summary.get("preferences")
    if isinstance(summary_preferences, list):
        for item in summary_preferences:
            if isinstance(item, dict):
                value = item.get("value")
                if isinstance(value, str) and value.strip():
                    tags.append(value.strip())
                elif isinstance(value, list):
                    tags.extend(str(part).strip() for part in value if str(part).strip())
    return list(dict.fromkeys(tags))


def _build_search_text(
    *,
    city: str | None,
    duration: int | None,
    preferences: list[str],
    must_visit: list[str],
) -> str:
    parts: list[str] = []
    if city:
        parts.append(f"城市：{city}")
    if duration is not None:
        parts.append(f"{duration}天")
    if must_visit:
        parts.append("必去：" + " ".join(must_visit))
    if preferences:
        parts.append("偏好：" + " ".join(preferences))
    return " ".join(parts).strip()
