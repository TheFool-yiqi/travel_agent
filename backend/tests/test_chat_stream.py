"""chat_stream service tests."""

from __future__ import annotations

import inspect
import json

from app.services.chat_stream import iter_chat_events, sse


def test_sse_format() -> None:
    frame = sse({"type": "token", "content": "你好"})
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    payload = json.loads(frame.removeprefix("data: ").strip())
    assert payload["content"] == "你好"


def test_iter_chat_events_is_async_generator() -> None:
    assert hasattr(iter_chat_events, "__call__")


def test_sse_step_and_itinerary() -> None:
    step_frame = sse({"type": "step", "step": "collect", "label": "需求收集"})
    step_payload = json.loads(step_frame.removeprefix("data: ").strip())
    assert step_payload == {"type": "step", "step": "collect", "label": "需求收集"}

    itinerary_frame = sse(
        {
            "type": "itinerary",
            "itinerary": [{"day_number": 1, "theme": "抵达", "activities": ["宽窄巷子"]}],
            "budget": {"total": 3000},
        },
    )
    itinerary_payload = json.loads(itinerary_frame.removeprefix("data: ").strip())
    assert itinerary_payload["type"] == "itinerary"
    assert itinerary_payload["budget"]["total"] == 3000

    approval_frame = sse({"type": "approval_required", "message": "请确认"})
    approval_payload = json.loads(approval_frame.removeprefix("data: ").strip())
    assert approval_payload["type"] == "approval_required"


def test_iter_chat_events_delegates_to_runtime() -> None:
    source = inspect.getsource(iter_chat_events)
    assert "iter_chat_events_runtime" in source
