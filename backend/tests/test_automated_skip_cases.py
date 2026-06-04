"""Automate former SKIP cases (batch-4)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.messages import HumanMessage

from app.db.session import get_db
from app.graph.nodes.approval_node import approval_node
from app.graph.nodes.plan_activities import plan_activities
from app.graph.nodes.plan_stay_and_food import plan_stay_and_food
from app.graph.nl_extract import _rule_based_selection
from app.graph.semantic.destination_resolver import resolve_destination_input
from app.main import app
from app.schemas.travel import VALID_ACCOMMODATION, VALID_ACTIVITY, VALID_FOOD


def _planning_state(**overrides) -> dict:
    base = {
        "user_requirement": {
            "destination": "北京",
            "departure_city": "上海",
            "departure_date": "2026-06-19",
            "travel_days": 3,
            "budget_min": 800,
            "budget_max": 2000,
        },
        "selected_destination": "北京",
        "selected_transport": "train",
        "messages": [],
    }
    base.update(overrides)
    return base


@pytest.mark.asyncio
async def test_neg_006_invalid_accommodation_rejected() -> None:
    """TC-NEG-006 / TC-PLAN-017: invalid stay enum does not advance."""
    state = _planning_state(selected_accommodation_types=["space_capsule"])
    result = await plan_stay_and_food(state)
    assert result["current_step"] == "plan_stay_and_food"
    assert "住宿类型无效" in result["messages"][0].content
    assert "selected_accommodation_types" not in result


@pytest.mark.asyncio
async def test_neg_007_invalid_activity_rejected() -> None:
    """TC-NEG-007 / TC-PLAN-021: invalid activity enum does not advance."""
    state = _planning_state(
        selected_accommodation_types=["economy_hotel"],
        selected_food_types=["local"],
        selected_activity_types=["skydiving"],
    )
    result = await plan_activities(state)
    assert result["current_step"] == "plan_activities"
    assert "活动类型无效" in result["messages"][0].content
    assert "build_itinerary" not in result.get("current_step", "")


def test_plan_020_multi_activity_rule_extract() -> None:
    """TC-PLAN-020: 文化+美食 maps to multiple activity enums."""
    extracted = _rule_based_selection("文化体验和美食之旅")
    assert "culture" in extracted.selected_activity_types
    assert "food_tour" in extracted.selected_activity_types


def test_nl_extract_filters_invalid_enums() -> None:
    """TC-PLAN-017: rule extract drops unknown accommodation tokens."""
    extracted = _rule_based_selection("胶囊太空舱")
    for item in extracted.selected_accommodation_types:
        assert item in VALID_ACCOMMODATION


@pytest.mark.asyncio
async def test_apr_011_vague_reply_stays_pending() -> None:
    """TC-APR-011: 再看看 stays on approval pending."""
    result = await approval_node(
        {
            "itinerary": [{"day_number": 1}],
            "approval_status": "pending",
            "messages": [HumanMessage(content="再看看")],
        }
    )
    assert result["current_step"] == "approval_node"
    assert result["approval_status"] == "pending"


@pytest.mark.asyncio
async def test_apr_021_fuzzy_replies_do_not_loop_forever() -> None:
    """TC-APR-021: repeated vague replies remain stable pending state."""
    state = {
        "itinerary": [{"day_number": 1}],
        "approval_status": "pending",
        "messages": [HumanMessage(content="再看看")],
    }
    for _ in range(5):
        result = await approval_node(state)
        assert result["current_step"] == "approval_node"
        assert result["approval_status"] == "pending"
        state = {**state, "messages": state["messages"] + [HumanMessage(content="再看看")]}


def test_sem_030_hong_kong_resolves() -> None:
    """TC-SEM-030: 香港 resolves via city lexicon."""
    res = resolve_destination_input("香港")
    assert res.action == "accept"
    assert res.city == "香港"


@pytest.mark.asyncio
async def test_api_016_register_missing_fields_422() -> None:
    """TC-API-016: register with missing required fields → 422."""
    mock_db = AsyncMock()

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/v1/users/register", json={"username": "onlyname"})
    app.dependency_overrides.clear()
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_api_022_basic_auth_rejected_401() -> None:
    """TC-API-022: Basic auth header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Basic dXNlcjpwYXNz"},
        )
    assert resp.status_code == 401


def test_neg_006_food_enum_guard() -> None:
    """TC-NEG-006 extension: invalid food enum filtered by rule extract."""
    extracted = _rule_based_selection("随便乱吃")
    assert all(f in VALID_FOOD for f in extracted.selected_food_types)


def test_plan_021_invalid_activity_not_in_valid_set() -> None:
    """TC-PLAN-021: 极限跳伞 not in VALID_ACTIVITY."""
    assert "skydiving" not in VALID_ACTIVITY
    extracted = _rule_based_selection("极限跳伞")
    assert "skydiving" not in extracted.selected_activity_types
