"""规划步骤常量（无 graph builder 依赖，避免循环导入）"""

PLANNING_STEPS = [
    "collect_requirements",
    "plan_destination",
    "plan_transport",
    "plan_stay_and_food",
    "plan_activities",
    "build_itinerary",
    "approval_node",
    "final_response",
]

STEP_LABELS = {
    "collect_requirements": "需求收集",
    "plan_destination": "目的地推荐",
    "plan_transport": "交通规划",
    "plan_stay_and_food": "住宿与餐饮",
    "plan_activities": "活动规划",
    "build_itinerary": "行程与预算",
    "approval_node": "行程确认",
    "final_response": "订单生成",
}

# 简单对话 / 需求收集用 fast 模型（mimo-v2.5）；规划与行程生成用 pro（mimo-v2.5-pro）
FAST_LLM_STEPS = frozenset({"collect_requirements"})

# 兼容参考 Handoffs 8 步命名
STEP_ALIASES = {
    "requirement_collection": "collect_requirements",
    "destination_recommendation": "plan_destination",
    "transport_planning": "plan_transport",
    "accommodation_planning": "plan_stay_and_food",
    "food_planning": "plan_stay_and_food",
    "activity_planning": "plan_activities",
    "itinerary_generation": "build_itinerary",
    "budget_summarization": "build_itinerary",
    "order_generation": "final_response",
}


def normalize_step(step: str) -> str:
    return STEP_ALIASES.get(step, step)
