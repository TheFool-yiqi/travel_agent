"""Approval and revision keyword detection for PlanningRuntime."""

from __future__ import annotations

import re


APPROVE_KEYWORDS = (
    "确认",
    "同意",
    "可以",
    "没问题",
    "好的",
    "ok",
    "approve",
    "通过",
)

REVISE_KEYWORDS = (
    "修改",
    "改一下",
    "调整",
    "重新",
    "不满意",
    "换",
    "revise",
    "change",
    "改行程",
)


def user_wants_approval(text: str) -> bool:
    lower = text.lower()
    return any(keyword in text or keyword in lower for keyword in APPROVE_KEYWORDS)


def user_wants_revision(text: str) -> bool:
    lower = text.lower()
    if any(keyword in text or keyword in lower for keyword in REVISE_KEYWORDS):
        return True
    return bool(re.search(r"改[\u4e00-\u9fff]{1,8}", text))
