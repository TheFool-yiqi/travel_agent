"""行程整合与预算节点（LLM 生成 + 结构化输出）"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from loguru import logger

from app.ai.llm import get_chat_model
from app.graph.state import TravelState
from app.graph.step_context import (
    build_step_instruction,
    invoke_step_llm,
    prepare_step_context,
)
from app.schemas.travel import BudgetBreakdown, DayPlan, ItineraryBuildResult
from app.settings import settings

REQUIRED_FIELDS = (
    "user_requirement",
    "selected_destination",
    "selected_transport",
    "selected_accommodation_types",
    "selected_food_types",
    "selected_activity_types",
)


def _party_size(requirement: dict) -> int:
    adults = int(requirement.get("adult_count") or 1)
    children = int(requirement.get("children_count") or 0)
    return max(adults + children, 1)


def _trip_budget_cap(requirement: dict, budget_max: float) -> float:
    """需求收集阶段 budget_max 为每人上限，行程预算为全员总计。"""
    return float(budget_max) * _party_size(requirement)


def budget_warning(state: TravelState, budget: dict) -> str | None:
    """预算超支警告（内联 critic，不单独图节点）。"""
    requirement = state.get("user_requirement") or {}
    budget_max = requirement.get("budget_max") or state.get("budget_max")
    if budget_max is None:
        return None
    total = float(budget.get("total") or 0)
    per_person = float(budget_max)
    trip_cap = _trip_budget_cap(requirement, per_person)
    if total > trip_cap:
        party = _party_size(requirement)
        return (
            f"⚠️ 预算警告：估算全员总计 {total:.0f} 元超出您设定的人均 {per_person:.0f} 元"
            f"（{party} 人合计上限 {trip_cap:.0f} 元），"
            "建议调整住宿标准或减少付费景点。"
        )
    return None

_BUILD_INSTRUCTION = (
    "请基于已收集信息与【工具查询结果】生成完整每日行程与预算估算。"
    "景点/开放时间/价格仅可引用工具结果；无依据处标注「建议预约/现场确认」。"
    "禁止编造具体门票价格、航班/车次号。"
    "每天分上午/下午/晚上，留机动时间，并给出 1 个 Plan B。"
    "预算拆分为交通/住宿/餐饮/门票/杂费，无精确数据时给区间并标注「估算」。"
)

_STRUCTURED_SYSTEM = """你是行程结构化输出器。根据助手生成的行程与预算文本，提取为 JSON 结构。
days 数组长度必须等于用户出行天数；budget 各项为全员总计估算（元）。
不得添加文本中未出现的具体价格或景点细节。"""

_ESTIMATE_DISCLAIMER = "（行程与预算为参考估算，景点开放时间与价格请以官方/预订渠道为准。）"


def day_plan_to_dict(day: DayPlan) -> dict:
    return {
        "day_number": day.day_number,
        "theme": day.theme,
        "activities": [day.morning, day.afternoon, day.evening],
        "meals": day.meals,
        "accommodation": day.accommodation,
        "plan_b": day.plan_b,
    }


def format_itinerary_message(result: ItineraryBuildResult) -> str:
    lines = [result.summary, ""]
    for day in result.days:
        lines.append(f"**Day {day.day_number}** {day.theme}")
        lines.append(f"  上午：{day.morning}")
        lines.append(f"  下午：{day.afternoon}")
        lines.append(f"  晚上：{day.evening}")
        if day.plan_b:
            lines.append(f"  Plan B：{day.plan_b}")
        lines.append("")
    b = result.budget
    lines.append(
        f"预算估算（全员）：{b.total:.0f} 元 "
        f"（交通 {b.transport:.0f} | 住宿 {b.accommodation:.0f} | "
        f"餐饮 {b.food:.0f} | 门票 {b.attractions:.0f} | 其他 {b.misc:.0f}）"
    )
    return "\n".join(lines)


async def structured_itinerary_from_text(text: str, travel_days: int) -> ItineraryBuildResult | None:
    if not settings.mimo_api_key:
        return None
    try:
        structured_llm = get_chat_model().bind(temperature=0).with_structured_output(
            ItineraryBuildResult,
        )
        result: ItineraryBuildResult = await structured_llm.ainvoke(
            [
                SystemMessage(content=_STRUCTURED_SYSTEM),
                HumanMessage(
                    content=f"出行 {travel_days} 天。请将以下行程文本结构化为 JSON：\n\n{text}",
                ),
            ],
        )
        if result.budget.total <= 0:
            b = result.budget
            result.budget = BudgetBreakdown(
                transport=b.transport,
                accommodation=b.accommodation,
                food=b.food,
                attractions=b.attractions,
                misc=b.misc,
                total=b.transport + b.accommodation + b.food + b.attractions + b.misc,
            )
        return result
    except Exception as exc:
        logger.warning("行程结构化抽取失败: {}", exc)
        return None


def _fallback_itinerary(state: TravelState) -> tuple[list[dict], dict, str]:
    requirement = state["user_requirement"]
    travel_days = int(requirement["travel_days"])
    total_people = int(requirement["adult_count"]) + int(requirement["children_count"])
    destination = state.get("selected_destination", "目的地")

    itinerary = [
        {
            "day_number": day,
            "theme": f"{destination} 第{day}天",
            "activities": [
                f"上午：{destination} 核心景点游览",
                f"下午：当地特色体验",
                f"晚上：休闲或美食",
            ],
            "meals": ["早餐", "午餐", "晚餐"],
            "accommodation": "推荐区域酒店",
        }
        for day in range(1, travel_days + 1)
    ]

    transport_cost = 500 * total_people
    accommodation_cost = 300 * travel_days * total_people
    food_cost = 150 * travel_days * total_people
    attractions_cost = 200 * travel_days * total_people
    misc_cost = 100 * travel_days * total_people
    total_cost = (
        transport_cost + accommodation_cost + food_cost + attractions_cost + misc_cost
    )

    budget = BudgetBreakdown(
        transport=transport_cost,
        accommodation=accommodation_cost,
        food=food_cost,
        attractions=attractions_cost,
        misc=misc_cost,
        total=total_cost,
    ).model_dump()

    message = (
        f"已生成 {travel_days} 天 {destination} 行程（估算模式）。\n"
        f"预算总计：{total_cost:.0f} 元\n"
        f"{_ESTIMATE_DISCLAIMER}"
    )
    return itinerary, budget, message


async def build_itinerary(state: TravelState) -> dict:
    missing = [field for field in REQUIRED_FIELDS if not state.get(field)]
    if missing:
        return {
            "current_step": "build_itinerary",
            "messages": [
                AIMessage(content=f"信息不完整，缺少：{', '.join(missing)}")
            ],
        }

    requirement = state["user_requirement"]
    travel_days = int(requirement["travel_days"])
    ctx = prepare_step_context("build_itinerary", state)

    itinerary: list[dict]
    budget: dict
    message: str

    revision_note = state.get("consumed_revision_note")
    build_instruction = _BUILD_INSTRUCTION
    if revision_note:
        build_instruction = (
            f"{_BUILD_INSTRUCTION}\n\n"
            f"【修订要求】用户希望调整：{revision_note}。"
            "请在保留合理部分的前提下按此修改，并说明主要变更点。"
        )

    if settings.mimo_api_key and ctx.ready:
        try:
            raw_text = await invoke_step_llm(
                "build_itinerary",
                state,
                instruction=build_step_instruction(
                    "build_itinerary", state, build_instruction
                ),
                ctx=ctx,
            )
            structured = await structured_itinerary_from_text(raw_text, travel_days)
            if structured and structured.days and len(structured.days) == travel_days:
                itinerary = [day_plan_to_dict(d) for d in structured.days]
                budget = structured.budget.model_dump()
                message = format_itinerary_message(structured)
            elif structured and structured.days:
                logger.warning(
                    "行程天数不匹配 expected={} got={}",
                    travel_days,
                    len(structured.days),
                )
                itinerary, budget, message = _fallback_itinerary(state)
                message = f"{raw_text}\n\n---\n{message}"
            else:
                itinerary, budget, message = _fallback_itinerary(state)
                message = f"{raw_text}\n\n---\n{message}"
        except Exception as exc:
            logger.exception("行程生成 LLM 调用失败")
            itinerary, budget, message = _fallback_itinerary(state)
            message = f"（AI 服务异常：{exc}）\n{message}"
    else:
        itinerary, budget, message = _fallback_itinerary(state)

    warning = budget_warning(state, budget)
    report = state.get("report")
    if _ESTIMATE_DISCLAIMER not in message:
        message = f"{message}\n\n{_ESTIMATE_DISCLAIMER}"
    if warning:
        message = f"{message}\n\n{warning}"
        report = warning if not report else f"{report}\n{warning}"

    if revision_note:
        message = f"已按您的修订意见重新生成行程。\n\n{message}"

    return {
        "current_step": "approval_node",
        "approval_status": "pending",
        "itinerary": itinerary,
        "budget": budget,
        "report": report,
        "messages": [AIMessage(content=message)],
    }
