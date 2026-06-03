"""探索 Agent 自主调用 RAG 工具测试（Route 1：RAG 在 agents 层，不在 step_config）。"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage

import app.agents.destination.explore_agent as explore_module
import app.graph.routers.destination_router as destination_router
from app.agents.destination.explore_agent import create_explore_agent, run_explore_agent
from app.graph.routers.destination_router import create_destination_router
from app.settings import settings
from app.tools.rag import get_rag_tools


def _collect_tool_calls(messages: list) -> list[dict]:
    """从 Agent 消息历史中提取 tool_calls。"""
    calls: list[dict] = []
    for msg in messages:
        for tc in getattr(msg, "tool_calls", None) or []:
            if isinstance(tc, dict):
                calls.append({"name": tc["name"], "args": tc.get("args", {})})
            else:
                calls.append(
                    {
                        "name": getattr(tc, "name", ""),
                        "args": getattr(tc, "args", {}),
                    }
                )
    return calls


@pytest.fixture(autouse=True)
def clear_explore_cache() -> None:
    explore_module.create_explore_agent.cache_clear()
    yield
    explore_module.create_explore_agent.cache_clear()


def test_explore_agent_loads_four_rag_tools() -> None:
    tools = get_rag_tools()
    assert len(tools) == 4
    names = {tool.name for tool in tools}
    assert names == {
        "search_destination_guide",
        "search_food_recommendations",
        "search_accommodation_info",
        "search_travel_tips",
    }


def test_collect_tool_calls_helper() -> None:
    messages = [
        HumanMessage(content="西安景点"),
        AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_destination_guide",
                    "args": {"query": "西安兵马俑"},
                    "id": "call_1",
                    "type": "tool_call",
                }
            ],
        ),
    ]
    calls = _collect_tool_calls(messages)
    assert len(calls) == 1
    assert calls[0]["name"] == "search_destination_guide"
    assert "西安" in str(calls[0]["args"])


def test_explore_fallback_without_mimo(monkeypatch: pytest.MonkeyPatch) -> None:
    """无 LLM 时回退 rag_search，不经过 ReAct 工具链。"""
    monkeypatch.setattr(explore_module.settings, "mimo_api_key", "")
    monkeypatch.setattr(
        explore_module,
        "rag_search",
        lambda query, destination=None, **kwargs: "fallback body",
    )

    result = run_explore_agent("西安", "兵马俑门票多少钱？")
    assert "fallback body" in result


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY")
async def test_explore_agent_autonomous_rag() -> None:
    """探索 Agent 对具体旅游问题应自主调用 RAG 工具（非 graph 节点绑定）。"""
    agent = create_explore_agent()
    query = "西安兵马俑的门票多少钱？有什么游玩建议？"

    response = await agent.ainvoke(
        {"messages": [HumanMessage(content=f"目的地：西安\n查询：{query}")]}
    )

    messages = response.get("messages") or []
    tool_calls = _collect_tool_calls(messages)
    reply = messages[-1].content if messages else ""
    reply_text = reply if isinstance(reply, str) else str(reply)

    assert reply_text.strip(), "Agent 应返回非空回复"
    assert tool_calls, f"应对具体旅游问题调用 RAG 工具，实际 tool_calls={tool_calls}"
    rag_tool_names = {t.name for t in get_rag_tools()}
    assert all(call["name"] in rag_tool_names for call in tool_calls)


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY")
async def test_explore_agent_multi_topic_rag() -> None:
    """综合查询可能调用多个 RAG 工具。"""
    agent = create_explore_agent()
    query = "我想去西安，帮我介绍一下景点、美食和住宿建议"

    response = await agent.ainvoke(
        {"messages": [HumanMessage(content=f"目的地：西安\n查询：{query}")]}
    )

    tool_calls = _collect_tool_calls(response.get("messages") or [])
    assert tool_calls, "综合旅游查询应触发 RAG 检索"
    assert len({call["name"] for call in tool_calls}) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY")
async def test_router_explore_branch_autonomous_rag() -> None:
    """Router explore 分支内嵌探索 Agent，自主选 RAG 工具（非 step_config *rag_tools）。"""
    destination_router._router = None
    router = create_destination_router()

    result = await router.ainvoke(
        {
            "original_query": "西安有什么好玩的景点？",
            "destination": "西安",
            "classifications": [],
            "agent_results": [],
            "final_report": "",
        }
    )

    assert result["classifications"]
    assert any(item["agent"] == "explore" for item in result["classifications"])
    assert "explore" in result["final_report"].lower() or "西安" in result["final_report"]
    assert result["final_report"].strip()
