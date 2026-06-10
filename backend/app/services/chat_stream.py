"""SSE / WebSocket 流式对话与消息持久化。"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.db.models.message import Message
from app.db.models.user import User
from app.db.repositories.message_repository import MessageRepository
from app.db.session import get_session_factory
from app.services.itinerary_service import (
    approve_itinerary_with_order,
    upsert_itinerary_from_chat,
)


def sse(data: dict[str, Any]) -> str:
    """SSE 标准 data 帧。"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


async def save_message(
    conversation_id: uuid.UUID,
    role: str,
    content: str,
    *,
    extra_info: dict[str, Any] | None = None,
) -> Message:
    """在独立会话中保存消息并提交。"""
    factory = get_session_factory()
    async with factory() as session:
        try:
            message = await MessageRepository(session).create(
                conversation_id=conversation_id,
                role=role,
                content=content,
                extra_info=extra_info,
            )
            await session.commit()
            return message
        except Exception:
            await session.rollback()
            raise


async def _persist_itinerary_if_present(
    conversation_id: uuid.UUID,
    user: User,
    message_extra: dict[str, Any] | None,
) -> None:
    if not message_extra or "itinerary" not in message_extra:
        return
    days = message_extra.get("itinerary")
    if not isinstance(days, list):
        return
    budget = message_extra.get("budget")
    if budget is not None and not isinstance(budget, dict):
        budget = None
    summary = message_extra.get("summary")
    if summary is not None and not isinstance(summary, str):
        summary = None
    await upsert_itinerary_from_chat(
        conversation_id,
        user.id,
        days=days,
        budget=budget,
        summary=summary,
    )


async def _persist_order_if_present(
    conversation_id: uuid.UUID,
    user: User,
    message_extra: dict[str, Any] | None,
) -> None:
    if not message_extra:
        return
    order_id = message_extra.get("order_id")
    if not isinstance(order_id, str) or not order_id.strip():
        return
    await approve_itinerary_with_order(
        conversation_id,
        user.id,
        order_id=order_id.strip(),
    )


async def iter_chat_events(
    conversation_id: uuid.UUID,
    user_message: str,
    user: User,
) -> AsyncIterator[dict[str, Any]]:
    """PlanningRuntime chat stream events for SSE / WebSocket."""
    from app.services.runtime_chat_service import iter_chat_events_runtime

    async for event in iter_chat_events_runtime(conversation_id, user_message, user):
        yield event


async def generate_sse_stream(
    conversation_id: uuid.UUID,
    user_message: str,
    user: User,
) -> AsyncIterator[str]:
    """PlanningRuntime stream encoded as SSE frames."""
    async for event in iter_chat_events(conversation_id, user_message, user):
        yield sse(event)
