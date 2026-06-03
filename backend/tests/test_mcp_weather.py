"""MCP 天气层测试。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

import app.mcp.adapters.weather_adapter as weather_adapter_module
import app.mcp.client as mcp_client_module
from app.mcp.adapters.weather_adapter import get_weather_forecast
from app.mcp.client import build_mcp_connections
from app.mcp.providers.qweather import fetch_weather_markdown
from app.mcp.registry import get_registry, reset_registry
from app.mcp.servers.weather_server import get_weather_forecast as server_get_weather_forecast
from app.settings import settings
from app.tools.weather import fetch_weather_info


@pytest.fixture(autouse=True)
def reset_mcp_caches() -> None:
    reset_registry()
    mcp_client_module.reset_mcp_client()
    yield
    reset_registry()
    mcp_client_module.reset_mcp_client()


def test_build_mcp_connections_inprocess() -> None:
    with (
        patch.object(settings, "mcp_weather_transport", "inprocess"),
        patch.object(settings, "mcp_search_transport", "inprocess"),
    ):
        mcp_client_module.reset_mcp_client()
        assert build_mcp_connections() == {}


def test_build_mcp_connections_stdio() -> None:
    with patch.object(settings, "mcp_weather_transport", "stdio"):
        mcp_client_module.reset_mcp_client()
        connections = build_mcp_connections()
        assert "weather" in connections
        assert connections["weather"]["transport"] == "stdio"
        assert "-m" in connections["weather"]["args"]


def test_get_weather_forecast_inprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mcp_weather_transport", "inprocess")
    monkeypatch.setattr(
        weather_adapter_module,
        "fetch_weather_markdown",
        lambda city: f"markdown:{city}",
    )
    assert get_weather_forecast("西安") == "markdown:西安"


def test_get_weather_forecast_stdio(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "mcp_weather_transport", "stdio")
    mock_registry = MagicMock()
    mock_registry.call_tool_sync.return_value = "mcp:西安天气"
    monkeypatch.setattr(weather_adapter_module, "get_registry", lambda: mock_registry)

    assert get_weather_forecast("西安") == "mcp:西安天气"
    mock_registry.call_tool_sync.assert_called_once_with(
        "weather",
        "get_weather_forecast",
        {"city": "西安"},
    )


def test_tools_weather_delegates_to_adapter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.tools.weather.get_weather_forecast",
        lambda dest: f"tool:{dest}",
    )
    assert fetch_weather_info("成都") == "tool:成都"


def test_qweather_unconfigured_returns_placeholder() -> None:
    with patch.object(settings, "qweather_api_key", ""):
        text = fetch_weather_markdown("西安")
        assert "未配置" in text
        assert "西安" in text


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.qweather_api_key, reason="需要 QWEATHER_API_KEY")
@pytest.mark.skipif(not settings.qweather_base_url, reason="需要 QWEATHER_API_HOST")
async def test_weather_server_xian() -> None:
    """直接调用 weather_server 工具（中文城市名，非 adcode）。"""
    result = await server_get_weather_forecast("西安")
    assert result.strip()
    assert "天气" in result or "西安" in result


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(not settings.qweather_api_key, reason="需要 QWEATHER_API_KEY")
@pytest.mark.skipif(not settings.qweather_base_url, reason="需要 QWEATHER_API_HOST")
async def test_weather_server_beijing() -> None:
    result = await server_get_weather_forecast("北京")
    assert result.strip()
    assert "天气" in result or "北京" in result


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.skipif(
    settings.mcp_weather_transport != "stdio",
    reason="需要 MCP_WEATHER_TRANSPORT=stdio",
)
@pytest.mark.skipif(not settings.qweather_api_key, reason="需要 QWEATHER_API_KEY")
async def test_mcp_stdio_weather_roundtrip() -> None:
    """stdio 模式下 registry 调用本地 weather_server。"""
    registry = get_registry()
    text = await registry.call_tool(
        "weather",
        "get_weather_forecast",
        {"city": "西安"},
    )
    assert text.strip()
    assert "天气" in text or "西安" in text


async def _run_manual_weather_server_demo() -> None:
    """参考 Handoffs 脚本：手动打印西安/北京天气。"""
    print("=== 测试西安天气（city: 西安，参考 adcode 610100）===")
    print(await server_get_weather_forecast("西安"))

    print("\n=== 测试北京天气（city: 北京，参考 adcode 110000）===")
    print(await server_get_weather_forecast("北京"))


if __name__ == "__main__":
    import asyncio

    asyncio.run(_run_manual_weather_server_demo())
