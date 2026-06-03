"""graph/middleware Route 1 等价层测试。"""

from __future__ import annotations

import pytest

from app.graph.middleware import (
    StepConfigBundle,
    apply_step_config_for_model_call,
    create_step_config_middleware,
)


@pytest.mark.asyncio
async def test_create_step_config_middleware_returns_bundle() -> None:
    bundle = await create_step_config_middleware()
    assert isinstance(bundle, StepConfigBundle)
    assert "plan_destination" in bundle.config


def test_apply_step_config_raises_on_missing_requires() -> None:
    with pytest.raises(ValueError, match="user_requirement"):
        apply_step_config_for_model_call("plan_destination", {}, instruction="hi")


def test_approval_node_requires_itinerary_and_budget() -> None:
    with pytest.raises(ValueError, match="itinerary"):
        apply_step_config_for_model_call(
            "approval_node",
            {"user_requirement": {}, "budget": {}},
            instruction="hi",
        )
    with pytest.raises(ValueError, match="budget"):
        apply_step_config_for_model_call(
            "approval_node",
            {"user_requirement": {}, "itinerary": [{}]},
            instruction="hi",
        )
