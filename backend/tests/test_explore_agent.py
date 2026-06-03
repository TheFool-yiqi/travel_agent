"""探索 Agent 测试。"""

from __future__ import annotations

import pytest

import app.agents.destination.explore_agent as explore_module
from app.agents.destination.explore_agent import run_explore_agent


@pytest.fixture(autouse=True)
def clear_explore_cache() -> None:
    explore_module.create_explore_agent.cache_clear()
    yield
    explore_module.create_explore_agent.cache_clear()


def test_explore_fallback_without_mimo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(explore_module.settings, "mimo_api_key", "")
    monkeypatch.setattr(
        explore_module,
        "rag_search",
        lambda query, destination=None, **kwargs: "mock rag body",
    )

    result = run_explore_agent("西安", "有什么好玩的")
    assert "mock rag body" in result
    assert "西安" in result
