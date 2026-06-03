"""Graph 条件路由"""

from langgraph.graph import END

from app.graph.rollback import PLANNING_STEPS, normalize_step
from app.graph.state import TravelState


def route_after_memory(state: TravelState) -> str:
    """注入长期记忆后，按 current_step 恢复到对应节点"""
    step = normalize_step(state.get("current_step") or "collect_requirements")

    if step == "done":
        return END
    if step in PLANNING_STEPS:
        return step
    return "collect_requirements"


def route_after_collect(state: TravelState) -> str:
    if (
        state.get("requirements_complete")
        and state.get("user_requirement")
        and state.get("user_confirmed")
    ):
        return "plan_destination"
    return END


def route_after_destination(state: TravelState) -> str:
    """目的地节点结束后暂停，等待用户选择交通方式。"""
    return END


def route_after_transport(state: TravelState) -> str:
    """交通节点结束后暂停，等待用户选择食宿。"""
    return END


def route_after_stay_and_food(state: TravelState) -> str:
    """食宿节点结束后暂停，等待用户选择活动。"""
    return END


def route_after_activities(state: TravelState) -> str:
    """活动确认后自动进入行程生成（与 approval_router 逻辑一致）。"""
    if (
        state.get("current_step") == "build_itinerary"
        and state.get("selected_activity_types")
    ):
        return "build_itinerary"
    return END


def route_after_final(state: TravelState) -> str:
    return END
