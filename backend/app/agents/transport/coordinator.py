"""

交通规划协调器（主 Agent）



Subagents（航班 / 高铁 / 自驾）+ MCP 辅助工具，由协调器按需调用。

Route 1：graph/nodes → app.tools.transport → 本模块。

"""



from __future__ import annotations

import asyncio
from collections.abc import Callable
from functools import lru_cache

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool, tool
from loguru import logger

from app.agents.transport._react import create_transport_react_agent
from app.agents.transport.driving_subagent import (
    _fallback_driving_report,
    create_driving_subagent,
    run_driving_subagent,
)
from app.agents.transport.flight_subagent import (
    _fallback_flight_report,
    create_flight_subagent,
    run_flight_subagent,
)
from app.agents.transport.train_subagent import (
    _fallback_train_report,
    create_train_subagent,
    run_train_subagent,
)

from app.ai.llm import get_chat_model

from app.mcp.auxiliary_tools import get_auxiliary_mcp_tools_sync
from app.mcp.registry import run_async
from app.settings import settings

from app.tools.datetime_tools import get_current_date, today_beijing_iso



_COORDINATOR_PROMPT = """你是交通规划协调专家。



**交通查询（主要）**：

1. query_flights：查询航班（长途、速度快）

2. query_trains：查询高铁/火车（中短途、舒适）

3. plan_driving_route：规划自驾路线（灵活、深度游）



**辅助工具（按需）**：

- get-current-date：获取今天日期（**本地工具**，用户说「今天/明天/下周」时必须先调用）

- maps_around_search：周边 POI 搜索（高德）

- getFutureWeather*：机场/目的地未来天气（若可用）



**工作流程**：

1. 理解出发地、目的地、日期、人数

2. 涉及相对日期时，先 get-current-date 再查票/路线

3. 用户指定方式则直接调用对应工具；未指定则按距离推荐：

   * < 300km：高铁

   * 300–1000km：高铁或航班

   * > 1000km：航班

4. 整合结果，清晰展示；可询问时间优先还是价格优先



**注意**：

- 必须调用工具获取实时信息，不要编造

- 航班/高铁需要日期（YYYY-MM-DD）；自驾不需要日期

- 查询失败时说明原因并提供替代方案

"""





def _extract_agent_text(result: dict) -> str:

    messages = result.get("messages") or []

    if not messages:

        return ""

    content = messages[-1].content

    return content if isinstance(content, str) else str(content)


async def _invoke_subagent_safe(
    agent_getter: Callable[[], object],
    content: str,
    fallback: Callable[[], str],
) -> str:
    """Subagent 超时或 MCP 失败时回退本地 mock，避免整链崩溃或无限等待。"""
    try:
        result = await asyncio.wait_for(
            agent_getter().ainvoke({"messages": [HumanMessage(content=content)]}),
            timeout=settings.transport_subagent_timeout_seconds,
        )
        text = _extract_agent_text(result)
        if text.strip():
            return text
    except Exception as exc:
        logger.warning("Subagent 调用失败，回退本地 mock: {}", exc)
    return fallback()





@lru_cache(maxsize=1)

def _get_flight_subagent():

    return create_flight_subagent()





@lru_cache(maxsize=1)

def _get_train_subagent():

    return create_train_subagent()





@lru_cache(maxsize=1)

def _get_driving_subagent():

    return create_driving_subagent()





@tool
async def query_flights(
    origin: str,
    destination: str,
    departure_date: str,
    passenger_count: int = 1,
) -> str:
    """查询航班信息。需要提供出发城市、目的地城市、出发日期、乘客数量。"""
    logger.info("协调器调用航班 Subagent: {} -> {}", origin, destination)
    content = (
        f"请查询从 {origin} 到 {destination} 的航班，"
        f"出发日期是 {departure_date}，共 {passenger_count} 人。"
    )
    return await _invoke_subagent_safe(
        _get_flight_subagent,
        content,
        lambda: _fallback_flight_report(origin, destination, departure_date),
    )





@tool
async def query_trains(origin: str, destination: str, departure_date: str) -> str:
    """查询高铁/火车信息。需要提供出发城市、目的地城市、出发日期。"""
    logger.info("协调器调用高铁 Subagent: {} -> {}", origin, destination)
    content = (
        f"请查询从 {origin} 到 {destination} 的高铁，"
        f"出发日期是 {departure_date}。"
    )
    return await _invoke_subagent_safe(
        _get_train_subagent,
        content,
        lambda: _fallback_train_report(origin, destination, departure_date),
    )





@tool
async def plan_driving_route(origin: str, destination: str) -> str:
    """规划自驾路线。需要提供出发地、目的地（地址或地名）。"""
    logger.info("协调器调用自驾 Subagent: {} -> {}", origin, destination)
    content = f"请规划从 {origin} 到 {destination} 的自驾路线。"
    return await _invoke_subagent_safe(
        _get_driving_subagent,
        content,
        lambda: _fallback_driving_report(origin, destination),
    )





def _build_coordinator_tools() -> list[BaseTool]:

    tools: list[BaseTool] = [
        query_flights,
        query_trains,
        plan_driving_route,
        get_current_date,
    ]

    try:

        tools.extend(get_auxiliary_mcp_tools_sync())

    except Exception as exc:

        logger.warning("协调器辅助工具加载失败: {}", exc)

    return tools





@lru_cache(maxsize=1)

def create_transport_coordinator():

    """创建交通规划协调器（主 Agent，同步）。"""

    tools = _build_coordinator_tools()

    agent = create_transport_react_agent(
        get_chat_model().bind(temperature=0.7),
        tools,
        prompt=_COORDINATOR_PROMPT,
    )

    logger.info("交通规划协调器创建完成，工具数={}", len(tools))

    return agent





async def create_transport_coordinator_async():

    """异步创建（与参考 Handoffs 接口一致）。"""

    return create_transport_coordinator()





def clear_transport_coordinator_cache() -> None:

    create_transport_coordinator.cache_clear()





def _build_coordinator_message(

    origin: str,

    destination: str,

    departure_date: str,

    *,

    passenger_count: int = 1,

    user_preference: str = "",

    transport_type: str | None = None,

) -> str:

    type_labels = {

        "flight": "航班",

        "train": "高铁",

        "driving": "自驾",

    }

    if transport_type:

        label = type_labels.get(transport_type, transport_type)

        message = (

            f"我想从 {origin} 去 {destination}，"

            f"出发日期是 {departure_date}，"

            f"共 {passenger_count} 人，"

            f"交通方式选择 {label}，"

            f"请帮我查询详细信息。"

        )

    else:

        message = (

            f"我想从 {origin} 去 {destination}，"

            f"出发日期是 {departure_date}，"

            f"共 {passenger_count} 人，"

            f"请推荐合适的交通方式并提供详细信息。"

        )

    if user_preference.strip():

        message += f" 用户补充说明：{user_preference.strip()}"

    message += f"（系统提示：今天北京时间 {today_beijing_iso()}）"

    return message





def _fallback_transport_report(

    origin: str,

    destination: str,

    departure_date: str,

) -> str:

    return "\n\n".join(

        [

            "### 航班\n" + run_flight_subagent(origin, destination, departure_date),

            "### 高铁\n" + run_train_subagent(origin, destination, departure_date),

            "### 自驾\n" + run_driving_subagent(origin, destination),

        ]

    )





def run_transport_coordinator(

    origin: str,

    destination: str,

    departure_date: str,

    *,

    passenger_count: int = 1,

    user_preference: str = "",

    transport_type: str | None = None,

) -> str:

    fallback = _fallback_transport_report(origin, destination, departure_date)

    if not settings.mimo_api_key:

        logger.warning("MIMO_API_KEY 未配置，协调器回退为三种方式并列查询")

        return fallback



    coordinator = create_transport_coordinator()

    try:

        result = run_async(
            coordinator.ainvoke(
                {
                    "messages": [
                        HumanMessage(
                            content=_build_coordinator_message(
                                origin,
                                destination,
                                departure_date,
                                passenger_count=passenger_count,
                                user_preference=user_preference,
                                transport_type=transport_type,
                            )
                        )
                    ]
                }
            )
        )

        text = _extract_agent_text(result)

        return text or fallback

    except Exception as exc:

        logger.warning("交通协调器失败，回退为三种方式并列查询: {}", exc)

        return fallback





async def run_transport_coordinator_async(

    origin: str,

    destination: str,

    departure_date: str,

    *,

    passenger_count: int = 1,

    user_preference: str = "",

    transport_type: str | None = None,

) -> str:

    fallback = _fallback_transport_report(origin, destination, departure_date)

    if not settings.mimo_api_key:

        return fallback



    coordinator = create_transport_coordinator()

    try:

        result = await coordinator.ainvoke(

            {

                "messages": [

                    HumanMessage(

                        content=_build_coordinator_message(

                            origin,

                            destination,

                            departure_date,

                            passenger_count=passenger_count,

                            user_preference=user_preference,

                            transport_type=transport_type,

                        )

                    )

                ]

            }

        )

        text = _extract_agent_text(result)

        return text or fallback

    except Exception as exc:

        logger.warning("交通协调器异步失败，回退为三种方式并列查询: {}", exc)

        return fallback


