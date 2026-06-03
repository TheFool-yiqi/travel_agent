"""SQLAlchemy declarative base and shared model utilities."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column

# PostgreSQL naming conventions for Alembic-friendly constraint names
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def _camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class Base(DeclarativeBase):
    """Declarative base with optional auto table names and ``to_dict()``."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Default: ``TravelSession`` → ``travel_sessions`` (override per model)."""
        return f"{_camel_to_snake(cls.__name__)}s"

    def to_dict(self) -> dict[str, Any]:
        """Serialize mapped columns (UUID/datetime → str / ISO)."""
        out: dict[str, Any] = {}
        for column in self.__table__.columns:
            value = getattr(self, column.key)
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            out[column.key] = value
        return out


class UUIDPrimaryKeyMixin:
    """UUID primary key defaulting to ``uuid4``."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """``created_at`` / ``updated_at`` with server-side defaults."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
