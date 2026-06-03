"""交通回复 grounding 校验"""

from __future__ import annotations

import re

# 常见航班号 / 车次号模式
_FLIGHT_PATTERN = re.compile(r"\b[A-Z]{2}\d{3,4}\b|\b\d{2,3}[A-Z]{2}\d{3,4}\b")
_TRAIN_PATTERN = re.compile(r"\b[GDCZTKL]\d{1,4}\b")


def validate_transport_reply(reply: str, tool_context: str) -> list[str]:
    """
    检查回复是否引用了工具结果中不存在的具体班次号。
    无 tool_context 时不做班次校验（仅依赖 prompt 约束）。
    """
    if not reply.strip() or not tool_context.strip():
        return []

    errors: list[str] = []
    context_upper = tool_context.upper()
    for pattern in (_FLIGHT_PATTERN, _TRAIN_PATTERN):
        for match in pattern.findall(reply.upper()):
            token = match.upper()
            if token not in context_upper:
                errors.append(f"回复中的班次/车次 {token} 未出现在工具查询结果中")
    return errors


def append_grounding_notice(reply: str, errors: list[str]) -> str:
    if not errors:
        return reply
    notice = "（以下方案来自查询结果；具体票价/时刻请以预订页面为准，以上为参考信息。）"
    if notice not in reply:
        reply = f"{notice}\n\n{reply}"
    return reply
