"""LangGraph Checkpointer 配置。"""

from __future__ import annotations

import pytest

from app.graph.checkpoint import checkpoint_ttl_config, resolve_checkpoint_backend


def test_resolve_checkpoint_backend_defaults_redis() -> None:
    assert resolve_checkpoint_backend("redis") == "redis"
    assert resolve_checkpoint_backend("postgres") == "postgres"


def test_resolve_checkpoint_backend_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        resolve_checkpoint_backend("memory")


def test_checkpoint_ttl_from_retention_days() -> None:
    from app.settings import Settings

    cfg = Settings(CHECKPOINT_RETENTION_DAYS=7)
    assert checkpoint_ttl_config(cfg) == {"default_ttl": 7 * 24 * 60}
