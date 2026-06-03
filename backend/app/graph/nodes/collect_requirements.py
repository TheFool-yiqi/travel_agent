"""收集用户需求节点（NL 解析 + 对话式追问）"""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from loguru import logger

from app.ai.llm import get_chat_model
from app.graph.greeting import build_greeting_reply, is_greeting_only_messages
from app.graph.state import TravelState
from app.graph.step_context import (
    build_step_instruction,
    invoke_step_llm,
    prepare_step_context,
)
from app.graph.templates.budget_tiers import (
    apply_budget_tier_to_fields,
    apply_party_from_dialogue,
    is_party_confirmed,
)
from app.graph.templates.collect_followup import render_collect_followup
from app.graph.templates.collect_guidance import needs_guidance_followup, next_guidance_step
from app.graph.semantic.slot_tracker import last_human_text
from app.graph.templates.requirements_summary import (
    format_requirements_summary,
    render_facts_prefix,
)
from app.graph.validators.collect_reply import sanitize_collect_reply, validate_collect_reply
from app.graph.validators.requirements import (
    sanitize_budget,
    sanitize_destination,
    sanitize_travel_styles,
    validate_requirements,
)
from app.schemas.travel import RequirementExtraction, UserRequirement, infer_budget_level
from app.settings import settings
from app.tools.datetime_tools import parse_relative_date, today_beijing_iso
from app.graph.semantic.normalizer import normalize_text
from app.graph.semantic.slot_sanitizer import fields_for_guidance_step
from app.graph.semantic.semantic_metrics import build_turn_metrics
from app.graph.semantic.semantic_pipeline import apply_semantic_frame, build_semantic_frame
from app.services.conversation_bootstrap import has_assistant_messages
from app.tools.holiday_calendar import (
    apply_holiday_date_to_fields,
    detect_holiday_departure_date,
    format_holiday_departure_hint,
    holiday_reference_text,
    suggest_holiday_travel_days,
)

_GO_DESTINATION = re.compile(
    r"(?:从[\u4e00-\u9fff]{1,8}去|想去|去|到)([\u4e00-\u9fff]{2,8}?)(?:玩|旅|游|看看|度)?",
)
_CONFIRM_PATTERN = re.compile(
    r"^(确认|没问题|对的?|可以|就这些|没错|正确|ok|OK)[!.?？\s]*$",
    re.IGNORECASE,
)

_EXTRACTION_SYSTEM_TEMPLATE = """你是旅行需求信息抽取器。从用户与助手的对话中提取结构化字段。
当前日期（北京时间）：{today}

{holiday_reference}

## 预处理（必须先做）
1. 对每条用户消息做语义规范化后再抽取：同音错字（程度→成都、杭洲→杭州）、口语（下礼拜→下周、一家三口→2成人1儿童、学生党→穷游党）
2. 从**规范化后的语义**填槽，不要被错字误导；不确定则留 null
3. 用户说「总共/一共 X 元」为总预算，须结合人数折算到每人；「每人/人均 X 元」直接作为 budget_min/max 参考

规则：
- 用户一句话可能同时包含多项信息（目的地/出发地/时间/天数/人数/预算/交通方式/食宿偏好等），须**并行提取**所有能确定的字段，不要因分步引导而丢弃
- 用户若提到交通偏好（高铁/飞机/自驾）、住宿或饮食要求，写入 special_needs 或合适的 travel_styles
- departure_date 必须是 YYYY-MM-DD
- 用户提到任何节日（元旦/春节/清明/五一/端午/中秋/国庆等）时，必须使用上方节日参考中的 2026 年日期，禁止臆造
- budget_min/budget_max 为每人预算（元）；若用户说总预算，按人数折算
- budget_min/budget_max 仅当用户明确提到预算金额或档位（穷游党/一般党/富有党/学生党/随便玩玩/每人X元等）时填写；勿默认、勿从目的地或天数推断
- 用户说「穷游党/一般党/富有党/学生党/随便玩玩」时映射为对应档位金额，勿自行编造窄区间（如 2000-30）
- 询问预算前须先确认出行人数（成人+儿童）
- travel_styles 取值：relaxation, culture, adventure, food（可多选）
- travel_styles 仅当用户明确提到风格关键词时填写；勿从预算档位（穷游党/一般党/富有党）、目的地或历史偏好推断
- 仅提取对话中明确出现或合理推断的信息；不确定则留 null
- user_confirmed：用户明确表示「确认/没错/可以/就这些」时为 true
"""

_FIELD_LABELS: dict[str, str] = {
    "departure_city": "出发城市",
    "departure_date": "出发日期",
    "travel_days": "出行天数",
    "adult_count": "成人数",
    "children_count": "儿童数",
    "budget_min": "预算下限",
    "budget_max": "预算上限",
    "destination": "目的地",
    "special_needs": "特殊需求",
}

_REQUIRED_KEYS = ("departure_city", "departure_date", "travel_days", "budget_min", "budget_max")

_COLLECT_INSTRUCTION = (
    "请根据对话收集旅行需求。"
    "引导用户时一次只问【仍缺失】中排在最前的一项，不要在同一句里混问城市/时间/预算等多件事。"
    "用户若已在对话中一次说出多项信息，后台会全部记录，你只需自然确认已知信息并追问下一缺失项。"
    "信息尚未齐全时继续追问；齐全后做简要确认摘要。"
)


def _dialogue_text(messages: list[BaseMessage]) -> str:
    lines: list[str] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            continue
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            lines.append(f"用户: {content}")
        elif isinstance(message, AIMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            lines.append(f"助手: {content}")
    return "\n".join(lines) if lines else "（暂无对话）"


def _normalized_dialogue_text(messages: list[BaseMessage]) -> str:
    """供 LLM 抽取的规范化对话（用户句先做口语/错字规范化）。"""
    lines: list[str] = []
    for message in messages:
        if isinstance(message, SystemMessage):
            continue
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            normalized, _ = normalize_text(content.strip())
            if normalized and normalized != content.strip():
                lines.append(f"用户: {content}（规范化: {normalized}）")
            else:
                lines.append(f"用户: {content}")
        elif isinstance(message, AIMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            lines.append(f"助手: {content}")
    return "\n".join(lines) if lines else "（暂无对话）"


def _extraction_system_prompt() -> str:
    return _EXTRACTION_SYSTEM_TEMPLATE.format(
        today=today_beijing_iso(),
        holiday_reference=holiday_reference_text(),
    )


def _human_messages_text(messages: list[BaseMessage]) -> str:
    parts: list[str] = []
    for message in messages:
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            parts.append(content.strip())
    return " ".join(parts)


def _heuristic_extract(text: str) -> RequirementExtraction:
    """规则兜底：节日、天数、显式目的地句式（城市槽位由 semantic 层处理）。"""
    if not text:
        return RequirementExtraction()

    data: dict[str, Any] = {}
    stripped = text.strip()

    from app.graph.semantic.slot_tracker import _extract_rule_slots  # noqa: PLC0415

    data.update(_extract_rule_slots(stripped, "departure_date"))

    dest_match = _GO_DESTINATION.search(stripped)
    if dest_match:
        data["destination"] = dest_match.group(1)

    return RequirementExtraction(**data) if data else RequirementExtraction()


def _heuristic_extract_from_messages(messages: list[BaseMessage]) -> RequirementExtraction:
    """扫描全部用户消息（节日/城市可能在较早轮次）。"""
    merged: dict[str, Any] = {}
    for message in messages:
        if not isinstance(message, HumanMessage):
            continue
        content = message.content if isinstance(message.content, str) else str(message.content)
        partial = _heuristic_extract(content).model_dump()
        for key, value in partial.items():
            if value is not None and value != "" and value != []:
                merged[key] = value

    combined = _human_messages_text(messages)
    holiday_date = detect_holiday_departure_date(combined)
    if holiday_date:
        merged["departure_date"] = holiday_date

    relative_date = parse_relative_date(combined)
    if relative_date:
        merged.setdefault("departure_date", relative_date)

    return RequirementExtraction(**merged) if merged else RequirementExtraction()


def _merge_extractions(
    llm: RequirementExtraction,
    heuristic: RequirementExtraction,
) -> RequirementExtraction:
    """LLM 结果为基础，规则抽取覆盖（节日/城市等以规则为准）。"""
    merged = llm.model_dump()
    for key, value in heuristic.model_dump().items():
        if value is not None and value != "" and value != []:
            merged[key] = value
    return RequirementExtraction(**merged)


def _format_known_requirements(fields: dict[str, Any]) -> str:
    lines: list[str] = []
    for key, label in _FIELD_LABELS.items():
        value = fields.get(key)
        if value is not None and value != "":
            lines.append(f"- {label}：{value}")
    return "\n".join(lines) if lines else "- 无"


def _missing_requirement_labels(fields: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for key in _REQUIRED_KEYS:
        value = fields.get(key)
        if value is None or value == "":
            missing.append(_FIELD_LABELS[key])
    return missing


def _build_collect_instruction(
    merged_fields: dict[str, Any],
    state: TravelState,
    *,
    include_tool_context: bool,
    validation_errors: list[str] | None = None,
    awaiting_confirmation: bool = False,
    dialogue_text: str = "",
) -> str:
    known = _format_known_requirements(merged_fields)
    missing = _missing_requirement_labels(merged_fields)
    missing_text = "、".join(missing) if missing else "无（可做简要摘要确认）"
    facts_block = render_facts_prefix(merged_fields, dialogue_text=dialogue_text)
    contextual = (
        f"【已收集信息】\n{known}\n\n"
        f"【仍缺失】{missing_text}\n\n"
        f"回复开头必须包含以下事实块（可在此基础上续写，勿改日期/城市）：\n{facts_block}\n\n"
        "请勿重复询问【已收集信息】中的内容；只针对【仍缺失】项提问。"
        "回复中的日期必须与【已收集信息】里的出发日期一致；若用户提到节日，只能使用工具/节日参考表中的日期。"
        "举例天数时用「X天（Y晚）」且 Y 通常为 X-1；短途指 2-4 天，禁止出现「短途21晚」等矛盾说法。"
        "勿主动提「年假」除非用户先提到，或当前为 12 月–2 月春节规划季。"
        "举例日期必须来自【工具查询结果】中的相对日期，勿臆造。"
        "若【仍缺失】含出发日期，举例须包含最近法定节假日名称与日期区间。"
    )
    if validation_errors:
        contextual += "\n\n【待纠正】\n" + "\n".join(f"- {e}" for e in validation_errors)
    if awaiting_confirmation:
        contextual += (
            "\n\n信息已齐全，请基于【已收集信息】做简要摘要，"
            "并询问用户「我理解得对吗？还有没有必须要做或坚决不想要的点？」"
            "不要进入下一步，等待用户明确确认。"
        )
    base = f"{contextual}\n\n{_COLLECT_INSTRUCTION}"
    if include_tool_context:
        return build_step_instruction("collect_requirements", state, base)
    return base


def merge_extraction(state: TravelState, extracted: RequirementExtraction) -> dict[str, Any]:
    """将抽取结果与已有 state 合并（新值优先）。"""
    merged: dict[str, Any] = {}

    def pick(key: str, value: Any) -> None:
        if value is not None and value != "" and value != []:
            merged[key] = value

    guidance_step = next_guidance_step(fields_for_guidance_step(state))

    if guidance_step == "destination":
        pick("departure_city", state.get("departure_city"))
        pick("destination", state.get("destination"))
        if "destination" not in merged:
            pick("destination", extracted.destination)
    else:
        pick("departure_city", extracted.departure_city or state.get("departure_city"))
        if state.get("destination"):
            pick("destination", state.get("destination"))
        else:
            pick(
                "destination",
                extracted.destination or state.get("selected_destination"),
            )
    pick(
        "departure_date",
        extracted.departure_date or state.get("departure_date") or state.get("start_date"),
    )
    pick("travel_days", extracted.travel_days or state.get("travel_days"))

    if extracted.adult_count is not None:
        merged["adult_count"] = extracted.adult_count
    elif state.get("adult_count") is not None:
        merged["adult_count"] = state.get("adult_count")

    if extracted.children_count is not None:
        merged["children_count"] = extracted.children_count
    elif state.get("children_count") is not None:
        merged["children_count"] = state.get("children_count")
    elif merged.get("adult_count") is not None and "children_count" not in merged:
        merged["children_count"] = 0

    if state.get("party_confirmed"):
        merged["party_confirmed"] = True
    if extracted.adult_count is not None:
        merged["party_confirmed"] = True

    pick("budget_min", extracted.budget_min if extracted.budget_min is not None else state.get("budget_min"))
    pick("budget_max", extracted.budget_max if extracted.budget_max is not None else state.get("budget_max"))
    if extracted.travel_styles:
        merged["travel_styles"] = list(extracted.travel_styles)
    elif state.get("travel_styles"):
        merged["travel_styles"] = list(state.get("travel_styles") or [])
    pick("special_needs", extracted.special_needs or state.get("special_needs"))

    return merged


def is_requirement_complete(fields: dict[str, Any]) -> bool:
    """P0：必填字段齐全且日期格式有效即视为可进入下一步。"""
    required_keys = ("departure_city", "departure_date", "travel_days", "budget_min", "budget_max")
    for key in required_keys:
        if fields.get(key) is None or fields.get(key) == "":
            return False
    if not is_party_confirmed(fields):
        return False
    try:
        datetime.strptime(str(fields["departure_date"]), "%Y-%m-%d")
    except ValueError:
        return False
    try:
        days = int(fields["travel_days"])
        if days < 1:
            return False
    except (TypeError, ValueError):
        return False
    return float(fields["budget_min"]) <= float(fields["budget_max"])


def can_advance_to_planning(fields: dict[str, Any], *, user_confirmed: bool, dialogue_text: str = "") -> bool:
    """字段齐全 + 校验通过 + 用户已确认。"""
    if not user_confirmed:
        return False
    if not is_requirement_complete(fields):
        return False
    return len(validate_requirements(fields, dialogue_text=dialogue_text)) == 0


def _detect_user_confirmed(messages: list[BaseMessage], extracted: RequirementExtraction) -> bool:
    if extracted.user_confirmed:
        return True
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            if _CONFIRM_PATTERN.match(content.strip()):
                return True
    return False


def _confirmation_reply(fields: dict[str, Any], *, dialogue_text: str = "") -> str:
    summary = format_requirements_summary(fields, dialogue_text=dialogue_text)
    return (
        f"我整理一下您的需求：\n{summary}\n\n"
        "我理解得对吗？还有没有「必须要做」或「坚决不想要」的点？"
        "确认无误请回复「确认」或「没问题」。"
    )


def _ensure_facts_prefix(reply: str, fields: dict[str, Any], *, dialogue_text: str = "") -> str:
    if not fields.get("departure_city") and not fields.get("departure_date"):
        return reply
    prefix = render_facts_prefix(fields, dialogue_text=dialogue_text)
    if "【当前已确认】" in reply:
        return reply
    return f"{prefix}\n\n{reply}"


def build_user_requirement(fields: dict[str, Any]) -> UserRequirement:
    return UserRequirement(
        departure_city=str(fields["departure_city"]),
        destination=fields.get("destination"),
        departure_date=str(fields["departure_date"]),
        travel_days=int(fields["travel_days"]),
        adult_count=int(fields.get("adult_count") or 1),
        children_count=int(fields.get("children_count") or 0),
        budget_min=float(fields["budget_min"]),
        budget_max=float(fields["budget_max"]),
        budget_level=infer_budget_level(float(fields["budget_min"]), float(fields["budget_max"])),
        travel_styles=list(fields.get("travel_styles") or []),
        special_needs=fields.get("special_needs"),
    )


def _is_greeting_only(messages: list[BaseMessage]) -> bool:
    """纯寒暄跳过结构化抽取与 LLM，使用即时模板回复。"""
    return is_greeting_only_messages(messages)


async def _instant_greeting_reply() -> str:
    return build_greeting_reply()


def _finalize_collect_reply(
    reply: str,
    merged_fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> str:
    """清洗 LLM 回复；不通过校验则改用模板追问。"""
    reply = _ensure_facts_prefix(reply, merged_fields, dialogue_text=dialogue_text)
    reply = sanitize_collect_reply(reply, dialogue_text=dialogue_text)
    missing_departure_date = not merged_fields.get("departure_date")
    if validate_collect_reply(
        reply,
        dialogue_text=dialogue_text,
        missing_departure_date=missing_departure_date,
    ):
        logger.warning("需求收集回复未通过校验，改用模板追问")
        return render_collect_followup(merged_fields, dialogue_text=dialogue_text)
    return reply


def _needs_template_followup(merged_fields: dict[str, Any], *, awaiting_confirmation: bool) -> bool:
    """尚未齐全时，用模板逐步引导（目的地 → 出发地 → 时间 → …）。"""
    return needs_guidance_followup(merged_fields, awaiting_confirmation=awaiting_confirmation)


async def _generate_collect_reply(
    state: TravelState,
    merged_fields: dict[str, Any],
    *,
    include_tool_context: bool = True,
    validation_errors: list[str] | None = None,
    awaiting_confirmation: bool = False,
    dialogue_text: str = "",
) -> str:
    if awaiting_confirmation and is_requirement_complete(merged_fields) and not validation_errors:
        return _confirmation_reply(merged_fields, dialogue_text=dialogue_text)

    if _needs_template_followup(merged_fields, awaiting_confirmation=awaiting_confirmation):
        return render_collect_followup(merged_fields, dialogue_text=dialogue_text)

    ctx = prepare_step_context("collect_requirements", state)
    if settings.mimo_api_key and ctx.ready:
        instruction = _build_collect_instruction(
            merged_fields,
            state,
            include_tool_context=include_tool_context,
            validation_errors=validation_errors,
            awaiting_confirmation=awaiting_confirmation,
            dialogue_text=dialogue_text,
        )
        try:
            reply = await invoke_step_llm(
                "collect_requirements",
                state,
                instruction=instruction,
                ctx=ctx,
            )
            return _finalize_collect_reply(
                reply,
                merged_fields,
                dialogue_text=dialogue_text,
            )
        except Exception as exc:
            logger.exception("需求收集 LLM 调用失败")
            return _fallback_reply(merged_fields, exc, validation_errors=validation_errors)
    return _fallback_reply(merged_fields, None, validation_errors=validation_errors)


async def extract_requirements_from_dialogue(
    messages: list[BaseMessage],
) -> RequirementExtraction:
    if not settings.mimo_api_key:
        return RequirementExtraction()

    dialogue = _normalized_dialogue_text(messages)
    heuristic = _heuristic_extract_from_messages(messages)
    try:
        structured_llm = get_chat_model(fast=True).bind(temperature=0).with_structured_output(
            RequirementExtraction,
        )
        result: RequirementExtraction = await structured_llm.ainvoke(
            [
                SystemMessage(content=_extraction_system_prompt()),
                HumanMessage(content=f"对话记录（含用户句规范化提示）：\n{dialogue}"),
            ],
        )
        return _merge_extractions(result, heuristic)
    except Exception as exc:
        logger.warning("需求抽取 LLM 失败: {}", exc)
        return heuristic


_TRAVEL_DAYS_INTERPRET_SYSTEM = """你是旅行天数理解助手。根据用户最新一句及已知出发信息，推断出行/游玩天数（整数）。

规则：
- 用户说「整个假期/整个小长假/假期都玩/放几天玩几天」等，结合出发日期所在法定假期长度返回天数
- 出发日期若在法定假期内，以该假期总天数为准
- 用户给出明确数字（如「3天」）时直接采用
- 无法确定时 travel_days 留 null
"""


async def _interpret_travel_days_llm(
    messages: list[BaseMessage],
    fields: dict[str, Any],
    dialogue_text: str,
) -> int | None:
    """天数槽位规则未命中时，用 LLM 结合节日/出发日上下文再理解一次。"""
    if not settings.mimo_api_key:
        return None

    last_message = last_human_text(messages)
    if not last_message.strip():
        return None

    holiday_hint = ""
    suggestion = suggest_holiday_travel_days(fields, dialogue_text=dialogue_text)
    if suggestion:
        days, label = suggestion
        holiday_hint = f"{label}法定假期一般为 {days} 天"

    prompt = (
        f"出发日期：{fields.get('departure_date') or '未知'}\n"
        f"节日提示：{holiday_hint or '无'}\n"
        f"用户最新一句：{last_message}\n"
        f"完整对话摘要：{dialogue_text[-500:]}"
    )
    try:
        structured_llm = get_chat_model(fast=True).bind(temperature=0).with_structured_output(
            RequirementExtraction,
        )
        result: RequirementExtraction = await structured_llm.ainvoke(
            [
                SystemMessage(content=_TRAVEL_DAYS_INTERPRET_SYSTEM),
                HumanMessage(content=prompt),
            ],
        )
        if result.travel_days is not None and result.travel_days >= 1:
            return int(result.travel_days)
    except Exception as exc:
        logger.warning("天数理解 LLM 失败: {}", exc)
    return None


async def collect_requirements(state: TravelState) -> dict:
    if state.get("user_requirement") and state.get("requirements_complete"):
        return {
            "current_step": "plan_destination",
            "messages": [AIMessage(content="需求已记录，进入目的地规划。")],
        }

    messages = state.get("messages") or []
    extracted = RequirementExtraction()

    if _is_greeting_only(messages):
        session_id = state.get("session_id")
        already_greeted = False
        if session_id:
            try:
                already_greeted = await has_assistant_messages(uuid.UUID(str(session_id)))
            except ValueError:
                already_greeted = False
        if already_greeted:
            reply = "你好！咱们继续吧——你想去哪里玩呢？"
        else:
            reply = await _instant_greeting_reply()
        merged_fields = merge_extraction(state, extracted)
        validation_errors: list[str] = []
        user_confirmed = False
        pending_clarification_update = None
        semantic_trace = None
    else:
        extracted = await extract_requirements_from_dialogue(messages)
        merged_fields = merge_extraction(state, extracted)
        dialogue = _dialogue_text(messages)
        merged_fields = apply_holiday_date_to_fields(merged_fields, dialogue)
        merged_fields = apply_party_from_dialogue(merged_fields, dialogue)
        merged_fields = apply_budget_tier_to_fields(merged_fields, dialogue)
        validation_errors = validate_requirements(merged_fields, dialogue_text=dialogue)
        user_confirmed = bool(state.get("user_confirmed")) or _detect_user_confirmed(messages, extracted)

        semantic_reply: str | None = None
        pending_clarification_update: dict[str, Any] | None = None
        semantic_trace: dict[str, Any] | None = None

        frame = build_semantic_frame(messages, merged_fields, state)
        had_pending_before = bool(state.get("pending_clarification"))
        merged_fields, semantic_reply, pending_clarification_update = apply_semantic_frame(
            merged_fields,
            state,
            frame,
        )
        merged_fields = sanitize_travel_styles(merged_fields, dialogue_text=dialogue)
        merged_fields = sanitize_budget(merged_fields, dialogue_text=dialogue)
        merged_fields = sanitize_destination(
            merged_fields,
            dialogue_text=dialogue,
            pending_clarification=pending_clarification_update or state.get("pending_clarification"),
            guidance_step=next_guidance_step(fields_for_guidance_step(state)),
        )

        if (
            next_guidance_step(merged_fields) == "travel_days"
            and not merged_fields.get("travel_days")
            and last_human_text(messages).strip()
            and not semantic_reply
        ):
            llm_days = await _interpret_travel_days_llm(messages, merged_fields, dialogue)
            if llm_days:
                merged_fields["travel_days"] = llm_days
            elif pending_clarification_update is None and not state.get("pending_clarification"):
                from app.graph.templates.collect_followup import render_travel_days_clarification

                clarifier = render_travel_days_clarification(merged_fields, dialogue_text=dialogue)
                if clarifier.get("pending"):
                    semantic_reply = clarifier["reply"]
                    pending_clarification_update = clarifier["pending"]

        if frame.normalized_text:
            turn_metrics = build_turn_metrics(
                frame,
                requirements_complete=is_requirement_complete(merged_fields),
                had_pending_before=had_pending_before,
            )
            semantic_trace = frame.to_trace(metrics=turn_metrics)

        awaiting_confirmation = (
            is_requirement_complete(merged_fields)
            and not validation_errors
            and not user_confirmed
        )
        if semantic_reply:
            reply = semantic_reply
        else:
            reply = await _generate_collect_reply(
                state,
                merged_fields,
                validation_errors=validation_errors or None,
                awaiting_confirmation=awaiting_confirmation,
                dialogue_text=dialogue,
            )

    state_update: dict[str, Any] = {
        "departure_city": merged_fields.get("departure_city"),
        "departure_date": merged_fields.get("departure_date"),
        "start_date": merged_fields.get("departure_date"),
        "travel_days": merged_fields.get("travel_days"),
        "adult_count": merged_fields.get("adult_count"),
        "children_count": merged_fields.get("children_count"),
        "party_confirmed": is_party_confirmed(merged_fields),
        "budget_min": merged_fields.get("budget_min"),
        "budget_max": merged_fields.get("budget_max"),
        "destination": merged_fields.get("destination"),
        "travel_styles": merged_fields.get("travel_styles") or [],
        "special_needs": merged_fields.get("special_needs"),
        "user_confirmed": user_confirmed,
    }

    if pending_clarification_update is not None:
        state_update["pending_clarification"] = pending_clarification_update or None

    if semantic_trace is not None:
        state_update["semantic_trace"] = semantic_trace

    dialogue = _dialogue_text(messages)

    if can_advance_to_planning(merged_fields, user_confirmed=user_confirmed, dialogue_text=dialogue):
        requirement = build_user_requirement(merged_fields)
        req = requirement.model_dump()
        state_update.update(
            {
                "current_step": "plan_destination",
                "requirements_complete": True,
                "user_requirement": req,
                "destination": req.get("destination"),
                "start_date": req["departure_date"],
                "messages": [AIMessage(content=reply)],
            },
        )
        return state_update

    state_update.update(
        {
            "current_step": "collect_requirements",
            "requirements_complete": False,
            "messages": [AIMessage(content=reply)],
        },
    )
    return state_update


def _fallback_reply(
    fields: dict[str, Any],
    exc: Exception | None,
    *,
    validation_errors: list[str] | None = None,
) -> str:
    if validation_errors:
        return "请纠正以下信息：\n" + "\n".join(f"- {e}" for e in validation_errors)

    missing: list[str] = []
    if not fields.get("departure_city"):
        missing.append("出发城市")
    if not fields.get("departure_date"):
        missing.append("出发日期")
    if not fields.get("travel_days"):
        missing.append("出行天数")
    if fields.get("budget_min") is None or fields.get("budget_max") is None:
        missing.append("预算范围")

    prefix = ""
    if exc is not None:
        err = str(exc).lower()
        if "connection" in err or "connect" in err:
            prefix = "（AI 服务连接失败，请检查网络或稍后再试）\n"
        else:
            prefix = "（AI 服务暂不可用，请稍后再试）\n"

    if missing:
        template = render_collect_followup(fields, dialogue_text="")
        if prefix:
            return f"{prefix}{template}"
        return template
    return f"{prefix}请确认以上旅行需求是否正确？"
