"""Async SQLAlchemy engine (postgresql+psycopg)."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.settings import settings

_engine: AsyncEngine | None = None


def get_async_engine() -> AsyncEngine:
    """Return the process-wide async engine (lazy singleton)."""
    global _engine
    if _engine is None:
        max_overflow = max(
            0, settings.db_pool_max_size - settings.db_pool_min_size
        )
        _engine = create_async_engine(
            settings.database_url,
            pool_size=settings.db_pool_min_size,
            max_overflow=max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,
        )
    return _engine


async def dispose_async_engine() -> None:
    """Close the engine pool (tests / shutdown)."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
