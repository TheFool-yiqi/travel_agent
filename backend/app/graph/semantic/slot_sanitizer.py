"""槽位冲突清理（出发地 / 目的地误绑）。"""

from __future__ import annotations

from typing import Any

from app.graph.semantic.frame import SemanticFrame
from app.graph.templates.collect_guidance import next_guidance_step


def sanitize_departure_city_collision(
    fields: dict[str, Any],
    state: dict[str, Any],
    frame: SemanticFrame,
) -> dict[str, Any]:
    """清除将「目的地回答」误写入 departure_city 的情况。"""
    updated = dict(fields)
    dest = updated.get("destination")
    dep = updated.get("departure_city")
    if not dest or not dep:
        return updated

    # 用户在出发城市步骤明确输入（含同城游）
    if (
        frame.guidance_step == "departure_city"
        and frame.slot_updates.get("departure_city") == dep
    ):
        return updated

    should_clear = False

    if frame.slot_updates.get("destination") == dest and dep == dest:
        should_clear = True

    pending = state.get("pending_clarification") or {}
    if frame.pending_clarification_cleared and pending.get("slot") == "destination":
        original = pending.get("original", "")
        candidate = pending.get("candidate", "")
        if dep in (dest, original, candidate):
            should_clear = True

    if dep == dest and next_guidance_step({"destination": dest}) == "departure_city":
        # 尚未问到出发城市，不应已有与目的地相同的出发地
        should_clear = True

    if should_clear:
        updated.pop("departure_city", None)

    return updated


def fields_for_guidance_step(state: dict[str, Any]) -> dict[str, Any]:
    """从 graph state 提取引导步骤判断所需字段。"""
    return {
        "destination": state.get("destination"),
        "departure_city": state.get("departure_city"),
        "departure_date": state.get("departure_date") or state.get("start_date"),
        "travel_days": state.get("travel_days"),
        "adult_count": state.get("adult_count"),
        "children_count": state.get("children_count"),
        "party_confirmed": state.get("party_confirmed"),
        "budget_min": state.get("budget_min"),
        "budget_max": state.get("budget_max"),
    }
