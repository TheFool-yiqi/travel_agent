"""规划流程回退与进度查询（路线1：纯函数，非 @tool）"""

from typing import Any

from langchain_core.messages import AIMessage
from loguru import logger

from app.graph.state import TravelState

from app.graph.steps import PLANNING_STEPS, STEP_LABELS, normalize_step

STEP_STATE_FIELDS: dict[str, list[str]] = {
    "collect_requirements": [
        "user_requirement",
        "requirements_complete",
        "departure_city",
        "departure_date",
        "travel_days",
        "budget_min",
        "budget_max",
        "travel_styles",
        "special_needs",
        "destination",
        "start_date",
        "end_date",
    ],
    "plan_destination": ["selected_destination", "destination"],
    "plan_transport": [
        "selected_transport",
        "origin_city",
        "destination_city",
        "passenger_count",
        "flight_options",
        "train_options",
        "driving_routes",
        "selected_flight",
        "selected_train",
        "selected_route",
    ],
    "plan_stay_and_food": ["selected_accommodation_types", "selected_food_types"],
    "plan_activities": ["selected_activity_types"],
    "build_itinerary": ["itinerary", "budget", "approval_status", "report"],
    "approval_node": ["approval_status"],
    "final_response": ["order_id", "report"],
}

LIST_FIELDS = {
    "travel_styles",
    "selected_accommodation_types",
    "selected_food_types",
    "selected_activity_types",
    "itinerary",
    "flight_options",
    "train_options",
    "driving_routes",
}
BOOL_FIELDS = {"requirements_complete"}
DICT_FIELDS = {"user_requirement", "budget"}


def _clear_value(field: str) -> Any:
    if field in LIST_FIELDS:
        return []
    if field in BOOL_FIELDS:
        return False
    if field in DICT_FIELDS:
        return {}
    return None


def apply_rollback(
    state: TravelState,
    target_step: str,
    reason: str,
    clear_subsequent: bool = True,
) -> dict:
    """
    回退到指定步骤，返回 partial state update（可与 aupdate_state / ainvoke 合并使用）。
    """
    target_step = normalize_step(target_step)

    if target_step not in PLANNING_STEPS:
        return {
            "messages": [AIMessage(content=f"无效的目标步骤：{target_step}")],
        }

    if target_step == "final_response":
        return {
            "messages": [
                AIMessage(content="订单生成是最终步骤，无法回退到此。请回退到更早的步骤。")
            ],
        }

    current = state.get("current_step", "collect_requirements")
    logger.info("规划回退: {} -> {}，原因: {}", current, target_step, reason)

    update: dict[str, Any] = {"current_step": target_step}
    cleared: list[str] = []

    if clear_subsequent:
        start_index = PLANNING_STEPS.index(target_step)
        for step in PLANNING_STEPS[start_index:]:
            for field in STEP_STATE_FIELDS.get(step, []):
                update[field] = _clear_value(field)
                cleared.append(field)

    label = STEP_LABELS.get(target_step, target_step)
    lines = [f"已回退到【{label}】阶段", f"原因：{reason}"]
    if clear_subsequent and cleared:
        lines.append("已清除目标步骤及后续步骤的数据")

    update["messages"] = [AIMessage(content="\n".join(lines))]
    return update


def rollback_to_requirement(state: TravelState, reason: str = "用户需要修改旅行需求") -> dict:
    return apply_rollback(state, "collect_requirements", reason)


def rollback_to_destination(state: TravelState, reason: str = "用户需要重新选择目的地") -> dict:
    return apply_rollback(state, "plan_destination", reason)


def rollback_to_transport(state: TravelState, reason: str = "用户需要更换交通方式") -> dict:
    return apply_rollback(state, "plan_transport", reason)


def rollback_to_stay_and_food(state: TravelState, reason: str = "用户需要调整住宿或餐饮") -> dict:
    return apply_rollback(state, "plan_stay_and_food", reason)


def rollback_to_itinerary(state: TravelState, reason: str = "用户需要调整行程或预算") -> dict:
    return apply_rollback(state, "build_itinerary", reason)


def rollback_to_activities(state: TravelState, reason: str = "用户需要调整活动偏好") -> dict:
    return apply_rollback(state, "plan_activities", reason)


def format_planning_progress(state: TravelState) -> str:
    """查询当前规划进度（对应 check_current_progress）"""
    current = normalize_step(state.get("current_step") or "collect_requirements")

    if current == "done":
        lines = ["当前规划进度", ""]
        for index, step in enumerate(PLANNING_STEPS):
            lines.append(f"  [{index + 1}] {STEP_LABELS[step]} - 已完成")
    else:
        try:
            current_index = PLANNING_STEPS.index(current)
        except ValueError:
            current_index = 0
            current = "collect_requirements"

        lines = ["当前规划进度", ""]
        for index, step in enumerate(PLANNING_STEPS):
            label = STEP_LABELS[step]
            if index < current_index:
                status = "已完成"
            elif step == current:
                status = "当前步骤"
            else:
                status = "待完成"
            lines.append(f"  [{index + 1}] {label} - {status}")

    lines.extend(["", "已收集信息:"])
    requirement = state.get("user_requirement") or {}
    if requirement:
        lines.append(f"  - 出发日期: {requirement.get('departure_date', '未设置')}")
        lines.append(f"  - 出行天数: {requirement.get('travel_days', '未设置')} 天")
        lines.append(
            f"  - 人数: {requirement.get('adult_count', 0)} 成人 + "
            f"{requirement.get('children_count', 0)} 儿童"
        )
    if state.get("selected_destination"):
        lines.append(f"  - 目的地: {state['selected_destination']}")
    if state.get("selected_transport"):
        transport_labels = {"flight": "航班", "train": "高铁", "driving": "自驾"}
        lines.append(
            f"  - 交通: {transport_labels.get(state['selected_transport'], state['selected_transport'])}"
        )
    if state.get("selected_accommodation_types"):
        lines.append(f"  - 住宿: {', '.join(state['selected_accommodation_types'])}")
    if state.get("selected_food_types"):
        lines.append(f"  - 餐饮: {', '.join(state['selected_food_types'])}")
    if state.get("selected_activity_types"):
        lines.append(f"  - 活动: {', '.join(state['selected_activity_types'])}")

    return "\n".join(lines)
