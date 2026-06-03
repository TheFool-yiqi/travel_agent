"""用户纠错反馈：识别「不对，是 XX」并更新槽位。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.graph.semantic.city_lexicon import match_cities
from app.graph.semantic.place_lexicon import lookup_place, resolve_place_destination
from app.graph.templates.collect_guidance import next_guidance_step
from app.tools.datetime_tools import parse_relative_date

_DATE_CORRECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:出发)?日期改(?:为|成|到)\s*(?P<value>.+)"),
    re.compile(r"日期改到\s*(?P<value>.+)"),
    re.compile(r"改成\s*(?P<value>\d{1,2}月\d{1,2}日)"),
)

_CORRECTION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"不对[，,.\s]*是(?P<value>[\u4e00-\u9fff]{2,10})"),
    re.compile(r"不是[\u4e00-\u9fff]{0,8}[，,.\s]*是(?P<value>[\u4e00-\u9fff]{2,10})"),
    re.compile(r"错了[，,.\s]*是(?P<value>[\u4e00-\u9fff]{2,10})"),
    re.compile(r"(?P<slot>目的地|出发地|出发城市)改(?:为|成)(?P<value>[\u4e00-\u9fff]{2,10})"),
    re.compile(r"(?P<slot>目的地|出发地|出发城市)[改为成是](?P<value>[\u4e00-\u9fff]{2,10})"),
    re.compile(r"改成(?P<value>[\u4e00-\u9fff]{2,10})"),
    re.compile(r"应该是(?P<value>[\u4e00-\u9fff]{2,10})"),
)

_SLOT_FIELD_MAP = {
    "destination": "destination",
    "departure_city": "departure_city",
    "目的地": "destination",
    "出发地": "departure_city",
    "出发城市": "departure_city",
}


@dataclass(frozen=True, slots=True)
class SlotCorrection:
    slot: str
    value: str
    original_text: str
    source: str = "user_correction"


def _resolve_place_or_city(name: str) -> str | None:
    name = name.strip()
    if not name:
        return None
    place = lookup_place(name) or resolve_place_destination(name)
    if place:
        return place
    matches = match_cities(name)
    if matches and matches[0].confidence >= 0.6:
        return matches[0].city
    return name if len(name) >= 2 else None


def _detect_date_correction(stripped: str) -> SlotCorrection | None:
    for pattern in _DATE_CORRECTION_PATTERNS:
        match = pattern.search(stripped)
        if not match:
            continue
        raw_value = match.group("value").strip()
        parsed = parse_relative_date(raw_value) or parse_relative_date(stripped)
        if parsed:
            return SlotCorrection(
                slot="departure_date",
                value=parsed,
                original_text=stripped,
            )
    return None


def detect_user_correction(
    text: str,
    fields: dict[str, Any],
    pending: dict[str, Any] | None = None,
) -> SlotCorrection | None:
    """检测用户主动纠错语句。"""
    stripped = text.strip()
    if not stripped:
        return None

    date_correction = _detect_date_correction(stripped)
    if date_correction is not None:
        return date_correction

    for pattern in _CORRECTION_PATTERNS:
        match = pattern.search(stripped)
        if not match:
            continue
        groups = match.groupdict()
        raw_value = groups.get("value", "").strip()
        resolved = _resolve_place_or_city(raw_value)
        if not resolved:
            continue

        slot_key = groups.get("slot")
        if slot_key:
            slot = _SLOT_FIELD_MAP.get(slot_key, "destination")
        elif re.search(r"改成|应该是", stripped) and fields.get("destination") and not re.search(
            r"(目的地|出发地|出发城市)", stripped
        ):
            slot = "destination"
        elif pending and pending.get("slot"):
            slot = pending["slot"]
        else:
            step = next_guidance_step(fields)
            slot = "destination" if step == "destination" else (
                "departure_city" if step == "departure_city" else "destination"
            )

        return SlotCorrection(slot=slot, value=resolved, original_text=stripped)

    # 澄清拒绝 + 同行给出新城市：「不是成都，是承德」
    if pending and re.search(r"不是|不对", stripped):
        tail = re.search(r"是([\u4e00-\u9fff]{2,10})\s*$", stripped)
        if tail:
            resolved = _resolve_place_or_city(tail.group(1))
            if resolved:
                return SlotCorrection(
                    slot=pending.get("slot", "destination"),
                    value=resolved,
                    original_text=stripped,
                )

    return None
