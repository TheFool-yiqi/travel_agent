"""步骤 Prompt 加载与渲染"""

import re
from functools import lru_cache
from pathlib import Path

from app.graph.steps import PLANNING_STEPS, STEP_LABELS, normalize_step

PROMPTS_DIR = Path(__file__).resolve().parent
_PLACEHOLDER = re.compile(r"\{([a-zA-Z0-9_\.]+)\}")


@lru_cache(maxsize=32)
def load_prompt_template(step: str) -> str:
    """加载步骤 prompt 模板（Markdown）"""
    step = normalize_step(step)
    path = PROMPTS_DIR / f"{step}.md"
    if not path.exists():
        raise FileNotFoundError(f"未找到步骤 prompt: {path}")
    return path.read_text(encoding="utf-8")


def _resolve_placeholder(state: dict, path: str) -> str:
    current: object = state
    for part in path.split("."):
        if not isinstance(current, dict):
            return "未设置"
        current = current.get(part)

    if current is None:
        return "未设置"
    if isinstance(current, list):
        return ", ".join(str(item) for item in current) if current else "未设置"
    return str(current)


def render_template(template: str, state: dict) -> str:
    """将 {user_requirement.departure_date} 等占位符替换为 state 中的值"""

    def replacer(match: re.Match[str]) -> str:
        return _resolve_placeholder(state, match.group(1))

    return _PLACEHOLDER.sub(replacer, template)


def render_step_prompt(step: str, state: dict) -> str:
    """渲染指定步骤的完整 system prompt"""
    step = normalize_step(step)
    template = load_prompt_template(step)
    enriched = dict(state)
    enriched["step_label"] = STEP_LABELS.get(step, step)
    enriched["step_number"] = (
        str(PLANNING_STEPS.index(step) + 1) if step in PLANNING_STEPS else "?"
    )
    enriched["total_steps"] = str(len(PLANNING_STEPS))
    return render_template(template, enriched).strip()
