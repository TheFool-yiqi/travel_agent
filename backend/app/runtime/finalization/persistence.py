"""Itinerary persistence adapter for finalize stage."""

from __future__ import annotations

import uuid
from typing import Any, Protocol

from app.runtime.planning.schemas import ItineraryDraft


class ItineraryPersistenceAdapter(Protocol):
    async def persist_approved_itinerary(
        self,
        *,
        session_id: str,
        user_id: str,
        itinerary_draft: ItineraryDraft,
        order_id: str,
    ) -> dict[str, Any]:
        ...


class StubItineraryPersistenceAdapter:
    """In-memory persistence for runtime tests."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    async def persist_approved_itinerary(
        self,
        *,
        session_id: str,
        user_id: str,
        itinerary_draft: ItineraryDraft,
        order_id: str,
    ) -> dict[str, Any]:
        record = {
            "session_id": session_id,
            "user_id": user_id,
            "order_id": order_id,
            "itinerary_draft": itinerary_draft.to_runtime_dict(),
        }
        self.records.append(record)
        return {
            "persisted": True,
            "itinerary_id": str(uuid.uuid4()),
            "order_id": order_id,
        }


class ServiceItineraryPersistenceAdapter:
    """Wrap existing itinerary_service for approved itinerary persistence."""

    async def persist_approved_itinerary(
        self,
        *,
        session_id: str,
        user_id: str,
        itinerary_draft: ItineraryDraft,
        order_id: str,
    ) -> dict[str, Any]:
        from app.services.itinerary_service import (
            approve_itinerary_with_order,
            upsert_itinerary_from_chat,
        )

        session_uuid = uuid.UUID(session_id)
        user_uuid = uuid.UUID(user_id)
        await upsert_itinerary_from_chat(
            session_uuid,
            user_uuid,
            days=itinerary_draft.days,
            budget=itinerary_draft.budget,
            summary=itinerary_draft.summary,
        )
        itinerary = await approve_itinerary_with_order(
            session_uuid,
            user_uuid,
            order_id=order_id,
        )
        if itinerary is None:
            return {"persisted": False, "order_id": order_id, "itinerary_id": None}
        return {
            "persisted": True,
            "itinerary_id": str(itinerary.id),
            "order_id": order_id,
        }
