"""LangGraph Checkpointer 工厂（Redis / Postgres）。"""

from __future__ import annotations

import asyncio
from typing import Literal

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from loguru import logger
from psycopg_pool import AsyncConnectionPool

from app.settings import Settings, settings

CheckpointBackend = Literal["redis", "postgres"]


def _patch_redis_serializer_for_checkpoint_v4() -> None:
    """Patch legacy JsonPlusRedisSerializer (0.0.x) for langgraph-checkpoint 4.x."""
    from importlib.metadata import PackageNotFoundError, version

    try:
        major, minor, *_ = (int(x) for x in version("langgraph-checkpoint-redis").split("."))
        if (major, minor) >= (0, 2):
            return
    except (PackageNotFoundError, ValueError):
        pass

    import base64
    from typing import Any, Union

    from langgraph.checkpoint.redis.jsonplus_redis import JsonPlusRedisSerializer
    from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

    if getattr(JsonPlusRedisSerializer, "_compat_patched_v4", False):
        return

    def dumps_typed(self: JsonPlusRedisSerializer, obj: Any) -> tuple[str, str]:
        if isinstance(obj, (bytes, bytearray)):
            return "base64", base64.b64encode(obj).decode("utf-8")
        type_, payload = JsonPlusSerializer.dumps_typed(self, obj)
        if isinstance(payload, bytes):
            if type_ == "json":
                return type_, payload.decode("utf-8")
            return type_, base64.b64encode(payload).decode("utf-8")
        return type_, str(payload)

    def loads_typed(
        self: JsonPlusRedisSerializer,
        data: tuple[str, Union[str, bytes]],
    ) -> Any:
        type_, data_ = data
        if type_ == "base64":
            raw = data_ if isinstance(data_, bytes) else data_.encode()
            return base64.b64decode(raw)
        if isinstance(data_, str) and type_ in ("msgpack", "json"):
            try:
                payload: bytes | str = base64.b64decode(data_)
            except Exception:
                payload = data_.encode()
        else:
            payload = data_ if isinstance(data_, bytes) else data_.encode()
        return JsonPlusSerializer.loads_typed(self, (type_, payload))

    JsonPlusRedisSerializer.dumps_typed = dumps_typed  # type: ignore[method-assign]
    JsonPlusRedisSerializer.loads_typed = loads_typed  # type: ignore[method-assign]
    JsonPlusRedisSerializer._compat_patched_v4 = True  # type: ignore[attr-defined]
    logger.info("已应用 JsonPlusRedisSerializer checkpoint v4 兼容补丁")


def resolve_checkpoint_backend(value: str | None = None) -> CheckpointBackend:
    backend = (value or settings.checkpoint_backend).strip().lower()
    if backend not in ("redis", "postgres"):
        raise ValueError(f"不支持的 CHECKPOINT_BACKEND: {backend}")
    return backend  # type: ignore[return-value]


def checkpoint_ttl_config(cfg: Settings | None = None) -> dict[str, float] | None:
    """将保留天数转为 Redis checkpoint TTL（分钟）。"""
    cfg = cfg or settings
    if cfg.checkpoint_retention_days <= 0:
        return None
    return {"default_ttl": cfg.checkpoint_retention_days * 24 * 60}


async def create_redis_checkpointer(
    *,
    redis_url: str | None = None,
    ttl: dict[str, float] | None = None,
) -> AsyncRedisSaver:
    """
    创建并初始化 Redis Checkpointer。

    需要 Redis 8+ 或 Redis Stack（RedisJSON + RediSearch 模块）。

    注意：请使用 langgraph-checkpoint-redis >=0.4.1（兼容 checkpoint 4.x）。
    旧版 0.0.x 需 _patch_redis_serializer_for_checkpoint_v4()。
    """
    _patch_redis_serializer_for_checkpoint_v4()
    url = redis_url or settings.redis_url
    saver = AsyncRedisSaver(redis_url=url, ttl=ttl or checkpoint_ttl_config())
    await saver.asetup()
    logger.info(
        "Redis Checkpointer 已就绪 url={} ttl={}",
        url.split("@")[-1],
        (ttl or checkpoint_ttl_config()),
    )
    return saver


def create_postgres_checkpointer(pool: AsyncConnectionPool) -> AsyncPostgresSaver:
    """从 PostgreSQL 连接池创建 Checkpointer。"""
    return AsyncPostgresSaver(pool)


async def close_redis_checkpointer(saver: AsyncRedisSaver) -> None:
    """关闭 Redis Checkpointer 及其连接。"""
    try:
        await saver.__aexit__(None, None, None)
    except AttributeError:
        close_fn = getattr(saver._redis, "aclose", None) or getattr(saver._redis, "close", None)
        if close_fn is not None:
            result = close_fn()
            if asyncio.iscoroutine(result):
                await result


def checkpointer_label(saver: BaseCheckpointSaver) -> str:
    if isinstance(saver, AsyncRedisSaver):
        return "redis"
    if isinstance(saver, AsyncPostgresSaver):
        return "postgres"
    return saver.__class__.__name__
