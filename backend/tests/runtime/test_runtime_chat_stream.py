import asyncio
from collections.abc import AsyncIterator

import pytest

from app.runtime.events import (
    RuntimeEvent,
    make_runtime_completed_event,
    make_stage_started_event,
)
from app.services.runtime_chat_stream import _iter_runtime_events_and_tokens


@pytest.mark.asyncio
async def test_iter_runtime_events_and_tokens_drains_tokens() -> None:
    async def events() -> AsyncIterator[RuntimeEvent]:
        yield make_stage_started_event(run_id="run_1", stage="collect")
        yield make_runtime_completed_event(run_id="run_1")

    token_queue: asyncio.Queue[str] = asyncio.Queue()
    await token_queue.put("hello")

    items = [
        item async for item in _iter_runtime_events_and_tokens(events(), token_queue)
    ]

    assert ("token", "hello") in items
    assert any(
        kind == "event" and value.type == "runtime_completed"
        for kind, value in items
    )


@pytest.mark.asyncio
async def test_iter_runtime_events_and_tokens_yields_token_during_runtime() -> None:
    token_queue: asyncio.Queue[str] = asyncio.Queue()

    async def events() -> AsyncIterator[RuntimeEvent]:
        yield make_stage_started_event(run_id="run_1", stage="collect")
        await token_queue.put("during")
        await asyncio.sleep(0)
        yield make_runtime_completed_event(run_id="run_1")

    items = [
        item async for item in _iter_runtime_events_and_tokens(events(), token_queue)
    ]

    token_index = items.index(("token", "during"))
    completed_index = next(
        index
        for index, (kind, value) in enumerate(items)
        if kind == "event" and value.type == "runtime_completed"
    )

    assert token_index < completed_index


@pytest.mark.asyncio
async def test_iter_runtime_events_and_tokens_drains_tail_tokens() -> None:
    token_queue: asyncio.Queue[str] = asyncio.Queue()

    async def events() -> AsyncIterator[RuntimeEvent]:
        yield make_stage_started_event(run_id="run_1", stage="collect")
        await token_queue.put("tail")

    items = [
        item async for item in _iter_runtime_events_and_tokens(events(), token_queue)
    ]

    assert ("token", "tail") in items
