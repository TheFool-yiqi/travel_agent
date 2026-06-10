"""Default chat path dispatch tests."""

from __future__ import annotations

import pytest

from app.services import chat_stream


@pytest.mark.asyncio
async def test_iter_chat_events_dispatches_to_runtime(monkeypatch) -> None:
    calls: list[str] = []

    async def _runtime(*_args, **_kwargs):
        calls.append("runtime")
        yield {"type": "done"}

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
