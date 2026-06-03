"""目的地 Router：分类后并行 explore（agents）+ weather（tools）。"""

from __future__ import annotations

from operator import add
from typing import Annotated, Literal, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from loguru import logger
from pydantic import BaseModel, Field

from app.agents.destination.explore_agent import run_explore_agent
from app.ai.llm import get_chat_model
from app.settings import settings
from app.tools.weather import fetch_weather_info


class Classification(TypedDict):
    agent: Literal["explore", "weather"]
    query: str


class AgentOutput(TypedDict):
    agent_name: str
    result: str


class DestinationRouterState(TypedDict):
    original_query: str
    destination: str
    classifications: list[Classification]
    agent_results: Annotated[list[AgentOutput], add]
    final_report: str


class AgentClassification(BaseModel):
    agent: Literal["explore", "weather"] = Field(description="explore 或 weather")
    query: str = Field(description="针对该 Agent 的子查询")


class ClassificationResult(BaseModel):
    classifications: list[AgentClassification] = Field(
        description="需要并行调用的 Agent 及子查询",
    )


class WorkerState(TypedDict):
    query: str
    destination: str


def classifier_node(state: DestinationRouterState) -> dict:
    logger.info("分类器分析查询: {}", state["original_query"])
    destination = state["destination"]
    query = state["original_query"]

    if not settings.mimo_api_key:
        return {"classifications": _default_classifications(destination, query)}

    try:
        structured_llm = get_chat_model().bind(temperature=0).with_structured_output(
            ClassificationResult
        )
        result: ClassificationResult = structured_llm.invoke(
            [
                SystemMessage(content=_CLASSIFIER_SYSTEM_PROMPT),
                HumanMessage(content=f"目的地：{destination}\n查询：{query}"),
            ],
        )
        classifications = [
            {"agent": item.agent, "query": item.query} for item in result.classifications
        ]
    except Exception as exc:
        logger.warning("分类器失败，规则回退: {}", exc)
        classifications = _default_classifications(destination, query)

    logger.info("分类完成: {} 个分支", len(classifications))
    return {"classifications": classifications}


def _default_classifications(destination: str, query: str) -> list[Classification]:
    weather_keywords = ("天气", "气温", "下雨", "降雨", "温度")
    comprehensive_keywords = ("推荐", "攻略", "旅游")

    has_weather = any(k in query for k in weather_keywords)
    has_comprehensive = any(k in query for k in comprehensive_keywords)

    if has_weather and not has_comprehensive:
        return [{"agent": "weather", "query": f"{destination} 天气"}]
    if has_comprehensive:
        return [
            {"agent": "explore", "query": query},
            {"agent": "weather", "query": f"{destination} 天气"},
        ]
    return [{"agent": "explore", "query": query}]


def route_to_agents(state: DestinationRouterState) -> list[Send]:
    return [
        Send(item["agent"], {"query": item["query"], "destination": state["destination"]})
        for item in state["classifications"]
    ]


def explore_agent_node(state: WorkerState) -> dict:
    destination = state["destination"]
    query = state["query"]
    logger.info("explore 节点: {} / {}", destination, query)
    result = run_explore_agent(destination, query)
    return {"agent_results": [{"agent_name": "explore", "result": result}]}


def weather_agent_node(state: WorkerState) -> dict:
    destination = state["destination"]
    logger.info("weather 节点: {}", destination)
    result = fetch_weather_info(destination)
    return {"agent_results": [{"agent_name": "weather", "result": result}]}


def synthesizer_node(state: DestinationRouterState) -> dict:
    results = state.get("agent_results") or []
    if not results:
        return {"final_report": "未找到相关信息。"}
    sections = [f"**{item['agent_name']}**\n{item['result']}" for item in results]
    return {"final_report": "\n\n".join(sections)}


def create_destination_router():
    workflow = StateGraph(DestinationRouterState)
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("explore", explore_agent_node)
    workflow.add_node("weather", weather_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.add_edge(START, "classifier")
    workflow.add_conditional_edges("classifier", route_to_agents, ["explore", "weather"])
    workflow.add_edge("explore", "synthesizer")
    workflow.add_edge("weather", "synthesizer")
    workflow.add_edge("synthesizer", END)
    return workflow.compile()


_router = None


def get_destination_router():
    global _router
    if _router is None:
        _router = create_destination_router()
    return _router


def run_destination_router(*, destination: str, original_query: str | None = None) -> str:
    query = original_query or f"推荐{destination}旅游"
    result = get_destination_router().invoke(
        {
            "original_query": query,
            "destination": destination,
            "classifications": [],
            "agent_results": [],
            "final_report": "",
        },
    )
    return str(result.get("final_report") or "")


_CLASSIFIER_SYSTEM_PROMPT = """分析旅行查询，输出 classifications 列表。

Agent 类型：
- explore：攻略、景点、美食、住宿、交通（知识库检索，由探索 Agent 自主选工具）
- weather：天气、气温、降雨

规则：攻略类 → explore；纯天气 → weather；综合推荐 → 两者都选。"""
