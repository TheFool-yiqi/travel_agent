"""行程持久化模型（表 itineraries）。"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

ITINERARY_STATUS_DRAFT = "draft"
ITINERARY_STATUS_APPROVED = "approved"


class Itinerary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """会话关联的行程快照（按 version 递增）。"""

    __tablename__ = "itineraries"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("travel_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    days: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    budget: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ITINERARY_STATUS_DRAFT,
        nullable=False,
        server_default=ITINERARY_STATUS_DRAFT,
        index=True,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        server_default="1",
    )

    session: Mapped["TravelSession"] = relationship("TravelSession")
    user: Mapped["User"] = relationship("User")
