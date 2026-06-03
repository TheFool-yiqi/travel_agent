"""清理过期 LangGraph Checkpoint（运维脚本）"""
import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from loguru import logger

from app.dependencies import CheckpointerManager
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()


async def _delete_thread_checkpoints(conn, thread_id: str) -> int:
    """删除指定 thread 的全部 checkpoint 相关数据"""
    deleted = 0
    async with conn.cursor() as cur:
        await cur.execute(
            "DELETE FROM checkpoint_writes WHERE thread_id = %s",
            (thread_id,),
        )
        deleted += cur.rowcount

        await cur.execute(
            "DELETE FROM checkpoint_blobs WHERE thread_id = %s",
            (thread_id,),
        )
        deleted += cur.rowcount

        await cur.execute(
            "DELETE FROM checkpoints WHERE thread_id = %s",
            (thread_id,),
        )
        deleted += cur.rowcount

    return deleted


async def _get_cutoff_checkpoint_id(conn, days: int) -> str | None:
    """
    LangGraph checkpoints 表无 created_at 字段。
    用 checkpoint_id 字典序估算 cutoff（LangGraph UUID 随时间递增）。
    """
    offset = max(days * settings.checkpoint_cleanup_daily_rate, 1)
    async with conn.cursor() as cur:
        await cur.execute("SELECT COUNT(*) FROM checkpoints")
        total = (await cur.fetchone())[0]
        if total == 0:
            return None

        pos = min(offset, total - 1)
        await cur.execute(
            "SELECT checkpoint_id FROM checkpoints "
            "ORDER BY checkpoint_id DESC OFFSET %s LIMIT 1",
            (pos,),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def _find_stale_thread_ids(conn, days: int) -> list[str]:
    cutoff_id = await _get_cutoff_checkpoint_id(conn, days)
    if not cutoff_id:
        return []

    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT thread_id, MAX(checkpoint_id) AS latest_id "
            "FROM checkpoints GROUP BY thread_id"
        )
        rows = await cur.fetchall()

    return [thread_id for thread_id, latest_id in rows if latest_id < cutoff_id]


async def cleanup_old_checkpoints(
    days: int | None = None,
    thread_id: str | None = None,
    dry_run: bool = False,
) -> int:
    """
    清理过期 Checkpoint。

    - postgres：按 thread_id 或保留天数删除表数据
    - redis：依赖 CHECKPOINT_RETENTION_DAYS 映射的 TTL 自动过期
    """
    if settings.checkpoint_backend.strip().lower() == "redis":
        logger.info(
            "当前使用 Redis Checkpoint，会话状态按 TTL（{} 天）自动过期，"
            "无需 Postgres 清理脚本。",
            settings.checkpoint_retention_days,
        )
        return 0

    retention_days = days if days is not None else settings.checkpoint_retention_days
    manager = await CheckpointerManager.get_instance()
    total_deleted = 0

    try:
        async with manager.pool.connection() as conn:
            if thread_id:
                targets = [thread_id]
                logger.info("按 thread_id 清理: {}", thread_id)
            else:
                cutoff_id = await _get_cutoff_checkpoint_id(conn, retention_days)
                targets = await _find_stale_thread_ids(conn, retention_days)
                logger.info(
                    "按保留 {} 天清理，cutoff checkpoint_id={}，匹配 {} 个 thread",
                    retention_days,
                    cutoff_id,
                    len(targets),
                )

            if dry_run:
                for tid in targets:
                    logger.info("[dry-run] 将删除 thread_id={}", tid)
                return len(targets)

            for tid in targets:
                count = await _delete_thread_checkpoints(conn, tid)
                total_deleted += count
                logger.info("已删除 thread_id={} 相关行 {} 条", tid, count)

            await conn.commit()

        logger.info("清理完成，共删除 {} 行", total_deleted)
        return total_deleted
    finally:
        await manager.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="清理过期 LangGraph Checkpoint")
    parser.add_argument(
        "--days",
        type=int,
        default=None,
        help=f"保留天数（默认 {settings.checkpoint_retention_days}）",
    )
    parser.add_argument("--thread-id", type=str, default=None, help="仅清理指定 thread_id")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将删除的 thread，不实际执行",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    deleted = asyncio.run(
        cleanup_old_checkpoints(
            days=args.days,
            thread_id=args.thread_id,
            dry_run=args.dry_run,
        )
    )
    print(f"完成，影响行数/线程数: {deleted}")
