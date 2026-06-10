"""Runtime frontend transport integration tests."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import pytest

from app.runtime.events import (
    RuntimeEvent,
    make_runtime_completed_event,
    make_stage_completed_event,
    make_stage_started_event,
)
from app.services.runtime_chat_stream import iter_frontend_transport_events


@pytest.mark.asyncio
async def test_iter_frontend_transport_events_multiplexes_tokens_and_events() -> None:
    async def events() -> AsyncIterator[RuntimeEvent]:
        yield make_stage_started_event(run_id="run_1", stage="collect")
        yield make_stage_completed_event(
            run_id="run_1",
            stage="collect",
            output={
                "status": "waiting",
                "data": {"public_reply": "请问出发城市？"},
            },
        )
        yield make_runtime_completed_event(run_id="run_1")

    token_queue: asyncio.Queue[str] = asyncio.Queue()
    await token_queue.put("流式")

    payloads = [
        item async for item in iter_frontend_transport_events(events(), token_queue)
    ]

    assert {"type": "step", "step": "collect", "label": "需求收集"} in payloads
    assert {"type": "token", "content": "请问出发城市？"} in payloads
    assert {"type": "token", "content": "流式"} in payloads
    assert payloads[-1] == {"type": "done"}
