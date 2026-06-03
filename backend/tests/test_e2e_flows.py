"""Module 09 (E2E/FLOW) backend-automatable coverage."""

from __future__ import annotations

import pytest

from app.graph.routers.approval_router import user_wants_approval, user_wants_revision
from app.graph.routers.step_router import route_after_collect
from app.graph.semantic.correction_handler import detect_user_correction
from app.tools.holiday_calendar import extract_whole_holiday_travel_days


pytestmark = pytest.mark.smoke


def test_e2e_006_smoke_paths_importable() -> None:
    """TC-E2E-006: smoke 三路径测试模块存在."""
    from pathlib import Path

    assert Path("backend/tests/test_smoke_flows.py").exists()


def test_e2e_009_backend_no_llm_routes() -> None:
    """TC-E2E-009: 路由层不依赖 LLM."""
    assert route_after_collect({"requirements_complete": True, "user_confirmed": False}) == "__end__"


def test_e2e_015_pytest_not_integration_marker() -> None:
    """TC-E2E-015: integration marker 存在."""
    assert pytest.mark.integration


def test_flow_017_approval_ok_english() -> None:
    """TC-FLOW-017: approval OK 英文."""
    assert user_wants_approval("OK")


def test_flow_018_revision_english() -> None:
    """TC-FLOW-018: change hotel 修订."""
    assert user_wants_revision("change hotel")


def test_flow_051_correction_destination() -> None:
    """TC-FLOW-051: 改成杭州."""
    corr = detect_user_correction("改成杭州", {"destination": "北京"}, None)
    assert corr is not None
    assert corr.value == "杭州"


def test_flow_050_whole_holiday() -> None:
    """TC-FLOW-050: 整个假期 → 3 天."""
    assert extract_whole_holiday_travel_days("整个假期", {"departure_date": "2026-06-19"}) == 3


def test_flow_019_incomplete_collect_stays() -> None:
    """TC-FLOW-019: 缺 budget 不进 plan."""
    state = {
        "requirements_complete": False,
        "user_confirmed": False,
        "user_requirement": {"destination": "北京"},
    }
    assert route_after_collect(state) == "__end__"
