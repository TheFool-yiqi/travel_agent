"""行程 REST API。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.travel_session import SESSION_STATUS_DELETED
from app.db.models.user import User
from app.db.repositories.itinerary_repository import ItineraryRepository
from app.db.repositories.travel_session_repository import TravelSessionRepository
from app.db.session import get_db
from app.schemas.itinerary import ItineraryResponse, ItineraryUpdate

router = APIRouter(prefix="/itineraries", tags=["行程"])


def _parse_uuid(value: str, *, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效的 {field}",
        ) from exc


@router.get("/sessions/{session_id}", response_model=ItineraryResponse)
async def get_latest_itinerary_for_session(
    session_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ItineraryResponse:
    """获取会话最新行程。"""
    sid = _parse_uuid(session_id, field="session_id")
    travel_session = await TravelSessionRepository(db).get_for_user(sid, user.id)
    if travel_session is None or travel_session.status == SESSION_STATUS_DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    itinerary = await ItineraryRepository(db).get_latest_for_session(
        sid,
        user_id=user.id,
    )
    if itinerary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在",
        )
    return ItineraryResponse.model_validate(itinerary)


@router.get("/{itinerary_id}", response_model=ItineraryResponse)
async def get_itinerary(
    itinerary_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ItineraryResponse:
    """按 ID 获取行程。"""
    iid = _parse_uuid(itinerary_id, field="itinerary_id")
    itinerary = await ItineraryRepository(db).get_by_id(iid, user_id=user.id)
    if itinerary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在",
        )
    return ItineraryResponse.model_validate(itinerary)


@router.patch("/{itinerary_id}", response_model=ItineraryResponse)
async def update_itinerary(
    itinerary_id: str,
    data: ItineraryUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ItineraryResponse:
    """手动编辑行程 days/budget/summary。"""
    iid = _parse_uuid(itinerary_id, field="itinerary_id")
    repo = ItineraryRepository(db)
    itinerary = await repo.get_by_id(iid, user_id=user.id)
    if itinerary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="行程不存在",
        )

    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return ItineraryResponse.model_validate(itinerary)

    itinerary = await repo.update_fields(itinerary, **update_data)

    travel_session = await TravelSessionRepository(db).get_for_user(
        itinerary.session_id,
        user.id,
    )
    if travel_session is not None:
        extra_info = dict(travel_session.extra_info or {})
        session_itinerary = dict(extra_info.get("itinerary") or {})
        if data.days is not None:
            session_itinerary["days"] = data.days
        if data.budget is not None:
            session_itinerary["budget"] = data.budget
        if data.summary is not None:
            session_itinerary["summary"] = data.summary
        session_itinerary["version"] = itinerary.version
        session_itinerary["itinerary_id"] = str(itinerary.id)
        extra_info["itinerary"] = session_itinerary
        await TravelSessionRepository(db).update(
            travel_session,
            extra_info=extra_info,
        )

    return ItineraryResponse.model_validate(itinerary)
