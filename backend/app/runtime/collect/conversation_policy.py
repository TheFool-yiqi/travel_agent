"""Collect conversation reply policy."""

from __future__ import annotations

from typing import Any

from app.graph.nodes.collect_requirements import _confirmation_reply
from app.graph.templates.collect_followup import render_collect_followup
from app.runtime.collect.readiness import ReadinessStatus


def choose_public_reply(
    *,
    trip_spec: dict[str, Any],
    readiness_status: ReadinessStatus,
    dialogue_text: str,
    semantic_reply: str | None,
    validation_errors: list[str] | None = None,
) -> str:
    if semantic_reply:
        return semantic_reply

    if readiness_status == "ready_for_confirmation" and not validation_errors:
        return _confirmation_reply(trip_spec, dialogue_text=dialogue_text)

    return render_collect_followup(trip_spec, dialogue_text=dialogue_text)
