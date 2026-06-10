"""Map internal RuntimeEvents to the existing frontend SSE/WS contract."""

from __future__ import annotations

from typing import Any

from app.runtime.events import RuntimeEvent
from app.runtime.streaming.stage_labels import stage_label

_DEFAULT_APPROVAL_MESSAGE = "请确认行程或提出修改意见"


def adapt_runtime_event_to_frontend_events(event: RuntimeEvent) -> list[dict[str, Any]]:
    """Convert one RuntimeEvent into zero or more frontend transport dicts."""
    if event.visibility != "public":
        return []

    if event.type == "stage_started":
        if event.stage is None:
            return []
        return [
            {
                "type": "step",
                "step": event.stage,
                "label": stage_label(event.stage),
            },
        ]

    if event.type == "stage_completed":
        return _adapt_stage_completed(event)

    if event.type == "runtime_completed":
        return [{"type": "done"}]

    if event.type == "runtime_failed":
        error = event.payload.get("error") or {}
        message = str(error.get("message") or "规划运行失败")
        return [{"type": "error", "message": message}]

    return []


def _adapt_stage_completed(event: RuntimeEvent) -> list[dict[str, Any]]:
    output = event.payload.get("output")
    if not isinstance(output, dict):
        return []

    events: list[dict[str, Any]] = []
    stage = event.stage
    data = output.get("data")
    if not isinstance(data, dict):
        data = {}

    if stage == "integrate":
        draft = data.get("itinerary_draft")
        if isinstance(draft, dict):
            events.append(_itinerary_event_from_draft(draft))

    if stage == "approve_or_revise" and output.get("status") == "waiting":
        pending = data.get("pending_approval")
        message = _DEFAULT_APPROVAL_MESSAGE
        if isinstance(pending, dict):
            prompt = pending.get("public_prompt")
            if isinstance(prompt, str) and prompt.strip():
                message = prompt.strip()
        events.append({"type": "approval_required", "message": message})

    if stage == "finalize":
        order_id = data.get("order_id")
        if isinstance(order_id, str) and order_id.strip():
            events.append({"type": "order", "order_id": order_id.strip()})

    public_reply = _extract_public_reply(output)
    if public_reply:
        events.append({"type": "token", "content": public_reply})

    return events


def _extract_public_reply(output: dict[str, Any]) -> str | None:
    data = output.get("data")
    if isinstance(data, dict):
        reply = data.get("public_reply")
        if isinstance(reply, str) and reply.strip():
            return reply.strip()

    reply = output.get("public_reply")
    if isinstance(reply, str) and reply.strip():
        return reply.strip()
    return None


def _itinerary_event_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    days = draft.get("days")
    budget = draft.get("budget")
    return {
        "type": "itinerary",
        "itinerary": days if isinstance(days, list) else [],
        "budget": budget if isinstance(budget, dict) else None,
    }
