"""新会话初始化（主动问候等）"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.message_repository import MessageRepository
from app.db.session import get_session_factory
from app.graph.greeting import build_greeting_reply


async def seed_initial_greeting(
    db: AsyncSession,
    conversation_id: uuid.UUID,
) -> None:
    """新建行程时写入助手问候语（持久化，刷新后仍可见）。"""
    await MessageRepository(db).create(
        conversation_id=conversation_id,
        role="assistant",
        content=build_greeting_reply(),
        extra_info={"kind": "greeting", "auto": True},
    )


async def has_assistant_messages(conversation_id: uuid.UUID) -> bool:
    """会话是否已有助手消息（含创建时自动问候）。"""
    factory = get_session_factory()
    async with factory() as session:
        messages = await MessageRepository(session).list_for_conversation(conversation_id)
        return any(message.role == "assistant" for message in messages)
