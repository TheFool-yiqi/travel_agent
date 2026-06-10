"""Automate former SKIP cases that still apply after Runtime migration."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_db
from app.graph.nl_extract import _rule_based_selection
from app.graph.routers.approval_router import user_wants_revision
from app.graph.semantic.destination_resolver import resolve_destination_input
from app.main import app
from app.schemas.travel import VALID_ACCOMMODATION, VALID_ACTIVITY, VALID_FOOD


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


def test_apr_011_vague_reply_is_not_approval() -> None:
    """TC-APR-011: 再看看 不触发确认。"""
    assert not user_wants_revision("再看看")


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
