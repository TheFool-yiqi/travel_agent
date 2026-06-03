"""chat_stream service tests."""

from __future__ import annotations

import asyncio
import inspect
import json
from typing import Any

from langchain_core.messages import AIMessage

from app.services.chat_stream import (
    _assistant_text_from_node_output,
    _should_emit_node_reply,
    iter_chat_events,
    sse,
)


async def _collect_multiplexed(graph_events, token_queue):
    from app.services.chat_stream import _iter_graph_events_and_tokens

    items: list[tuple[str, Any]] = []
    async for item in _iter_graph_events_and_tokens(graph_events, token_queue):
        items.append(item)
    return items


async def test_iter_graph_events_and_tokens_drains_during_node() -> None:
    """Tokens queued while graph awaits should be yielded before the next event."""

    async def _graph_events():
        await asyncio.sleep(0.05)
        yield {"event": "on_chain_end", "name": "build_itinerary", "data": {"output": {}}}
        await asyncio.sleep(0.05)

    token_queue: asyncio.Queue[str] = asyncio.Queue()

    async def _enqueue_tokens() -> None:
        await asyncio.sleep(0.01)
        await token_queue.put("Day")
        await token_queue.put(" 1")

    producer = asyncio.create_task(_enqueue_tokens())
    items = await _collect_multiplexed(_graph_events(), token_queue)
    await producer

    assert ("token", "Day") in items
    assert ("token", " 1") in items
    token_index = items.index(("token", "Day"))
    event_index = items.index(("event", {"event": "on_chain_end", "name": "build_itinerary", "data": {"output": {}}}))
    assert token_index < event_index


def test_should_emit_node_reply() -> None:
    assert _should_emit_node_reply(node_streamed_tokens=False, reply_text="行程已生成")
    assert not _should_emit_node_reply(node_streamed_tokens=True, reply_text="行程已生成")
    assert not _should_emit_node_reply(node_streamed_tokens=False, reply_text=None)
    assert not _should_emit_node_reply(node_streamed_tokens=False, reply_text="")
    assert not _should_emit_node_reply(
        node_streamed_tokens=False,
        reply_text="上海出发",
        assistant_message="好的，上海出发，请问出行天数？",
    )
    assert not _should_emit_node_reply(
        node_streamed_tokens=False,
        reply_text="上海出发",
        assistant_message="已确认上海出发",
    )


def test_sse_format() -> None:
    frame = sse({"type": "token", "content": "你好"})
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    payload = json.loads(frame.removeprefix("data: ").strip())
    assert payload["content"] == "你好"


def test_iter_chat_events_is_async_generator() -> None:
    assert hasattr(iter_chat_events, "__call__")


def test_iter_chat_events_does_not_handle_langgraph_model_stream() -> None:
    """Avoid duplicate tokens: invoke_step_llm uses emit_stream_token queue only."""
    source = inspect.getsource(iter_chat_events)
    assert 'if kind == "on_chat_model_stream"' not in source


def test_assistant_text_from_node_output() -> None:
    text = _assistant_text_from_node_output(
        {"messages": [AIMessage(content="你好，请告诉我出发城市。")]},
    )
    assert text == "你好，请告诉我出发城市。"


def test_assistant_text_from_node_output_uses_last_ai_only() -> None:
    text = _assistant_text_from_node_output(
        {
            "messages": [
                AIMessage(content="旧回复"),
                AIMessage(content="新回复"),
            ],
        },
    )
    assert text == "新回复"


def test_next_unique_token_skips_duplicate_greeting() -> None:
    from app.graph.greeting import GREETING_REPLY
    from app.services.chat_stream import _next_unique_token

    assert _next_unique_token(GREETING_REPLY, GREETING_REPLY) is None
    assert _next_unique_token(GREETING_REPLY, f"\n\n{GREETING_REPLY}") is None
    assert _next_unique_token("", GREETING_REPLY) == GREETING_REPLY


def test_sse_step_and_itinerary() -> None:
    step_frame = sse({"type": "step", "step": "plan_destination", "label": "目的地"})
    step_payload = json.loads(step_frame.removeprefix("data: ").strip())
    assert step_payload == {"type": "step", "step": "plan_destination", "label": "目的地"}

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
