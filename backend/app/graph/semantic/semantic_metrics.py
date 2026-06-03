"""语义理解质量指标（槽位命中率、澄清轮次等）。"""

from __future__ import annotations

from typing import Any

from app.graph.semantic.frame import SemanticFrame


def build_turn_metrics(
    frame: SemanticFrame,
    *,
    requirements_complete: bool = False,
    had_pending_before: bool = False,
) -> dict[str, Any]:
    """单轮语义指标，写入 semantic trace。"""
    slot_filled = bool(frame.slot_updates)
    clarification_asked = frame.pending_clarification is not None
    clarification_resolved = (
        frame.pending_clarification_cleared and slot_filled and had_pending_before
    )
    user_correction = any(c.reason == "user_correction" for c in frame.corrections)
    first_hit = slot_filled and not clarification_asked and not had_pending_before

    return {
        "slot_filled": slot_filled,
        "first_hit": first_hit,
        "clarification_asked": clarification_asked,
        "clarification_resolved": clarification_resolved,
        "user_correction": user_correction,
        "planning_reached": requirements_complete,
        "guidance_step": frame.guidance_step,
    }


def aggregate_session_metrics(traces: list[dict[str, Any]]) -> dict[str, Any]:
    """从会话内多条 assistant semantic trace 聚合指标。"""
    if not traces:
        return {
            "turns": 0,
            "slot_filled_turns": 0,
            "first_hit_turns": 0,
            "clarification_turns": 0,
            "clarification_resolved_turns": 0,
            "user_correction_turns": 0,
            "first_hit_rate": 0.0,
            "clarification_rate": 0.0,
            "planning_reached": False,
        }

    turns = len(traces)
    slot_filled = sum(1 for t in traces if t.get("metrics", {}).get("slot_filled"))
    first_hit = sum(1 for t in traces if t.get("metrics", {}).get("first_hit"))
    clarification = sum(1 for t in traces if t.get("metrics", {}).get("clarification_asked"))
    resolved = sum(1 for t in traces if t.get("metrics", {}).get("clarification_resolved"))
    corrections = sum(1 for t in traces if t.get("metrics", {}).get("user_correction"))
    planning = any(t.get("metrics", {}).get("planning_reached") for t in traces)

    return {
        "turns": turns,
        "slot_filled_turns": slot_filled,
        "first_hit_turns": first_hit,
        "clarification_turns": clarification,
        "clarification_resolved_turns": resolved,
        "user_correction_turns": corrections,
        "first_hit_rate": round(first_hit / turns, 4) if turns else 0.0,
        "clarification_rate": round(clarification / turns, 4) if turns else 0.0,
        "planning_reached": planning,
    }


def extract_traces_from_messages(messages: list[Any]) -> list[dict[str, Any]]:
    """从 ORM Message 列表提取 semantic traces。"""
    traces: list[dict[str, Any]] = []
    for message in messages:
        extra = getattr(message, "extra_info", None) or {}
        semantic = extra.get("semantic")
        if isinstance(semantic, dict):
            traces.append(semantic)
    return traces
