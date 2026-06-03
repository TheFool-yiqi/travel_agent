"""Travel session persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.travel_session import (
    SESSION_STATUS_ACTIVE,
    SESSION_STATUS_DELETED,
    TravelSession,
)


class TravelSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, session_id: uuid.UUID) -> TravelSession | None:
        return await self._session.get(TravelSession, session_id)

    async def get_by_thread_id(self, thread_id: str) -> TravelSession | None:
        stmt = select(TravelSession).where(TravelSession.thread_id == thread_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        status: str | None = None,
        exclude_deleted: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> list[TravelSession]:
        stmt = select(TravelSession).where(TravelSession.user_id == user_id)
        if status is not None:
            stmt = stmt.where(TravelSession.status == status)
        elif exclude_deleted:
            stmt = stmt.where(TravelSession.status != SESSION_STATUS_DELETED)
        stmt = (
            stmt.order_by(TravelSession.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_for_user(
        self, session_id: uuid.UUID, user_id: uuid.UUID
    ) -> TravelSession | None:
        stmt = select(TravelSession).where(
            TravelSession.id == session_id,
            TravelSession.user_id == user_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(
        self,
        travel_session: TravelSession,
        *,
        title: str | None = None,
        status: str | None = None,
        extra_info: dict | None = None,
    ) -> TravelSession:
        if title is not None:
            travel_session.title = title
        if status is not None:
            travel_session.status = status
        if extra_info is not None:
            travel_session.extra_info = extra_info
        await self._session.flush()
        await self._session.refresh(travel_session)
        return travel_session

    async def create(
        self,
        *,
        user_id: uuid.UUID,
        title: str = "新对话",
        status: str = SESSION_STATUS_ACTIVE,
        extra_info: dict | None = None,
        thread_id: str | None = None,
    ) -> TravelSession:
        travel_session = TravelSession(
            user_id=user_id,
            title=title,
            status=status,
            extra_info=extra_info or {},
            thread_id=thread_id,
        )
        self._session.add(travel_session)
        await self._session.flush()
        await self._session.refresh(travel_session)
        return travel_session

    async def update_status(
        self, session_id: uuid.UUID, status: str
    ) -> TravelSession | None:
        travel_session = await self.get_by_id(session_id)
        if travel_session is None:
            return None
        travel_session.status = status
        await self._session.flush()
        await self._session.refresh(travel_session)
        return travel_session

    async def get_with_messages(self, session_id: uuid.UUID) -> TravelSession | None:
        stmt = (
            select(TravelSession)
            .where(TravelSession.id == session_id)
            .options(selectinload(TravelSession.messages))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()


# Handoffs 兼容别名
ConversationRepository = TravelSessionRepository
