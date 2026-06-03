"""
数据库初始化脚本（完整版）

1. 业务表（users / travel_sessions / messages）
2. LangGraph Checkpointer 表
3. LangGraph Store 表
4. pgvector 扩展

用法:
  uv run python scripts/init_db.py              # create_all 业务表（开发）
  uv run python scripts/init_db.py --alembic    # Alembic 迁移（推荐生产）
  uv run python scripts/init_db.py --skip-business  # 仅 LangGraph + pgvector
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from alembic import command
from alembic.config import Config
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres import AsyncPostgresStore
from loguru import logger
from psycopg_pool import AsyncConnectionPool

from app.db.init_db import init_db
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()


def _run_alembic_upgrade() -> None:
    ini_path = BACKEND_DIR / "alembic.ini"
    if not ini_path.is_file():
        raise FileNotFoundError(f"未找到 Alembic 配置: {ini_path}")
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")
    logger.info("Alembic 迁移完成 (head)")


async def init_database(
    *,
    use_alembic: bool = False,
    skip_business: bool = False,
) -> None:
    """初始化所有数据库表与扩展。"""
    db_url = settings.psycopg_url
    logger.info(
        "连接数据库 {}:{}/{}",
        settings.db_host,
        settings.db_port,
        settings.db_name,
    )

    try:
        if not skip_business:
            logger.info("初始化业务表...")
            if use_alembic:
                _run_alembic_upgrade()
            else:
                await init_db()
            logger.info("业务表就绪")

        pool_min = settings.db_pool_min_size
        pool_max = max(pool_min, min(10, settings.db_pool_max_size))

        async with AsyncConnectionPool(
            conninfo=db_url, min_size=pool_min, max_size=pool_max
        ) as pool:
            logger.info("初始化 Checkpointer 表...")
            async with AsyncPostgresSaver.from_conn_string(db_url) as checkpointer:
                await checkpointer.setup()
            logger.info("Checkpointer 表创建成功")

            logger.info("初始化 Store 表...")
            async with AsyncPostgresStore.from_conn_string(db_url) as store:
                await store.setup()
            logger.info("Store 表创建成功")

            logger.info("启用 pgvector 扩展...")
            async with pool.connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                await conn.commit()
            logger.info("pgvector 扩展启用成功")

        logger.info("数据库初始化完成")

    except Exception as exc:
        logger.exception("数据库初始化失败: {}", exc)
        raise


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="初始化 PostgreSQL（业务表 + LangGraph + pgvector）")
    parser.add_argument(
        "--alembic",
        action="store_true",
        help="使用 Alembic 迁移业务表（生产推荐）",
    )
    parser.add_argument(
        "--skip-business",
        action="store_true",
        help="跳过业务表，仅初始化 Checkpointer / Store / pgvector",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(
        init_database(
            use_alembic=args.alembic,
            skip_business=args.skip_business,
        )
    )
