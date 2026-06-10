"""RuntimeEvent and public-token stream multiplexing."""

from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any

from app.runtime.events import RuntimeEvent
from app.runtime.streaming.frontend_adapter import adapt_runtime_event_to_frontend_events


def _drain_stream_tokens(queue: asyncio.Queue[str]) -> list[str]:
    tokens: list[str] = []
    while True:
        try:
            tokens.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            break
    return tokens


async def _iter_runtime_events_and_tokens(
    runtime_events: AsyncIterator[RuntimeEvent],
    token_queue: asyncio.Queue[str],
) -> AsyncIterator[tuple[str, Any]]:
    """Multiplex internal RuntimeEvents with the single public token stream."""
    event_iter = runtime_events.__aiter__()
    event_task: asyncio.Task[RuntimeEvent] | None = None
    token_task: asyncio.Task[str] | None = None

    while True:
        if event_task is None:
            event_task = asyncio.create_task(event_iter.__anext__())
        if token_task is None:
            token_task = asyncio.create_task(token_queue.get())

        done, _ = await asyncio.wait(
            {event_task, token_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if token_task in done:
            token = token_task.result()
            token_task = None
            yield ("token", token)

        if event_task in done:
            try:
                event = event_task.result()
            except StopAsyncIteration:
                event_task = None
                break
            event_task = None
            yield ("event", event)

    if token_task is not None:
        token_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await token_task

    for token in _drain_stream_tokens(token_queue):
        yield ("token", token)


async def iter_frontend_transport_events(
    runtime_events: AsyncIterator[RuntimeEvent],
    token_queue: asyncio.Queue[str],
) -> AsyncIterator[dict[str, Any]]:
    """Multiplex RuntimeEvents and tokens, yielding frontend transport dicts."""
    async for kind, payload in _iter_runtime_events_and_tokens(runtime_events, token_queue):
        if kind == "token":
            yield {"type": "token", "content": payload}
            continue

        for event in adapt_runtime_event_to_frontend_events(payload):
            yield event
