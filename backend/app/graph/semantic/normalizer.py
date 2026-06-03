"""文本规范化：去噪、口语替换、全角转半角。"""

from __future__ import annotations

import re
import unicodedata

from app.graph.semantic.frame import TextCorrection
from app.graph.semantic.intent_normalizer import expand_colloquial_phrases

_FULLWIDTH_SPACE = "\u3000"

# 常见口语/错字 → 规范表达（P1 基础词典，可扩展）
_COLLOQUIAL_REPLACEMENTS: tuple[tuple[str, str, str], ...] = (
    (r"粗去", "出去", "typo"),
    (r"粗来", "出来", "typo"),
    (r"咋样", "怎么样", "colloquial"),
    (r"啥时候", "什么时候", "colloquial"),
    (r"玩几天", "旅行天数", "colloquial"),
)

_COMPILED_REPLACEMENTS = tuple(
    (re.compile(pattern), corrected, reason) for pattern, corrected, reason in _COLLOQUIAL_REPLACEMENTS
)


def _to_halfwidth(text: str) -> str:
    chars: list[str] = []
    for char in text:
        code = ord(char)
        if code == 0x3000:
            chars.append(" ")
        elif 0xFF01 <= code <= 0xFF5E:
            chars.append(chr(code - 0xFEE0))
        else:
            chars.append(char)
    return "".join(chars)


def normalize_text(text: str) -> tuple[str, list[TextCorrection]]:
    """规范化用户输入，返回 (normalized_text, corrections)。"""
    if not text:
        return "", []

    raw = text.strip()
    normalized = _to_halfwidth(raw)
    normalized = re.sub(r"\s+", " ", normalized)
    corrections: list[TextCorrection] = []

    if normalized != raw:
        corrections.append(
            TextCorrection(
                original=raw,
                corrected=normalized,
                reason="whitespace_or_fullwidth",
                confidence=1.0,
            ),
        )

    for pattern, replacement, reason in _COMPILED_REPLACEMENTS:
        if pattern.search(normalized):
            updated = pattern.sub(replacement, normalized)
            if updated != normalized:
                corrections.append(
                    TextCorrection(
                        original=normalized,
                        corrected=updated,
                        reason=reason,
                        confidence=0.95,
                    ),
                )
                normalized = updated

    expanded = expand_colloquial_phrases(normalized)
    if expanded != normalized:
        corrections.append(
            TextCorrection(
                original=normalized,
                corrected=expanded,
                reason="colloquial_expand",
                confidence=0.92,
            ),
        )
        normalized = expanded

    # 去除不可见字符
    cleaned = "".join(ch for ch in normalized if unicodedata.category(ch) != "Cf")
    if cleaned != normalized:
        corrections.append(
            TextCorrection(
                original=normalized,
                corrected=cleaned,
                reason="strip_control_chars",
                confidence=1.0,
            ),
        )
        normalized = cleaned

    return normalized, corrections
