"""plan_activities 节点冒烟测试。"""

import inspect

from app.graph.nodes import plan_activities as plan_activities_module
from app.graph.nodes.plan_activities import plan_activities
from app.schemas.travel import VALID_ACTIVITY


def test_plan_activities_is_async_callable() -> None:
    assert inspect.iscoroutinefunction(plan_activities)


def test_plan_activities_module_exports() -> None:
    assert plan_activities_module.plan_activities is plan_activities


def test_valid_activity_types() -> None:
    assert "culture" in VALID_ACTIVITY
    assert len(VALID_ACTIVITY) == 5
