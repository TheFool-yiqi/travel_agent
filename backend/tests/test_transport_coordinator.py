"""交通规划 Subagents / 协调器测试。"""

from __future__ import annotations

import asyncio

import pytest
from langchain_core.messages import AIMessage, HumanMessage

import app.agents.transport.coordinator as coordinator_module
from app.agents.transport.coordinator import (
    create_transport_coordinator,
    create_transport_coordinator_async,
    query_flights,
    query_trains,
    plan_driving_route,
    run_transport_coordinator,
)
from app.settings import settings
from app.tools.datetime_tools import today_beijing_iso


@pytest.fixture(autouse=True)
def clear_coordinator_caches() -> None:
    """避免 lru_cache 在测试间共享 Subagent 实例。"""
    coordinator_module.create_transport_coordinator.cache_clear()
    coordinator_module._get_flight_subagent.cache_clear()
    coordinator_module._get_train_subagent.cache_clear()
    coordinator_module._get_driving_subagent.cache_clear()
    yield
    coordinator_module.create_transport_coordinator.cache_clear()
    coordinator_module._get_flight_subagent.cache_clear()
    coordinator_module._get_train_subagent.cache_clear()
    coordinator_module._get_driving_subagent.cache_clear()


class _FakeSubagent:
    def __init__(self, label: str) -> None:
        self.label = label
        self.last_input: dict | None = None

    def invoke(self, inputs: dict) -> dict:
        self.last_input = inputs
        return {"messages": [AIMessage(content=f"mock {self.label} result")]}

    async def ainvoke(self, inputs: dict) -> dict:
        return self.invoke(inputs)


@pytest.mark.asyncio
async def test_query_flights_tool_delegates_to_subagent(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSubagent("flight")
    monkeypatch.setattr(coordinator_module, "_get_flight_subagent", lambda: fake)

    result = await query_flights.ainvoke(
        {
            "origin": "北京",
            "destination": "上海",
            "departure_date": "2025-08-01",
            "passenger_count": 2,
        }
    )

    assert result == "mock flight result"
    assert fake.last_input is not None
    content = fake.last_input["messages"][0].content
    assert "北京" in content and "上海" in content and "2 人" in content


@pytest.mark.asyncio
async def test_query_trains_tool_delegates_to_subagent(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeSubagent("train")
    monkeypatch.setattr(coordinator_module, "_get_train_subagent", lambda: fake)

    result = await query_trains.ainvoke(
        {
            "origin": "北京",
            "destination": "西安",
            "departure_date": "2025-08-01",
        }
    )

    assert result == "mock train result"
    content = fake.last_input["messages"][0].content
    assert "高铁" in content


@pytest.mark.asyncio
async def test_plan_driving_route_tool_delegates_to_subagent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake = _FakeSubagent("driving")
    monkeypatch.setattr(coordinator_module, "_get_driving_subagent", lambda: fake)

    result = await plan_driving_route.ainvoke(
        {
            "origin": "北京",
            "destination": "上海",
        }
    )

    assert result == "mock driving result"
    content = fake.last_input["messages"][0].content
    assert "自驾" in content


def test_run_transport_coordinator_fallback_without_mimo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "mimo_api_key", "")

    report = run_transport_coordinator(
        "北京",
        "上海",
        "2025-08-01",
        passenger_count=2,
    )

    assert "### 航班" in report
    assert "### 高铁" in report
    assert "### 自驾" in report


def test_build_coordinator_tools_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(coordinator_module, "get_auxiliary_mcp_tools_sync", lambda: [])
    tools = coordinator_module._build_coordinator_tools()
    names = {tool.name for tool in tools}
    assert names == {
        "query_flights",
        "query_trains",
        "plan_driving_route",
        "get-current-date",
    }


def test_build_coordinator_tools_with_auxiliary(monkeypatch: pytest.MonkeyPatch) -> None:
    from langchain_core.tools import tool as lc_tool

    @lc_tool
    def maps_around_search(keywords: str, location: str) -> str:
        """mock around search"""
        return "mock"

    monkeypatch.setattr(
        coordinator_module,
        "get_auxiliary_mcp_tools_sync",
        lambda: [maps_around_search],
    )
    tools = coordinator_module._build_coordinator_tools()
    assert len(tools) == 5
    names = {tool.name for tool in tools}
    assert "get-current-date" in names
    assert "maps_around_search" in names


def test_build_coordinator_message_includes_today() -> None:
    message = coordinator_module._build_coordinator_message(
        "北京",
        "上海",
        "2025-08-01",
        passenger_count=2,
    )
    assert today_beijing_iso() in message
    assert "系统提示" in message
    assert "北京" in message and "上海" in message


def _coordinator_inputs(content: str) -> dict:
    return {"messages": [HumanMessage(content=content)]}


def _last_content(response: dict) -> str:
    content = response["messages"][-1].content
    return content if isinstance(content, str) else str(content)


async def _invoke_coordinator(coordinator, content: str) -> dict:
    """集成测试统一超时，避免 LLM+MCP 链无限挂起。"""
    return await asyncio.wait_for(
        coordinator.ainvoke(_coordinator_inputs(content)),
        timeout=settings.transport_coordinator_timeout_seconds,
    )


@pytest.mark.integration
@pytest.mark.timeout(200)
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY")
async def test_flight_query() -> None:
    """测试航班查询（参考 Handoffs：明天出发）。"""
    coordinator = await create_transport_coordinator_async()

    print("\n=== 测试航班查询 ===")
    response = await _invoke_coordinator(
        coordinator,
        f"我想从北京飞到上海，明天出发，请帮我查询航班。"
        f"（系统提示：今天北京时间 {today_beijing_iso()}）",
    )
    text = _last_content(response)
    print(f"\n协调器响应：\n{text}")

    assert text
    assert any(keyword in text for keyword in ("航班", "CA", "MU", "飞", "flight"))


@pytest.mark.integration
@pytest.mark.timeout(200)
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY")
async def test_train_query() -> None:
    """测试高铁查询（参考 Handoffs：明天 + 12306 MCP）。"""
    coordinator = await create_transport_coordinator_async()

    print("\n=== 测试高铁查询 ===")
    response = await _invoke_coordinator(
        coordinator,
        f"北京到西安，明天，坐高铁，帮我查一下车次。"
        f"（系统提示：今天北京时间 {today_beijing_iso()}）",
    )
    text = _last_content(response)
    print(f"\n协调器响应：\n{text}")

    assert text
    assert any(keyword in text for keyword in ("高铁", "车次", "G", "D", "火车", "西安"))


@pytest.mark.integration
@pytest.mark.timeout(200)
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY")
async def test_driving_route() -> None:
    """测试自驾路线（参考 Handoffs：高德 MCP）。"""
    coordinator = await create_transport_coordinator_async()

    print("\n=== 测试自驾路线 ===")
    response = await _invoke_coordinator(
        coordinator,
        "我打算自驾从北京到上海，帮我规划一下路线。",
    )
    text = _last_content(response)
    print(f"\n协调器响应：\n{text}")

    assert text
    assert any(keyword in text for keyword in ("自驾", "路线", "公里", "高速", "北京", "上海"))


@pytest.mark.integration
@pytest.mark.timeout(200)
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.mimo_api_key, reason="需要 MIMO_API_KEY")
async def test_auto_recommendation() -> None:
    """测试协调器自动推荐交通方式。"""
    coordinator = await create_transport_coordinator_async()
    response = await _invoke_coordinator(
        coordinator,
        "我想从北京去西安，8月1日出发，有什么推荐的交通方式吗？",
    )
    text = _last_content(response)
    assert text
    assert any(keyword in text for keyword in ("交通", "推荐", "航班", "高铁", "自驾"))


@pytest.mark.integration
@pytest.mark.timeout(200)
@pytest.mark.asyncio
async def test_auxiliary_mcp_tools_load() -> None:
    from app.mcp.auxiliary_tools import get_auxiliary_mcp_tools

    if not settings.mcp_train_url and not settings.amap_api_key:
        pytest.skip("需要 MCP_TRAIN_URL 或 AMAP_API_KEY")

    tools = await get_auxiliary_mcp_tools()
    assert len(tools) > 0
    names = [tool.name.lower() for tool in tools]
    assert any("around" in name for name in names)


async def _run_manual_transport_subagents_demo() -> None:
    """参考 Handoffs：依次跑航班 / 高铁 / 自驾集成测试。"""
    await test_flight_query()
    await test_train_query()
    await test_driving_route()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_manual_transport_subagents_demo())
