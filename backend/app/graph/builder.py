"""旅行规划 Graph 构建"""

from langgraph.graph import END, START, StateGraph

from app.dependencies import get_checkpointer
from app.graph.nodes.build_itinerary import build_itinerary
from app.graph.nodes.collect_requirements import collect_requirements
from app.graph.nodes.final_response import final_response
from app.graph.nodes.inject_memory import inject_user_memory
from app.graph.nodes.plan_destination import plan_destination
from app.graph.nodes.approval_node import approval_node
from app.graph.nodes.plan_activities import plan_activities
from app.graph.nodes.plan_stay_and_food import plan_stay_and_food
from app.graph.nodes.plan_transport import plan_transport
from app.graph.nodes.revise_itinerary import revise_itinerary
from app.graph.routers.approval_router import route_after_approval, route_after_itinerary
from app.graph.routers.step_router import (
    route_after_activities,
    route_after_collect,
    route_after_destination,
    route_after_memory,
    route_after_stay_and_food,
    route_after_transport,
)
from app.graph.state import TravelState


async def build_travel_graph():
    """编译带 Checkpointer 的旅行规划 Graph（路线1：节点 + 路由）"""
    # step_config / MCP 由 app.lifespan 在 FastAPI 启动时预加载；脚本直调时在此补加载
    from app.graph.step_config import _mcp_tools_loaded, apply_step_config_from_mcp

    if not _mcp_tools_loaded:
        await apply_step_config_from_mcp()

    builder = StateGraph(TravelState)

    builder.add_node("inject_user_memory", inject_user_memory)
    builder.add_node("collect_requirements", collect_requirements)
    builder.add_node("plan_destination", plan_destination)
    builder.add_node("plan_transport", plan_transport)
    builder.add_node("plan_stay_and_food", plan_stay_and_food)
    builder.add_node("plan_activities", plan_activities)
    builder.add_node("build_itinerary", build_itinerary)
    builder.add_node("approval_node", approval_node)
    builder.add_node("revise_itinerary", revise_itinerary)
    builder.add_node("final_response", final_response)

    builder.add_edge(START, "inject_user_memory")
    builder.add_conditional_edges(
        "inject_user_memory",
        route_after_memory,
        {
            "collect_requirements": "collect_requirements",
            "plan_destination": "plan_destination",
            "plan_transport": "plan_transport",
            "plan_stay_and_food": "plan_stay_and_food",
            "plan_activities": "plan_activities",
            "build_itinerary": "build_itinerary",
            "approval_node": "approval_node",
            "final_response": "final_response",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "collect_requirements",
        route_after_collect,
        {"plan_destination": "plan_destination", END: END},
    )
    builder.add_conditional_edges(
        "plan_destination",
        route_after_destination,
        {"plan_transport": "plan_transport", END: END},
    )
    builder.add_conditional_edges(
        "plan_transport",
        route_after_transport,
        {"plan_stay_and_food": "plan_stay_and_food", END: END},
    )
    builder.add_conditional_edges(
        "plan_stay_and_food",
        route_after_stay_and_food,
        {"plan_activities": "plan_activities", END: END},
    )
    builder.add_conditional_edges(
        "plan_activities",
        route_after_activities,
        {"build_itinerary": "build_itinerary", END: END},
    )
    builder.add_conditional_edges(
        "build_itinerary",
        route_after_itinerary,
        {"approval_node": "approval_node", END: END},
    )
    builder.add_conditional_edges(
        "approval_node",
        route_after_approval,
        {
            "final_response": "final_response",
            "revise_itinerary": "revise_itinerary",
            END: END,
        },
    )
    builder.add_edge("revise_itinerary", "build_itinerary")
    builder.add_edge("final_response", END)

    checkpointer = await get_checkpointer()
    return builder.compile(checkpointer=checkpointer)
