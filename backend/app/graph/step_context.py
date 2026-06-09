"""步骤 LLM 上下文准备（路线1 等价于 StepConfigMiddleware）"""

from dataclasses import dataclass

from langchain_core.messages import AIMessageChunk, BaseMessage, HumanMessage, SystemMessage
from loguru import logger

from app.ai.llm import get_chat_model
from app.ai.prompts.loader import render_step_prompt
from app.graph.state import TravelState
from app.graph.step_config import assert_step_requirements, get_step_tools
from app.graph.steps import FAST_LLM_STEPS, normalize_step
from app.graph.stream_callback import emit_stream_token, get_stream_token_handler
from app.settings import settings
from app.tools.router import fetch_destination_info
from app.tools.search import fetch_travel_search
from app.tools.datetime_tools import today_beijing_iso
from app.tools.transport import fetch_transport_options

# 进入 LLM prompt 的最近对话条数（不含 SystemMessage）
DIALOGUE_WINDOW_SIZE = 20


@dataclass(frozen=True)
class StepContext:
    """单步 LLM 调用所需的上下文"""

    step: str
    system_prompt: str
    missing: list[str]

    @property
    def ready(self) -> bool:
        return not self.missing


def prepare_step_context(step: str, state: TravelState) -> StepContext:
    """
    校验前置字段并渲染步骤 system prompt。

    等价于 StepConfigMiddleware 中的 requires 校验 + prompt 填充。
    """
    step = normalize_step(step)
    missing = assert_step_requirements(step, state)
    if missing:
        logger.warning("步骤 {} 前置条件未满足: {}", step, missing)
        return StepContext(step=step, system_prompt="", missing=missing)

    system_prompt = render_step_prompt(step, state)
    logger.debug("步骤 {} prompt 已渲染，长度 {}", step, len(system_prompt))
    return StepContext(step=step, system_prompt=system_prompt, missing=[])


def _transport_route_context(state: TravelState) -> tuple[str, str, str] | None:
    requirement = state.get("user_requirement") or {}
    origin = requirement.get("departure_city") or state.get("departure_city")
    destination = (
        state.get("selected_destination")
        or state.get("destination")
        or requirement.get("destination")
    )
    departure_date = (
        requirement.get("departure_date")
        or state.get("departure_date")
        or state.get("start_date")
    )
    if not origin or not destination or not departure_date:
        return None
    return origin, destination, departure_date


def _run_query_destination_info(state: TravelState) -> str | None:
    requirement = state.get("user_requirement") or {}
    destination = (
        state.get("selected_destination")
        or state.get("destination")
        or requirement.get("destination")
    )
    if not destination:
        return None

    query = requirement.get("destination_query") or ""
    return fetch_destination_info(destination, query=query or None)


def _transport_passenger_count(state: TravelState) -> int:
    requirement = state.get("user_requirement") or {}
    adults = int(requirement.get("adult_count") or 1)
    children = int(requirement.get("children_count") or 0)
    return adults + children


def _run_query_transport_plan(state: TravelState) -> str | None:
    route = _transport_route_context(state)
    if route is None:
        return None
    origin, destination, departure_date = route
    requirement = state.get("user_requirement") or {}
    preference = requirement.get("special_needs") or ""
    transport_type = state.get("selected_transport")
    return fetch_transport_options(
        origin,
        destination,
        departure_date,
        transport_type=transport_type,
        passenger_count=_transport_passenger_count(state),
        user_preference=preference or "",
    )


def _run_get_current_date(_state: TravelState) -> str:
    from app.tools.datetime_tools import date_context_for_prompt

    return f"今天日期（北京时间）：{today_beijing_iso()}\n\n{date_context_for_prompt()}"


def _run_search_travel_info(state: TravelState) -> str | None:
    requirement = state.get("user_requirement") or {}
    destination = (
        state.get("selected_destination")
        or state.get("destination")
        or requirement.get("destination")
    )
    if not destination:
        return None
    query = requirement.get("destination_query") or f"{destination} 旅游攻略 景点推荐"
    return fetch_travel_search(query, max_results=3)


_STEP_TOOL_RUNNERS = {
    "query_destination_info": _run_query_destination_info,
    "query_transport_plan": _run_query_transport_plan,
    "query_transport_options": _run_query_transport_plan,
    "get-current-date": _run_get_current_date,
    "search_travel_info": _run_search_travel_info,
    "search_web_travel_info": _run_search_travel_info,
}


def run_step_tools(step: str, state: TravelState) -> str:
    """
    按 step_config.tools 显式执行工具（路线1 替代 LLM 自动 tool call）。

    参考 Handoffs 中 middleware 注入 tools 列表；此处由节点预执行并把结果拼进 prompt。
    """
    step = normalize_step(step)
    parts: list[str] = []
    for tool in get_step_tools(step):
        runner = _STEP_TOOL_RUNNERS.get(tool.name)
        if runner is None:
            logger.warning("步骤 {} 未注册工具运行器: {}", step, tool.name)
            continue
        result = runner(state)
        if result:
            parts.append(result)
    return "\n\n".join(parts)


def build_step_instruction(step: str, state: TravelState, base_instruction: str) -> str:
    """将工具查询结果与步骤 instruction 合并"""
    tool_context = run_step_tools(step, state)
    if not tool_context:
        return base_instruction
    return f"【工具查询结果】\n{tool_context}\n\n{base_instruction}"


def build_step_messages(
    system_prompt: str,
    state: TravelState,
    *,
    instruction: str | None = None,
) -> list[BaseMessage]:
    """组装 LLM 消息：步骤 system prompt + 当前轮 memory_context + 窗口化对话历史"""
    prior = state.get("messages") or []
    dialogue = [message for message in prior if not isinstance(message, SystemMessage)]
    if len(dialogue) > DIALOGUE_WINDOW_SIZE:
        dialogue = dialogue[-DIALOGUE_WINDOW_SIZE:]

    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

    memory_context = state.get("memory_context")
    if memory_context:
        messages.append(SystemMessage(content=memory_context))

    messages.extend(dialogue)
    if instruction:
        messages.append(HumanMessage(content=instruction))
    return messages


async def invoke_step_llm(
    step: str,
    state: TravelState,
    *,
    instruction: str | None = None,
    ctx: StepContext | None = None,
) -> str:
    """按 current_step 配置调用 MiMo，返回模型文本回复（有 stream handler 时逐 token 推送）。"""
    ctx = ctx or prepare_step_context(step, state)
    if not ctx.ready:
        raise ValueError(f"步骤 {step} 前置条件未满足: {', '.join(ctx.missing)}")

    messages = build_step_messages(ctx.system_prompt, state, instruction=instruction)
    logger.info("调用 LLM: step={} message_count={}", ctx.step, len(messages))

    streaming = get_stream_token_handler() is not None
    use_fast = normalize_step(step) in FAST_LLM_STEPS
    model = get_chat_model(streaming=streaming, fast=use_fast)
    if use_fast:
        logger.debug("步骤 {} 使用 fast 模型 {}", step, settings.mimo_model_fast)

    if streaming:
        parts: list[str] = []
        async for chunk in model.astream(messages):
            if not isinstance(chunk, AIMessageChunk):
                continue
            token = chunk.content
            if not isinstance(token, str):
                token = str(token) if token is not None else ""
            if not token:
                continue
            parts.append(token)
            await emit_stream_token(token)
        return "".join(parts)

    response = await model.ainvoke(messages)
    content = response.content
    if not isinstance(content, str):
        content = str(content)
    return content
