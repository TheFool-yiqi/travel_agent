"""Async session factory and FastAPI ``get_db`` dependency."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.db.engine import get_async_engine

_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


def reset_session_factory() -> None:
    """Clear cached factory (tests)."""
    global _session_factory
    _session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a session; commit on success, rollback on error."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
