"""
高铁查询 Subagent

有 MCP_TRAIN_URL 时绑定 12306 MCP 多工具；否则回退 mock query_trains_from_mcp。
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
from app.graph.transport_state import TrainOption
from app.mcp.railway_tools import get_railway_mcp_tools_sync
from app.mcp.registry import run_async
from app.settings import settings

_TRAIN_MCP_PROMPT = """你是高铁查询专家，负责火车票查询、行程规划及车次详情查询。

**可用工具**（12306 MCP）：
1. 日期：`get-current-date`——用户说「明天/下周」时必须先调用
2. 站点编码：
   - `get-station-code-of-citys`：城市名（如「北京」）
   - `get-station-code-by-names`：具体站名（如「北京南」）
   - `get-stations-code-in-city`：某城市所有站
3. 余票：
   - `get-tickets`：直达车次
   - `get-interline-tickets`：中转方案（直达无票或用户问中转时使用）
4. 经停：`get-train-route-stations`——询问经停站/时刻表时使用

**流程**：解析日期 → 城市/站名转 station_code（禁止中文直传查询接口）→ get-tickets → 必要时 get-interline-tickets

**输出**：车次、起降时间、时长、席别余票与价格；中转方案标明中转站与换乘时间。

**注意**：必须调用工具；无票时明确告知。"""

_TRAIN_FALLBACK_PROMPT = """你是高铁查询专家。

**职责**：调用 query_trains_from_mcp 查询车次，按出发时间排序返回。

**注意**：一定要调用工具，不要编造数据。"""


def _build_mock_trains(
    origin: str,
    destination: str,
    departure_date: str,
) -> list[TrainOption]:
    return [
        {
            "train_number": "G123",
            "departure_station": f"{origin}站",
            "arrival_station": f"{destination}站",
            "departure_time": f"{departure_date} 09:00",
            "arrival_time": f"{departure_date} 13:30",
            "duration": "4小时30分",
            "seat_types": ["商务座", "一等座", "二等座"],
            "prices": {"商务座": 1200.0, "一等座": 650.0, "二等座": 410.0},
            "available": True,
        },
        {
            "train_number": "D456",
            "departure_station": f"{origin}站",
            "arrival_station": f"{destination}站",
            "departure_time": f"{departure_date} 11:00",
            "arrival_time": f"{departure_date} 16:10",
            "duration": "5小时10分",
            "seat_types": ["一等座", "二等座"],
            "prices": {"一等座": 480.0, "二等座": 300.0},
            "available": True,
        },
    ]


def fetch_trains_json(origin: str, destination: str, departure_date: str) -> str:
    trains = _build_mock_trains(origin, destination, departure_date)
    return json.dumps(trains, ensure_ascii=False, indent=2)


def parse_train_options(raw: str) -> list[TrainOption]:
    data: Any = json.loads(raw)
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _format_seat_prices(prices: dict[str, float]) -> list[str]:
    order = ["二等座", "一等座", "商务座"]
    lines: list[str] = []
    for seat in order:
        if seat in prices:
            lines.append(f"     * {seat}：¥{prices[seat]}")
    for seat, price in prices.items():
        if seat not in order:
            lines.append(f"     * {seat}：¥{price}")
    return lines


def format_train_options(trains: list[TrainOption]) -> str:
    if not trains:
        return "未找到可用车次。"

    sorted_trains = sorted(trains, key=lambda item: item.get("departure_time", ""))
    lines = [f"找到 {len(sorted_trains)} 个车次选项：", ""]
    for index, train in enumerate(sorted_trains, start=1):
        status = "有票" if train.get("available", True) else "无票"
        lines.extend(
            [
                f"{index}. 【{train['train_number']}】 {train['train_number']}",
                f"   - 出发：{train['departure_station']} {train['departure_time']}",
                f"   - 到达：{train['arrival_station']} {train['arrival_time']}",
                f"   - 时长：{train['duration']}",
                "   - 座位与价格：",
                *_format_seat_prices(train.get("prices") or {}),
                f"   - 状态：{status}",
                "",
            ]
        )
    return "\n".join(lines).strip()


@tool
def query_trains_from_mcp(origin: str, destination: str, departure_date: str) -> str:
    """从本地 mock 查询高铁（无 12306 MCP 时使用）。"""
    logger.info("mock 高铁查询: {} -> {}, {}", origin, destination, departure_date)
    return fetch_trains_json(origin, destination, departure_date)


def _resolve_train_tools() -> tuple[list[BaseTool], str]:
    railway_tools = get_railway_mcp_tools_sync()
    if railway_tools:
        return railway_tools, _TRAIN_MCP_PROMPT
    return [query_trains_from_mcp], _TRAIN_FALLBACK_PROMPT


@lru_cache(maxsize=1)
def create_train_subagent():
    tools, prompt = _resolve_train_tools()
    model = get_chat_model().bind(temperature=0.1)
    agent = create_transport_react_agent(model, tools, prompt=prompt)
    logger.info("高铁 Subagent 创建完成，工具数={}", len(tools))
    return agent


async def create_train_subagent_async():
    return create_train_subagent()


def clear_train_subagent_cache() -> None:
    create_train_subagent.cache_clear()


def _train_query_message(origin: str, destination: str, departure_date: str) -> str:
    return (
        f"请查询从 {origin} 到 {destination}、出发日期 {departure_date} 的高铁/火车，"
        "按出发时间从早到晚整理后返回。"
    )


def _extract_agent_text(result: dict) -> str:
    messages = result.get("messages") or []
    if not messages:
        return ""
    content = messages[-1].content
    return content if isinstance(content, str) else str(content)


def _fallback_train_report(origin: str, destination: str, departure_date: str) -> str:
    return format_train_options(
        parse_train_options(fetch_trains_json(origin, destination, departure_date))
    )


def run_train_subagent(origin: str, destination: str, departure_date: str) -> str:
    if not settings.mimo_api_key:
        logger.warning("MIMO_API_KEY 未配置，使用本地格式化车次结果")
        return _fallback_train_report(origin, destination, departure_date)

    agent = create_train_subagent()
    try:
        result = run_async(
            agent.ainvoke(
                {"messages": [HumanMessage(content=_train_query_message(origin, destination, departure_date))]}
            )
        )
        text = _extract_agent_text(result)
        return text or _fallback_train_report(origin, destination, departure_date)
    except Exception as exc:
        logger.warning("高铁 Subagent 失败，回退本地格式化: {}", exc)
        return _fallback_train_report(origin, destination, departure_date)


async def run_train_subagent_async(
    origin: str,
    destination: str,
    departure_date: str,
) -> str:
    if not settings.mimo_api_key:
        return _fallback_train_report(origin, destination, departure_date)

    agent = create_train_subagent()
    try:
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=_train_query_message(origin, destination, departure_date))]}
        )
        text = _extract_agent_text(result)
        return text or _fallback_train_report(origin, destination, departure_date)
    except Exception as exc:
        logger.warning("高铁 Subagent 异步失败，回退本地格式化: {}", exc)
        return _fallback_train_report(origin, destination, departure_date)
