"""

航班查询 Subagent



有 VARIFLIGHT_API_KEY 时绑定 Variflight Aviation MCP 多工具；

否则回退 mock query_flights_from_mcp。

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

from app.graph.transport_state import FlightOption

from app.mcp.aviation_tools import get_aviation_mcp_tools_sync

from app.mcp.registry import run_async
from app.settings import settings



_FLIGHT_MCP_PROMPT = """你是航班查询专家，负责航班查询、机票价格比较及航班状态查询。



**可用工具**（Variflight Aviation MCP）：

1. 日期与基础：`getTodayDate` 等——用户说「明天」时先取今天日期

2. 航班查询：`searchFlightsByDepArr`、`searchFlightsByNumber`、`getFlightTransferInfo`、`searchFlightItineraries` 等



**IATA 示例**：北京=BJS/PEK，上海=SHA/PVG，西安=XIY，成都=CTU



**流程**：提取出发/到达/日期 → 相对日期先调 getTodayDate → 选 depcity/arrcity 或 dep/arr → 调用工具



**输出格式**：

✈️ 航班 {航班号}

- 出发：{机场} {时间}

- 到达：{机场} {时间}

- 价格：¥{价格}



**注意**：必须调用工具；日期 YYYY-MM-DD；无结果时明确告知。"""



_FLIGHT_FALLBACK_PROMPT = """你是航班查询专家。



**职责**：

1. 接收出发城市、目的地城市、出发日期

2. 调用 query_flights_from_mcp 工具查询航班

3. 整理航班信息，按价格从低到高排序



**注意**：一定要调用工具，不要编造数据。"""





def _build_mock_flights(

    origin: str,

    destination: str,

    departure_date: str,

) -> list[FlightOption]:

    return [

        {

            "flight_number": "CA1234",

            "airline": "中国国航",

            "departure_airport": f"{origin}首都国际机场",

            "arrival_airport": f"{destination}浦东国际机场",

            "departure_time": f"{departure_date} 08:00",

            "arrival_time": f"{departure_date} 10:30",

            "duration": "2小时30分",

            "price": 800.0,

            "cabin_class": "经济舱",

            "available_seats": 45,

        },

        {

            "flight_number": "MU5678",

            "airline": "东方航空",

            "departure_airport": f"{origin}首都国际机场",

            "arrival_airport": f"{destination}虹桥国际机场",

            "departure_time": f"{departure_date} 14:00",

            "arrival_time": f"{departure_date} 16:20",

            "duration": "2小时20分",

            "price": 750.0,

            "cabin_class": "经济舱",

            "available_seats": 23,

        },

    ]





def fetch_flights_json(origin: str, destination: str, departure_date: str) -> str:

    """无 Variflight MCP 时的 mock JSON。"""

    flights = _build_mock_flights(origin, destination, departure_date)

    return json.dumps(flights, ensure_ascii=False, indent=2)





def parse_flight_options(raw: str) -> list[FlightOption]:

    data: Any = json.loads(raw)

    if not isinstance(data, list):

        return []

    return [item for item in data if isinstance(item, dict)]





def format_flight_options(flights: list[FlightOption]) -> str:

    if not flights:

        return "未找到可用航班。"



    sorted_flights = sorted(flights, key=lambda item: item.get("price", 0))

    lines = [f"找到 {len(sorted_flights)} 个航班选项：", ""]

    for index, flight in enumerate(sorted_flights, start=1):

        lines.extend(

            [

                f"{index}. 【{flight['flight_number']}】 {flight['airline']} {flight['flight_number']}",

                f"   - 出发：{flight['departure_airport']} {flight['departure_time']}",

                f"   - 到达：{flight['arrival_airport']} {flight['arrival_time']}",

                f"   - 时长：{flight['duration']}",

                f"   - 价格：¥{flight['price']}",

                f"   - 余票：{flight['available_seats']} 座",

                "",

            ]

        )

    return "\n".join(lines).strip()





@tool

def query_flights_from_mcp(origin: str, destination: str, departure_date: str) -> str:

    """从本地 mock 查询航班（无 Variflight MCP 时使用）。"""

    logger.info("mock 航班查询: {} -> {}, {}", origin, destination, departure_date)

    return fetch_flights_json(origin, destination, departure_date)





def _resolve_flight_tools() -> tuple[list[BaseTool], str]:

    aviation_tools = get_aviation_mcp_tools_sync()

    if aviation_tools:

        return aviation_tools, _FLIGHT_MCP_PROMPT

    return [query_flights_from_mcp], _FLIGHT_FALLBACK_PROMPT





@lru_cache(maxsize=1)

def create_flight_subagent():

    """创建航班 Subagent（MiMo + Variflight MCP 或 mock 工具）。"""

    tools, prompt = _resolve_flight_tools()

    model = get_chat_model().bind(temperature=0.1)

    agent = create_transport_react_agent(model, tools, prompt=prompt)

    logger.info("航班 Subagent 创建完成，工具数={}", len(tools))

    return agent





async def create_flight_subagent_async():

    """异步创建（与参考 Handoffs 接口一致）。"""

    return create_flight_subagent()





def clear_flight_subagent_cache() -> None:

    create_flight_subagent.cache_clear()





def _flight_query_message(

    origin: str,

    destination: str,

    departure_date: str,

    *,

    passenger_count: int = 1,

) -> str:

    return (

        f"请查询从 {origin} 到 {destination}、出发日期 {departure_date} 的航班，"

        f"乘客 {passenger_count} 人。按价格从低到高整理后返回。"

    )





def _extract_agent_text(result: dict) -> str:

    messages = result.get("messages") or []

    if not messages:

        return ""

    content = messages[-1].content

    return content if isinstance(content, str) else str(content)





def _fallback_flight_report(origin: str, destination: str, departure_date: str) -> str:

    return format_flight_options(

        parse_flight_options(fetch_flights_json(origin, destination, departure_date))

    )





def run_flight_subagent(

    origin: str,

    destination: str,

    departure_date: str,

    *,

    passenger_count: int = 1,

) -> str:

    if not settings.mimo_api_key:

        logger.warning("MIMO_API_KEY 未配置，使用本地格式化航班结果")

        return _fallback_flight_report(origin, destination, departure_date)



    agent = create_flight_subagent()

    message = _flight_query_message(

        origin, destination, departure_date, passenger_count=passenger_count

    )

    try:

        result = run_async(agent.ainvoke({"messages": [HumanMessage(content=message)]}))

        text = _extract_agent_text(result)

        return text or _fallback_flight_report(origin, destination, departure_date)

    except Exception as exc:

        logger.warning("航班 Subagent 失败，回退本地格式化: {}", exc)

        return _fallback_flight_report(origin, destination, departure_date)





async def run_flight_subagent_async(

    origin: str,

    destination: str,

    departure_date: str,

    *,

    passenger_count: int = 1,

) -> str:

    if not settings.mimo_api_key:

        return _fallback_flight_report(origin, destination, departure_date)



    agent = create_flight_subagent()

    message = _flight_query_message(

        origin, destination, departure_date, passenger_count=passenger_count

    )

    try:

        result = await agent.ainvoke({"messages": [HumanMessage(content=message)]})

        text = _extract_agent_text(result)

        return text or _fallback_flight_report(origin, destination, departure_date)

    except Exception as exc:

        logger.warning("航班 Subagent 异步失败，回退本地格式化: {}", exc)

        return _fallback_flight_report(origin, destination, departure_date)


