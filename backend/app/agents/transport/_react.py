"""交通 Subagent / 协调器共用的 ReAct 图工厂。"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.tools import BaseTool
from langgraph.prebuilt import ToolNode, create_react_agent


def create_transport_react_agent(
    model: Any,
    tools: Sequence[BaseTool | Callable | dict[str, Any]],
    *,
    prompt: str,
):
    """创建 ReAct Agent；MCP 工具失败时回传错误给 LLM，而不是整图崩溃。"""
    tool_node = ToolNode(list(tools), handle_tool_errors=True)
    return create_react_agent(model, tool_node, prompt=prompt)
