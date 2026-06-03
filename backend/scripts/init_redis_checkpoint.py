"""
初始化 Redis LangGraph Checkpointer 索引。

需要 Redis Stack 或 Redis 8+（含 RedisJSON、RediSearch 模块）。

用法（在 backend 目录）：
    uv run python scripts/init_redis_checkpoint.py
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from loguru import logger

from app.graph.checkpoint import create_redis_checkpointer, close_redis_checkpointer
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()


async def main() -> None:
    if resolve_backend() != "redis":
        logger.warning(
            "当前 CHECKPOINT_BACKEND={}，如需 Redis 请设置 CHECKPOINT_BACKEND=redis",
            settings.checkpoint_backend,
        )

    logger.info("初始化 Redis Checkpointer 索引...")
    saver = await create_redis_checkpointer()
    await close_redis_checkpointer(saver)
    logger.info("Redis Checkpointer 索引就绪")


def resolve_backend() -> str:
    return settings.checkpoint_backend.strip().lower()


if __name__ == "__main__":
    asyncio.run(main())
