"""需求收集分步引导顺序（引导一次一项，提取可并行）"""

from __future__ import annotations

from typing import Any, Literal

GuidanceStep = Literal[
    "destination",
    "departure_city",
    "departure_date",
    "travel_days",
    "party",
    "budget",
    "done",
]


def next_guidance_step(fields: dict[str, Any]) -> GuidanceStep:
    """返回下一项应引导用户提供的字段。"""
    from app.graph.templates.budget_tiers import is_party_confirmed

    if not fields.get("destination"):
        return "destination"
    if not fields.get("departure_city"):
        return "departure_city"
    if not fields.get("departure_date"):
        return "departure_date"
    if not fields.get("travel_days"):
        return "travel_days"
    if not is_party_confirmed(fields):
        return "party"
    if fields.get("budget_min") is None or fields.get("budget_max") is None:
        return "budget"
    return "done"


def needs_guidance_followup(fields: dict[str, Any], *, awaiting_confirmation: bool = False) -> bool:
    if awaiting_confirmation:
        return False
    return next_guidance_step(fields) != "done"
