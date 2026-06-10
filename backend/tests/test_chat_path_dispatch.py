"""Default chat path dispatch tests."""

from __future__ import annotations

import inspect

import pytest

from app.services import chat_stream


@pytest.mark.asyncio
async def test_iter_chat_events_dispatches_to_runtime_by_default(monkeypatch) -> None:
    calls: list[str] = []

    async def _runtime(*_args, **_kwargs):
        calls.append("runtime")
        yield {"type": "done"}

    async def _graph(*_args, **_kwargs):
        calls.append("graph")
        yield {"type": "done"}

    monkeypatch.setattr(chat_stream.settings, "chat_planner_backend", "runtime")
    monkeypatch.setattr(
        "app.services.runtime_chat_service.iter_chat_events_runtime",
        _runtime,
    )

    events = [
        event
        async for event in chat_stream.iter_chat_events(
            conversation_id=__import__("uuid").uuid4(),
            user_message="你好",
            user=object(),
        )
    ]

    assert calls == ["runtime"]
    assert events == [{"type": "done"}]


@pytest.mark.asyncio
async def test_iter_chat_events_can_use_legacy_graph_backend(monkeypatch) -> None:
    calls: list[str] = []

    async def _graph(*_args, **_kwargs):
        calls.append("graph")
        yield {"type": "done"}

    monkeypatch.setattr(chat_stream.settings, "chat_planner_backend", "graph")
    monkeypatch.setattr(chat_stream, "iter_chat_events_graph", _graph)

    events = [
        event
        async for event in chat_stream.iter_chat_events(
            conversation_id=__import__("uuid").uuid4(),
            user_message="你好",
            user=object(),
        )
    ]

    assert calls == ["graph"]
    assert events == [{"type": "done"}]


def test_iter_chat_events_graph_exported_for_compatibility() -> None:
    assert inspect.isasyncgenfunction(chat_stream.iter_chat_events_graph)
