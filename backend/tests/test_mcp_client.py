"""MCP 客户端 Manager 集成测试（参考 Handoffs test_print_mcp_tools）。"""

from __future__ import annotations

import json

import pytest

from app.mcp.client import (
    AIGOHOTEL_SERVER,
    AMAP_SERVER,
    SEARCH_SERVER,
    TRAIN_SERVER,
    VARIFLIGHT_SERVER,
    WEATHER_SERVER,
    build_manager_connections,
    normalize_server_names,
)
from app.mcp.manager import MCPClientManager, reset_mcp_manager


@pytest.fixture(autouse=True)
def reset_singleton() -> None:
    reset_mcp_manager()
    yield
    reset_mcp_manager()


def test_normalize_server_aliases() -> None:
    names = normalize_server_names(
        ["weather", "12306-mcp", "VariFlight-Aviation", "aigohotel-mcp"]
    )
    assert names == ["weather", TRAIN_SERVER, VARIFLIGHT_SERVER, AIGOHOTEL_SERVER]


def _print_tools(tools: list) -> None:
    print(f"\n共发现 {len(tools)} 个 MCP 工具")
    for index, tool in enumerate(tools, 1):
        print(f"\n工具 [{index}]")
        print(f"  名称: {tool.name}")
        print(f"  描述: {tool.description}")
        print("  参数结构:")
        schema = _tool_args_schema(tool)
        if schema is not None:
            print(json.dumps(schema, indent=2, ensure_ascii=False))
        else:
            print("    (无参数 schema)")


def _tool_args_schema(tool: object) -> dict | None:
    args_schema = getattr(tool, "args_schema", None)
    if args_schema is None:
        return None
    if isinstance(args_schema, dict):
        return args_schema
    if hasattr(args_schema, "model_json_schema"):
        return args_schema.model_json_schema()
    if hasattr(args_schema, "schema"):
        return args_schema.schema()
    return {"raw": str(args_schema)}


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mcp_tools_local_servers() -> None:
    """本地 stdio：weather + search（无需外部 API Key）。"""
    manager = await MCPClientManager.get_instance(
        servers=[WEATHER_SERVER, SEARCH_SERVER],
    )
    try:
        tools = await manager.get_tools()
        _print_tools(tools)
        assert len(tools) >= 2
        names = {tool.name for tool in tools}
        assert "get_weather_forecast" in names
        assert "search_travel_info" in names
    finally:
        await manager.close()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_print_mcp_tools_all_configured() -> None:
    """
    加载所有已配置 MCP 服务（参考 Handoffs 全量列表）。

    参考名 → 本项目：12306-mcp→train，VariFlight→variflight，aigohotel-mcp→aigohotel
    无 API Key 的外部服务会自动跳过，不会出现在连接表中。
    """
    reference_servers = [
        "weather",
        "search",
        "amap",
        "12306-mcp",
        "VariFlight-Aviation",
        "aigohotel-mcp",
    ]
    normalized = normalize_server_names(reference_servers)
    available = list(build_manager_connections(normalized).keys())

    print("\n" + "=" * 60)
    print("正在初始化 MCP 客户端管理器...")
    print(f"请求服务: {reference_servers}")
    print(f"实际连接: {available}")

    if not available:
        pytest.skip("无可用 MCP 连接（请配置 API Key 或检查 MCP_TRAIN_URL）")

    manager = await MCPClientManager.get_instance(servers=reference_servers)
    try:
        tools = await manager.get_tools()
        _print_tools(tools)
        assert len(tools) > 0, "应该至少有一个工具"

        connected = set(manager.servers)
        assert WEATHER_SERVER in connected
        assert SEARCH_SERVER in connected
    finally:
        print("\n关闭 MCP 连接...")
        await manager.close()


async def _run_manual_mcp_tools_demo() -> None:
    """手动运行：打印所有已配置 MCP 工具。"""
    reference_servers = [
        WEATHER_SERVER,
        SEARCH_SERVER,
        AMAP_SERVER,
        TRAIN_SERVER,
        VARIFLIGHT_SERVER,
        AIGOHOTEL_SERVER,
    ]
    available = list(build_manager_connections(reference_servers).keys())
    print(f"将连接: {available}")

    manager = await MCPClientManager.get_instance(servers=reference_servers)
    try:
        _print_tools(await manager.get_tools())
    finally:
        await manager.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_manual_mcp_tools_demo())
