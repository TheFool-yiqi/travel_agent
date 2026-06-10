"""Graph-era shared collect / semantic helpers (PlanningRuntime reuse)."""

from app.graph.state import TravelState

__all__ = [
    "TravelState",
    "assert_step_requirements",
    "get_step_config",
    "invoke_step_llm",
    "list_planning_steps",
    "prepare_step_context",
    "render_step_prompt",
]


def __getattr__(name: str):
    if name == "render_step_prompt":
        from app.ai.prompts.loader import render_step_prompt

        return render_step_prompt
    if name in ("assert_step_requirements", "get_step_config", "list_planning_steps"):
        from app.graph import step_config

        return getattr(step_config, name)
    if name in ("prepare_step_context", "invoke_step_llm", "StepContext"):
        from app.graph import step_context

        return getattr(step_context, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
