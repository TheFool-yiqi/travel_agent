"""Business table initialization (Handoffs ``init_db`` compatible)."""

from __future__ import annotations

from loguru import logger

from app.db.base import Base
from app.db.engine import dispose_async_engine, get_async_engine
from app.db.models import Message, TravelSession, User  # noqa: F401 — register metadata


async def create_business_tables() -> None:
    """Create ORM tables via ``Base.metadata.create_all`` (development / bootstrap)."""
    engine = get_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(
        "业务表已创建: {}",
        ", ".join(sorted(Base.metadata.tables.keys())),
    )


async def init_db() -> None:
    """
    Handoffs 兼容入口：初始化 users / travel_sessions / messages 等业务表。

    生产环境请优先使用 ``alembic upgrade head``。
    """
    await create_business_tables()
    await dispose_async_engine()
