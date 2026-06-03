"""目的地 Router 测试。"""

from __future__ import annotations

import pytest

import app.graph.routers.destination_router as destination_router
from app.graph.routers.destination_router import create_destination_router


def _router_state(*, original_query: str, destination: str) -> dict:
    return {
        "original_query": original_query,
        "destination": destination,
        "classifications": [],
        "agent_results": [],
        "final_report": "",
    }


@pytest.fixture
def router(monkeypatch: pytest.MonkeyPatch):
    """使用规则分类 + mock Agent，避免 LLM/RAG/天气 API 依赖。"""
    destination_router._router = None

    monkeypatch.setattr(
        destination_router,
        "classifier_node",
        lambda state: {
            "classifications": destination_router._default_classifications(
                state["destination"],
                state["original_query"],
            ),
        },
    )

    def mock_explore(state: dict) -> dict:
        return {
            "agent_results": [
                {
                    "agent_name": "explore",
                    "result": f"mock explore: {state['query']}",
                },
            ],
        }

    def mock_weather(state: dict) -> dict:
        return {
            "agent_results": [
                {
                    "agent_name": "weather",
                    "result": f"mock weather: {state['destination']}",
                },
            ],
        }

    monkeypatch.setattr(destination_router, "explore_agent_node", mock_explore)
    monkeypatch.setattr(destination_router, "weather_agent_node", mock_weather)

    return create_destination_router()


@pytest.mark.asyncio
async def test_explore_only(router) -> None:
    """景点类查询仅调用 explore。"""
    result = await router.ainvoke(
        _router_state(
            original_query="西安有什么好玩的景点？",
            destination="西安",
        ),
    )

    assert len(result["classifications"]) == 1
    assert result["classifications"][0]["agent"] == "explore"
    assert "mock explore" in result["final_report"]
    assert "mock weather" not in result["final_report"]


@pytest.mark.asyncio
async def test_weather_only(router) -> None:
    """天气类查询仅调用 weather。"""
    result = await router.ainvoke(
        _router_state(
            original_query="西安现在天气怎么样？",
            destination="西安",
        ),
    )

    assert len(result["classifications"]) == 1
    assert result["classifications"][0]["agent"] == "weather"
    assert "mock weather" in result["final_report"]
    assert "mock explore" not in result["final_report"]


@pytest.mark.asyncio
async def test_both_agents(router) -> None:
    """综合推荐类查询并行调用 explore + weather。"""
    result = await router.ainvoke(
        _router_state(
            original_query="推荐西安旅游",
            destination="西安",
        ),
    )

    assert len(result["classifications"]) == 2
    assert {item["agent"] for item in result["classifications"]} == {"explore", "weather"}
    assert "mock explore" in result["final_report"]
    assert "mock weather" in result["final_report"]
