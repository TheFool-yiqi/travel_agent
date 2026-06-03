"""Itinerary persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.itinerary import ITINERARY_STATUS_DRAFT, Itinerary


class ItineraryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        itinerary_id: uuid.UUID,
        *,
        user_id: uuid.UUID | None = None,
    ) -> Itinerary | None:
        stmt = select(Itinerary).where(Itinerary.id == itinerary_id)
        if user_id is not None:
            stmt = stmt.where(Itinerary.user_id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_for_session(
        self,
        session_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
    ) -> Itinerary | None:
        stmt = (
            select(Itinerary)
            .where(
                Itinerary.session_id == session_id,
                Itinerary.user_id == user_id,
            )
            .order_by(Itinerary.version.desc(), Itinerary.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        session_id: uuid.UUID,
        user_id: uuid.UUID,
        days: list,
        budget: dict | None = None,
        summary: str | None = None,
        status: str = ITINERARY_STATUS_DRAFT,
        version: int = 1,
    ) -> Itinerary:
        itinerary = Itinerary(
            session_id=session_id,
            user_id=user_id,
            days=days,
            budget=budget,
            summary=summary,
            status=status,
            version=version,
        )
        self._session.add(itinerary)
        await self._session.flush()
        await self._session.refresh(itinerary)
        return itinerary

    async def update_fields(
        self,
        itinerary: Itinerary,
        *,
        days: list | None = None,
        budget: dict | None = None,
        summary: str | None = None,
        status: str | None = None,
    ) -> Itinerary:
        if days is not None:
            itinerary.days = days
        if budget is not None:
            itinerary.budget = budget
        if summary is not None:
            itinerary.summary = summary
        if status is not None:
            itinerary.status = status
        await self._session.flush()
        await self._session.refresh(itinerary)
        return itinerary
