"""目的地语义解析：区域优先 + 白名单纠错 + 模糊仅澄清。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.graph.semantic.city_lexicon import CityMatch, lookup_city_by_pinyin, match_cities
from app.graph.semantic.place_lexicon import lookup_place, resolve_place_destination
from app.graph.semantic.region_lexicon import lookup_region

Action = Literal["accept", "clarify", "none"]

AUTO_ACCEPT_THRESHOLD = 0.85
CLARIFY_THRESHOLD = 0.60

# 常见境外目的地：不自动 accept，触发澄清/说明国内支持范围
_FOREIGN_DESTINATIONS = frozenset(
    {
        "东京",
        "大阪",
        "京都",
        "首尔",
        "曼谷",
        "新加坡",
        "纽约",
        "巴黎",
        "伦敦",
        "悉尼",
    }
)


@dataclass(frozen=True, slots=True)
class DestinationResolution:
    action: Action
    city: str | None = None
    confidence: float = 0.0
    original: str = ""
    candidates: tuple[str, ...] = ()


def _ambiguous_candidates(matches: list[CityMatch]) -> tuple[str, ...]:
    """多个接近的模糊候选 → 一并展示澄清。"""
    if len(matches) < 2:
        return tuple(m.city for m in matches[:3])
    top = matches[0].confidence
    close = [m for m in matches if m.confidence >= top - 0.05 and m.source == "fuzzy"]
    if len(close) >= 2:
        return tuple(m.city for m in close[:3])
    return tuple(m.city for m in matches[:3])


def resolve_destination_input(text: str) -> DestinationResolution:
    """解析用户输入的目的地候选。

    策略（由严到松）：
    1. 景点/区域别名、省级区域 — 精确 accept
    2. 城市精确 / 形近错字白名单 typo_auto — accept
    3. 同音近音 typo_confirm、任意 fuzzy — 仅 clarify，不自动写入
    4. 多候选接近 — clarify 并列出备选项
    """
    raw = text.strip()
    if not raw:
        return DestinationResolution(action="none", original=raw)

    if raw in _FOREIGN_DESTINATIONS:
        return DestinationResolution(
            action="clarify",
            city=None,
            confidence=0.0,
            original=raw,
            candidates=(),
        )

    region = lookup_region(raw)
    if region:
        return DestinationResolution(
            action="accept",
            city=region,
            confidence=1.0,
            original=raw,
            candidates=(region,),
        )

    place = lookup_place(raw) or resolve_place_destination(raw)
    if place:
        return DestinationResolution(
            action="accept",
            city=place,
            confidence=1.0,
            original=raw,
            candidates=(place,),
        )

    pinyin_entry = lookup_city_by_pinyin(raw)
    if pinyin_entry:
        return DestinationResolution(
            action="accept",
            city=pinyin_entry.name,
            confidence=1.0,
            original=raw,
            candidates=(pinyin_entry.name,),
        )

    matches = match_cities(raw)
    if not matches:
        return DestinationResolution(action="none", original=raw)

    best: CityMatch = matches[0]
    candidates = _ambiguous_candidates(matches)

    # 模糊匹配一律不自动采纳（仅白名单 typo_auto / exact 可 accept）
    if best.source == "fuzzy" or best.needs_confirm:
        if best.confidence >= CLARIFY_THRESHOLD:
            return DestinationResolution(
                action="clarify",
                city=best.city,
                confidence=best.confidence,
                original=raw,
                candidates=candidates,
            )
        return DestinationResolution(action="none", original=raw, candidates=candidates)

    if best.confidence < AUTO_ACCEPT_THRESHOLD:
        if best.confidence >= CLARIFY_THRESHOLD:
            return DestinationResolution(
                action="clarify",
                city=best.city,
                confidence=best.confidence,
                original=raw,
                candidates=candidates,
            )
        return DestinationResolution(action="none", original=raw, candidates=candidates)

    return DestinationResolution(
        action="accept",
        city=best.city,
        confidence=best.confidence,
        original=raw,
        candidates=candidates,
    )
