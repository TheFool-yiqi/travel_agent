"""Message persistence."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.message import Message


class MessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, message_id: uuid.UUID) -> Message | None:
        return await self._session.get(Message, message_id)

    async def list_for_conversation(
        self,
        conversation_id: uuid.UUID,
        *,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_session(
        self, session_id: uuid.UUID, **kwargs: Any
    ) -> list[Message]:
        """Route 1 别名。"""
        return await self.list_for_conversation(session_id, **kwargs)

    async def create(
        self,
        *,
        conversation_id: uuid.UUID | None = None,
        session_id: uuid.UUID | None = None,
        role: str,
        content: str,
        extra_info: dict[str, Any] | None = None,
        content_metadata: dict[str, Any] | None = None,
    ) -> Message:
        cid = conversation_id or session_id
        if cid is None:
            raise ValueError("conversation_id 或 session_id 必填")
        metadata = extra_info if extra_info is not None else content_metadata
        message = Message(
            conversation_id=cid,
            role=role,
            content=content,
            extra_info=metadata or {},
        )
        self._session.add(message)
        await self._session.flush()
        await self._session.refresh(message)
        return message
