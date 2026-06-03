"""LLM model tier selection tests."""

from __future__ import annotations

from app.ai.llm import get_chat_model, get_fast_chat_model
from app.graph.steps import FAST_LLM_STEPS


def test_fast_llm_steps_contains_collect_requirements() -> None:
    assert "collect_requirements" in FAST_LLM_STEPS


def test_get_chat_model_fast_uses_mimo_v25() -> None:
    model = get_fast_chat_model()
    assert model.model_name == "mimo-v2.5"


def test_get_chat_model_pro_uses_configured_pro() -> None:
    model = get_chat_model()
    assert model.model_name == "mimo-v2.5-pro"


def test_get_chat_model_fast_uses_lower_max_tokens() -> None:
    fast = get_fast_chat_model()
    pro = get_chat_model()
    assert fast.max_tokens < pro.max_tokens
