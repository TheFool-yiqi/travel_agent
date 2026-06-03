"""Step-aware 槽位绑定与规则抽取。"""

from __future__ import annotations

import re
from typing import Any

from langchain_core.messages import BaseMessage, HumanMessage

from app.graph.semantic.correction_handler import detect_user_correction
from app.graph.semantic.destination_resolver import resolve_destination_input
from app.graph.semantic.disambiguator import (
    ambiguity_to_pending,
    apply_budget_scope_resolution,
    detect_ambiguities,
)
from app.graph.semantic.frame import SemanticFrame, TextCorrection
from app.graph.semantic.intent_normalizer import extract_intent_slots
from app.graph.semantic.slot_sanitizer import sanitize_departure_city_collision
from app.graph.templates.collect_followup import (
    render_collect_followup,
    render_destination_ambiguity,
    render_destination_clarification,
    render_destination_unrecognized,
    render_travel_days_clarification,
)
from app.graph.templates.collect_guidance import GuidanceStep, next_guidance_step
from app.tools.datetime_tools import parse_relative_date
from app.tools.holiday_calendar import (
    detect_holiday_departure_date,
    extract_whole_holiday_travel_days,
)

_CLARIFY_CONFIRM = re.compile(
    r"^(对|是的?|嗯|没错|是|好|确认|可以|ok|OK)[!.?？\s]*$",
    re.IGNORECASE,
)
_CLARIFY_DENY = re.compile(r"^(不|不是|不对|错了|否)[!.?？\s]*$")
_TRAVEL_DAYS = re.compile(r"(\d+)\s*天")
_CITY_SLOT_STEPS = frozenset({"destination", "departure_city"})
_NON_CITY_HINT = re.compile(
    r"高铁|动车|火车|飞机|飞过去|自驾|开车|礼拜|周末|总共|一共|每人|人均|"
    r"\d+\s*天|\d+\s*人|大\s*\d|小|\d+\s*大|\d+\s*小|"
    r"穷游|一般党|富有党|学生党|万|元|块",
)


def last_human_text(messages: list[BaseMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            return content.strip()
    return ""


def is_short_city_attempt(text: str) -> bool:
    stripped = text.strip()
    if _NON_CITY_HINT.search(stripped):
        return False
    return 1 <= len(stripped) <= 8 and not re.search(r"[0-9a-zA-Z]", stripped)


def compute_missing_slots(fields: dict[str, Any]) -> list[str]:
    """按引导顺序返回仍缺失的槽位名。"""
    step = next_guidance_step(fields)
    if step == "done":
        return []
    order: list[GuidanceStep] = [
        "destination",
        "departure_city",
        "departure_date",
        "travel_days",
        "party",
        "budget",
    ]
    idx = order.index(step)
    return order[idx:]


def _slot_field_name(step: GuidanceStep) -> str | None:
    if step in ("destination", "departure_city"):
        return step
    if step == "departure_date":
        return "departure_date"
    if step == "travel_days":
        return "travel_days"
    return None


def _resolve_city_slot(text: str, slot: str) -> SemanticFrame:
    """城市类槽位（destination / departure_city）解析。"""
    frame = SemanticFrame(normalized_text=text, guidance_step=slot)
    if not is_short_city_attempt(text):
        return frame

    resolution = resolve_destination_input(text)
    field = slot

    if resolution.action == "accept" and resolution.city:
        frame.slot_updates[field] = resolution.city
        frame.confidence = resolution.confidence
        frame.extraction_source = "fuzzy" if resolution.original != resolution.city else "rule"
        return frame

    if resolution.action == "clarify" and resolution.city:
        candidates = resolution.candidates or (resolution.city,)
        if len(candidates) > 1:
            frame.reply_override = render_destination_ambiguity(
                resolution.original or text,
                candidates,
            )
        else:
            frame.reply_override = render_destination_clarification(
                resolution.city,
                resolution.original or text,
            )
        frame.pending_clarification = {
            "slot": slot,
            "kind": "city",
            "candidate": resolution.city,
            "original": resolution.original or text,
            "candidates": list(candidates),
        }
        frame.confidence = resolution.confidence
        frame.extraction_source = "fuzzy"
        if resolution.original and resolution.original != resolution.city:
            frame.corrections.append(
                TextCorrection(
                    original=resolution.original,
                    corrected=resolution.city,
                    reason="typo_confirm",
                    confidence=resolution.confidence,
                ),
            )
        return frame

    frame.reply_override = render_destination_unrecognized(text)
    frame.confidence = 0.0
    return frame


def _extract_rule_slots(
    text: str,
    step: GuidanceStep,
    fields: dict[str, Any] | None = None,
    *,
    dialogue_text: str = "",
) -> dict[str, Any]:
    """非城市类规则抽取（天数、日期）。"""
    fields = fields or {}
    updates: dict[str, Any] = {}
    if step == "travel_days" or step != "destination":
        days_match = _TRAVEL_DAYS.search(text)
        if days_match and not fields.get("travel_days"):
            updates["travel_days"] = int(days_match.group(1))

        if not updates.get("travel_days") and not fields.get("travel_days"):
            whole_holiday_days = extract_whole_holiday_travel_days(
                text,
                fields,
                dialogue_text=dialogue_text,
            )
            if whole_holiday_days:
                updates["travel_days"] = whole_holiday_days

    holiday_date = detect_holiday_departure_date(text)
    if holiday_date:
        updates["departure_date"] = holiday_date

    relative_date = parse_relative_date(text)
    if relative_date and "departure_date" not in updates:
        updates["departure_date"] = relative_date

    return updates


def _handle_pending_clarification(
    text: str,
    pending: dict[str, Any],
    fields: dict[str, Any],
) -> SemanticFrame:
    slot = pending.get("slot", "")
    kind = pending.get("kind", "city")
    frame = SemanticFrame(normalized_text=text, guidance_step=slot or kind)

    if kind == "budget_scope" and slot == "budget":
        if "每人" in text or "总共" in text or "人均" in text or "合计" in text:
            resolved = apply_budget_scope_resolution(fields, pending, text)
            if resolved:
                frame.slot_updates.update(resolved)
                frame.confidence = 1.0
                frame.extraction_source = "rule"
                frame.pending_clarification_cleared = True
                merged = {**fields, **frame.slot_updates}
                frame.reply_override = render_collect_followup(merged)
                return frame

    if kind == "travel_days" and slot == "travel_days":
        if _CLARIFY_CONFIRM.match(text):
            candidate = pending.get("candidate")
            if candidate is not None:
                frame.slot_updates["travel_days"] = int(candidate)
                frame.confidence = 1.0
                frame.extraction_source = "rule"
                frame.pending_clarification_cleared = True
                merged = {**fields, **frame.slot_updates}
                frame.reply_override = render_collect_followup(merged)
                return frame
        if _CLARIFY_DENY.match(text):
            clarifier = render_travel_days_clarification(fields, force_generic=True)
            frame.reply_override = clarifier["reply"]
            frame.pending_clarification_cleared = True
            return frame
        explicit_days = _TRAVEL_DAYS.search(text)
        if explicit_days:
            frame.slot_updates["travel_days"] = int(explicit_days.group(1))
            frame.pending_clarification_cleared = True
            merged = {**fields, **frame.slot_updates}
            frame.reply_override = render_collect_followup(merged)
            return frame

    if slot in _CITY_SLOT_STEPS:
        if _CLARIFY_CONFIRM.match(text):
            candidate = pending.get("candidate")
            if candidate and slot:
                frame.slot_updates[slot] = candidate
                frame.confidence = 1.0
                frame.extraction_source = "rule"
                frame.pending_clarification_cleared = True
                merged = sanitize_departure_city_collision(
                    {**fields, **frame.slot_updates},
                    state={"pending_clarification": pending},
                    frame=frame,
                )
                frame.reply_override = render_collect_followup(merged)
                original = pending.get("original", "")
                if original and original != candidate:
                    frame.corrections.append(
                        TextCorrection(
                            original=original,
                            corrected=candidate,
                            reason="user_confirmed_typo",
                            confidence=1.0,
                        ),
                    )
            return frame

        if _CLARIFY_DENY.match(text):
            frame.reply_override = render_destination_unrecognized(pending.get("original", text))
            frame.pending_clarification_cleared = True
            return frame

    return frame


def _apply_user_correction(
    text: str,
    fields: dict[str, Any],
    state: dict[str, Any],
    *,
    corrections: list[TextCorrection] | None = None,
) -> SemanticFrame | None:
    pending = state.get("pending_clarification")
    correction = detect_user_correction(text, fields, pending)
    if not correction:
        return None

    frame = SemanticFrame(
        normalized_text=text,
        corrections=list(corrections or []),
        guidance_step=next_guidance_step(fields),
    )
    frame.slot_updates[correction.slot] = correction.value
    frame.confidence = 1.0
    frame.extraction_source = "rule"
    frame.pending_clarification_cleared = True
    frame.corrections.append(
        TextCorrection(
            original=correction.original_text,
            corrected=correction.value,
            reason="user_correction",
            confidence=1.0,
        ),
    )
    merged = {**fields, **frame.slot_updates}
    frame.reply_override = render_collect_followup(merged)
    return frame


def _apply_intent_and_disambiguation(
    frame: SemanticFrame,
    text: str,
    fields: dict[str, Any],
    *,
    dialogue_text: str = "",
) -> SemanticFrame:
    step = frame.guidance_step
    intent_updates = extract_intent_slots(text, step, fields, dialogue_text=dialogue_text)
    if intent_updates:
        frame.slot_updates.update(intent_updates)
        frame.confidence = max(frame.confidence, 0.85)
        if frame.extraction_source == "rule":
            frame.extraction_source = "hybrid"

    ambiguities = detect_ambiguities(intent_updates, fields, guidance_step=step)
    if ambiguities:
        amb = ambiguities[0]
        frame.ambiguities = [
            {
                "kind": amb.kind,
                "slot": amb.slot,
                "question": amb.question,
                "options": list(amb.options),
            },
        ]
        frame.reply_override = amb.question
        frame.pending_clarification = ambiguity_to_pending(amb)
        for key in ("budget_scope", "budget_amount"):
            frame.slot_updates.pop(key, None)
    return frame


def bind_utterance_to_slots(
    text: str,
    fields: dict[str, Any],
    state: dict[str, Any],
    *,
    corrections: list[TextCorrection] | None = None,
    dialogue_text: str = "",
) -> SemanticFrame:
    """根据当前引导步骤，将用户输入绑定到对应槽位。"""
    corrected = _apply_user_correction(text, fields, state, corrections=corrections)
    if corrected:
        return corrected

    pending = state.get("pending_clarification")
    frame = SemanticFrame(
        normalized_text=text,
        corrections=list(corrections or []),
        guidance_step=next_guidance_step(fields),
    )

    if pending:
        clarified = _handle_pending_clarification(text, pending, fields)
        if clarified.slot_updates or clarified.reply_override or clarified.pending_clarification_cleared:
            frame = clarified
            frame.corrections = list(corrections or []) + frame.corrections
            frame.guidance_step = next_guidance_step(fields)
            return frame

    step = frame.guidance_step
    if step in _CITY_SLOT_STEPS:
        field_name = _slot_field_name(step)
        if field_name and not fields.get(field_name):
            city_frame = _resolve_city_slot(text, step)
            frame.slot_updates.update(city_frame.slot_updates)
            frame.corrections.extend(city_frame.corrections)
            frame.confidence = max(frame.confidence, city_frame.confidence)
            frame.extraction_source = city_frame.extraction_source
            if city_frame.reply_override:
                frame.reply_override = city_frame.reply_override
            if city_frame.pending_clarification:
                frame.pending_clarification = city_frame.pending_clarification
            if frame.slot_updates:
                return frame
            if city_frame.reply_override:
                return frame

    rule_updates = _extract_rule_slots(text, step, fields, dialogue_text=dialogue_text)
    if rule_updates:
        frame.slot_updates.update(rule_updates)
        frame.confidence = max(frame.confidence, 0.9)
        frame.extraction_source = "rule"

    if not frame.reply_override:
        frame = _apply_intent_and_disambiguation(frame, text, fields, dialogue_text=dialogue_text)

    return frame


def apply_slot_updates(fields: dict[str, Any], frame: SemanticFrame, state: dict[str, Any]) -> dict[str, Any]:
    """将 SemanticFrame 的 slot_updates 合并进 fields，并纠正误绑槽位。"""
    updated = dict(fields)
    step = frame.guidance_step

    for key, value in frame.slot_updates.items():
        if key in ("budget_scope", "budget_amount"):
            continue
        if value is not None and value != "":
            updated[key] = value

    # 纠正规则层误把城市写入 departure_city（destination 步骤）
    if step == "destination" and frame.slot_updates.get("destination"):
        last = frame.normalized_text
        if updated.get("departure_city") == last and not state.get("departure_city"):
            updated.pop("departure_city", None)

    return sanitize_departure_city_collision(updated, state, frame)
