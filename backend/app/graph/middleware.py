"""
Handoffs StepConfigMiddleware 的 Route 1 等价层。

参考：单 Agent + AgentMiddleware 在每次 model call 前注入 prompt/tools。
本项目：Graph 节点显式调用 prepare_step_context + run_step_tools，不绑 AgentMiddleware。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from langchain_core.tools import BaseTool

from app.graph.state import TravelState
from app.graph.step_config import assert_step_requirements, get_step_config, get_step_tools
from app.graph.step_context import (
    StepContext,
    build_step_instruction,
    prepare_step_context,
)
from app.graph.steps import normalize_step


@dataclass(frozen=True)
class StepConfigBundle:
    """预加载的步骤配置（兼容 Handoffs middleware 预加载结果）。"""

    config: dict[str, dict[str, Any]]

    def get(self, step: str) -> dict[str, Any]:
        step = normalize_step(step)
        if step not in self.config:
            raise ValueError(f"未知步骤: {step}")
        return self.config[step]


async def create_step_config_middleware() -> StepConfigBundle:
    """
    兼容 Handoffs `create_step_config_middleware()` 工厂函数名。

    返回预加载的 step_config，而非 LangChain AgentMiddleware 实例。
    Route 1 节点请使用 `apply_step_config_for_model_call`。
    """
    return StepConfigBundle(config=await get_step_config())


def apply_step_config_for_model_call(
    step: str,
    state: TravelState,
    *,
    instruction: str = "",
) -> tuple[StepContext, list[BaseTool], str]:
    """
    等价于 StepConfigMiddleware.awrap_model_call 的配置注入阶段（不含 LLM 调用）。

    Returns:
        (step_context, tools, instruction_with_optional_tool_results)
    """
    step = normalize_step(step)
    ctx = prepare_step_context(step, state)
    if not ctx.ready:
        missing = ", ".join(ctx.missing)
        raise ValueError(f"步骤 {step} 需要完整状态: {missing} 未设置")

    tools = get_step_tools(step)
    merged_instruction = build_step_instruction(step, state, instruction)
    return ctx, tools, merged_instruction


# 别名：与参考 middleware 模块中类名对应，便于文档对照
StepConfigMiddleware = StepConfigBundle  # type: ignore[misc,assignment]

__all__ = [
    "StepConfigBundle",
    "StepConfigMiddleware",
    "apply_step_config_for_model_call",
    "assert_step_requirements",
    "create_step_config_middleware",
    "prepare_step_context",
]
