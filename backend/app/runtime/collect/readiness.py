"""Collect readiness evaluation."""

from __future__ import annotations

from typing import Any, Literal

from app.graph.nodes.collect_requirements import (
    can_advance_to_planning,
    is_requirement_complete,
)

ReadinessStatus = Literal[
    "continue_collect",
    "ready_for_confirmation",
    "ready_for_planning",
]


def evaluate_readiness(
    trip_spec: dict[str, Any],
    *,
    user_confirmed: bool,
    dialogue_text: str = "",
    has_unconfirmed_discovery: bool = False,
) -> tuple[ReadinessStatus, dict[str, Any]]:
    """Mirror collect_requirements completeness gates for Runtime collect."""
    if has_unconfirmed_discovery:
        return "continue_collect", {"reason": "unconfirmed_discovery"}

    if can_advance_to_planning(
        trip_spec,
        user_confirmed=user_confirmed,
        dialogue_text=dialogue_text,
    ):
        return "ready_for_planning", {}

    if is_requirement_complete(trip_spec):
        return "ready_for_confirmation", {}

    return "continue_collect", {}
