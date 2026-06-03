"""
自驾路线规划 Subagent

有 AMAP_API_KEY 时绑定高德 MCP（maps_geo + maps_direction_driving）；
否则回退 mock plan_driving_route_from_mcp。
Route 1：graph/nodes → app.tools.transport → 本模块。
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, tool
from app.agents.transport._react import create_transport_react_agent
from loguru import logger

from app.ai.llm import get_chat_model
from app.graph.transport_state import DrivingRoute
from app.mcp.amap_tools import get_amap_mcp_tools_sync
from app.mcp.registry import run_async
from app.settings import settings

_DRIVING_MCP_PROMPT = """你是自驾路线规划专家，负责驾车路线、距离时长及费用预估。

**可用工具**（高德 MCP）：
1. `maps_geo`：地址/地名 → 经纬度（格式：经度,纬度）
2. `maps_direction_driving`：驾车路线（参数必须是坐标，不能是地址）

**流程**：
1. 对起点、终点分别调用 `maps_geo`
2. 用坐标调用 `maps_direction_driving`
3. 若 geo 失败，请用户提供更详细地址

**输出格式**：
🚗 **自驾路线方案**
- 起点 / 终点
- 总距离、预计时长
- 路线详情、过路费
- 油费估算（可按 7L/100km、8 元/L）
- 注意事项

**注意**：必须调用工具，不要编造数据。"""

_DRIVING_FALLBACK_PROMPT = """你是自驾路线规划专家。

**职责**：调用 plan_driving_route_from_mcp 规划路线并对比方案。

**注意**：一定要调用工具，不要编造数据。"""


def _build_mock_routes(origin: str, destination: str) -> list[DrivingRoute]:
    return [
        {
            "route_name": "推荐路线（高速优先）",
            "distance": "1200 公里",
            "duration": "约 12 小时",
            "toll_fee": 450.0,
            "fuel_cost": 600.0,
            "steps": [
                f"从{origin}市区出发",
                "进入京沪高速（G2）",
                f"到达{destination}市区",
            ],
            "waypoints": ["天津", "济南", "南京"],
        },
        {
            "route_name": "省钱路线（国道优先）",
            "distance": "1250 公里",
            "duration": "约 15 小时",
            "toll_fee": 200.0,
            "fuel_cost": 650.0,
            "steps": [f"从{origin}出发", f"到达{destination}"],
            "waypoints": ["天津", "济南"],
        },
    ]


def fetch_driving_routes_json(origin: str, destination: str) -> str:
    routes = _build_mock_routes(origin, destination)
    return json.dumps(routes, ensure_ascii=False, indent=2)


def parse_driving_routes(raw: str) -> list[DrivingRoute]:
    data: Any = json.loads(raw)
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def format_driving_routes(routes: list[DrivingRoute]) -> str:
    if not routes:
        return "未找到可用自驾路线。"

    lines = [f"找到 {len(routes)} 个路线方案：", ""]
    for index, route in enumerate(routes, start=1):
        waypoints = "、".join(route.get("waypoints") or [])
        step_lines = "\n     ".join(f"- {step}" for step in (route.get("steps") or []))
        lines.extend(
            [
                f"{index}. 【{route['route_name']}】",
                f"   - 总距离：{route['distance']}",
                f"   - 预计时长：{route['duration']}",
                f"   - 过路费：¥{route['toll_fee']}",
                f"   - 油费估算：¥{route['fuel_cost']}",
                f"   - 途经城市：{waypoints}",
                f"   - 主要路段：\n     {step_lines}",
                "",
            ]
        )
    return "\n".join(lines).strip()


@tool
def plan_driving_route_from_mcp(origin: str, destination: str) -> str:
    """从本地 mock 规划自驾路线（无高德 MCP 时使用）。"""
    logger.info("mock 自驾规划: {} -> {}", origin, destination)
    return fetch_driving_routes_json(origin, destination)


def _resolve_driving_tools() -> tuple[list[BaseTool], str]:
    amap_tools = get_amap_mcp_tools_sync()
    if amap_tools:
        return amap_tools, _DRIVING_MCP_PROMPT
    return [plan_driving_route_from_mcp], _DRIVING_FALLBACK_PROMPT


@lru_cache(maxsize=1)
def create_driving_subagent():
    tools, prompt = _resolve_driving_tools()
    model = get_chat_model().bind(temperature=0.1)
    agent = create_transport_react_agent(model, tools, prompt=prompt)
    logger.info("自驾 Subagent 创建完成，工具数={}", len(tools))
    return agent


async def create_driving_subagent_async():
    return create_driving_subagent()


def clear_driving_subagent_cache() -> None:
    create_driving_subagent.cache_clear()


def _driving_query_message(origin: str, destination: str) -> str:
    return f"请规划从 {origin} 到 {destination} 的自驾路线，对比不同方案后返回推荐。"


def _extract_agent_text(result: dict) -> str:
    messages = result.get("messages") or []
    if not messages:
        return ""
    content = messages[-1].content
    return content if isinstance(content, str) else str(content)


def _fallback_driving_report(origin: str, destination: str) -> str:
    return format_driving_routes(
        parse_driving_routes(fetch_driving_routes_json(origin, destination))
    )


def run_driving_subagent(origin: str, destination: str) -> str:
    if not settings.mimo_api_key:
        logger.warning("MIMO_API_KEY 未配置，使用本地格式化路线结果")
        return _fallback_driving_report(origin, destination)

    agent = create_driving_subagent()
    try:
        result = run_async(
            agent.ainvoke(
                {"messages": [HumanMessage(content=_driving_query_message(origin, destination))]}
            )
        )
        text = _extract_agent_text(result)
        return text or _fallback_driving_report(origin, destination)
    except Exception as exc:
        logger.warning("自驾 Subagent 失败，回退本地格式化: {}", exc)
        return _fallback_driving_report(origin, destination)


async def run_driving_subagent_async(origin: str, destination: str) -> str:
    if not settings.mimo_api_key:
        return _fallback_driving_report(origin, destination)

    agent = create_driving_subagent()
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=_driving_query_message(origin, destination))]}
        )
        text = _extract_agent_text(result)
        return text or _fallback_driving_report(origin, destination)
    except Exception as exc:
        logger.warning("自驾 Subagent 异步失败，回退本地格式化: {}", exc)
        return _fallback_driving_report(origin, destination)
