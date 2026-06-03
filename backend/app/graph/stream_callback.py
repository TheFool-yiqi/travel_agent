"""Graph 节点内向 SSE 推送 token 的上下文回调。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextvars import ContextVar

StreamTokenHandler = Callable[[str], Awaitable[None] | None]

_handler: ContextVar[StreamTokenHandler | None] = ContextVar("stream_token_handler", default=None)


def set_stream_token_handler(handler: StreamTokenHandler | None) -> None:
    _handler.set(handler)


def get_stream_token_handler() -> StreamTokenHandler | None:
    return _handler.get()


async def emit_stream_token(token: str) -> None:
    if not token:
        return
    handler = get_stream_token_handler()
    if handler is None:
        return
    result = handler(token)
    if result is not None:
        await result
