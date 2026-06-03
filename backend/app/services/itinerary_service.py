"""行程业务编排：upsert 与 session extra_info 同步。"""

from __future__ import annotations

import uuid
from typing import Any

from app.db.models.itinerary import ITINERARY_STATUS_DRAFT, Itinerary
from app.db.repositories.itinerary_repository import ItineraryRepository
from app.db.repositories.travel_session_repository import TravelSessionRepository
from app.db.session import get_session_factory
from app.schemas.itinerary import ItinerarySessionPayload


async def upsert_itinerary_from_chat(
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    days: list[dict[str, Any]],
    budget: dict[str, Any] | None = None,
    summary: str | None = None,
) -> Itinerary:
    """流式完成时 upsert 行程并同步 travel_sessions.extra_info.itinerary。"""
    factory = get_session_factory()
    async with factory() as db:
        try:
            session_repo = TravelSessionRepository(db)
            travel_session = await session_repo.get_for_user(session_id, user_id)
            if travel_session is None:
                raise ValueError("会话不存在")

            itinerary_repo = ItineraryRepository(db)
            latest = await itinerary_repo.get_latest_for_session(
                session_id,
                user_id=user_id,
            )
            next_version = (latest.version + 1) if latest else 1

            itinerary = await itinerary_repo.create(
                session_id=session_id,
                user_id=user_id,
                days=days,
                budget=budget,
                summary=summary,
                status=ITINERARY_STATUS_DRAFT,
                version=next_version,
            )

            extra_info = dict(travel_session.extra_info or {})
            extra_info["itinerary"] = ItinerarySessionPayload(
                days=days,
                budget=budget,
                summary=summary,
                version=itinerary.version,
                itinerary_id=itinerary.id,
            ).model_dump(mode="json")
            await session_repo.update(travel_session, extra_info=extra_info)

            await db.commit()
            return itinerary
        except Exception:
            await db.rollback()
            raise
