"""itinerary_service 持久化测试。"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.db.models.itinerary import ITINERARY_STATUS_APPROVED, ITINERARY_STATUS_DRAFT
from app.services.itinerary_service import approve_itinerary_with_order


@pytest.mark.asyncio
async def test_approve_itinerary_with_order_updates_status_and_extra_info() -> None:
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()
    itinerary_id = uuid.uuid4()

    mock_itinerary = MagicMock()
    mock_itinerary.id = itinerary_id
    mock_itinerary.version = 1
    mock_itinerary.status = ITINERARY_STATUS_DRAFT

    mock_session = MagicMock()
    mock_session.extra_info = {
        "itinerary": {
            "days": [{"day_number": 1}],
            "itinerary_id": str(itinerary_id),
            "status": ITINERARY_STATUS_DRAFT,
        }
    }

    mock_session_repo = AsyncMock()
    mock_session_repo.get_for_user.return_value = mock_session

    mock_itinerary_repo = AsyncMock()
    mock_itinerary_repo.get_latest_for_session.return_value = mock_itinerary
    mock_itinerary_repo.update_fields = AsyncMock(return_value=mock_itinerary)

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.itinerary_service.get_session_factory",
        return_value=mock_factory,
    ), patch(
        "app.services.itinerary_service.TravelSessionRepository",
        return_value=mock_session_repo,
    ), patch(
        "app.services.itinerary_service.ItineraryRepository",
        return_value=mock_itinerary_repo,
    ):
        result = await approve_itinerary_with_order(
            session_id,
            user_id,
            order_id="ORDER-TEST1234",
        )

    assert result is mock_itinerary
    mock_itinerary_repo.update_fields.assert_awaited_once()
    assert mock_itinerary_repo.update_fields.await_args.kwargs["status"] == ITINERARY_STATUS_APPROVED
    mock_session_repo.update.assert_awaited_once()
    extra = mock_session_repo.update.await_args.kwargs["extra_info"]
    assert extra["itinerary"]["status"] == ITINERARY_STATUS_APPROVED
    assert extra["order"]["order_id"] == "ORDER-TEST1234"
    assert extra["order"]["itinerary_id"] == str(itinerary_id)


@pytest.mark.asyncio
async def test_approve_itinerary_with_order_returns_none_without_itinerary() -> None:
    session_id = uuid.uuid4()
    user_id = uuid.uuid4()

    mock_session = MagicMock()
    mock_session.extra_info = {}

    mock_session_repo = AsyncMock()
    mock_session_repo.get_for_user.return_value = mock_session

    mock_itinerary_repo = AsyncMock()
    mock_itinerary_repo.get_latest_for_session.return_value = None

    mock_db = AsyncMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()

    mock_factory = MagicMock()
    mock_factory.return_value.__aenter__ = AsyncMock(return_value=mock_db)
    mock_factory.return_value.__aexit__ = AsyncMock(return_value=False)

    with patch(
        "app.services.itinerary_service.get_session_factory",
        return_value=mock_factory,
    ), patch(
        "app.services.itinerary_service.TravelSessionRepository",
        return_value=mock_session_repo,
    ), patch(
        "app.services.itinerary_service.ItineraryRepository",
        return_value=mock_itinerary_repo,
    ):
        result = await approve_itinerary_with_order(
            session_id,
            user_id,
            order_id="ORDER-NO-ITIN",
        )

    assert result is None
    mock_itinerary_repo.update_fields.assert_not_called()
    mock_session_repo.update.assert_not_called()
