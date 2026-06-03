"""异常与边界测试（TC-NEG 可编程部分）。"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.graph.middleware import apply_step_config_for_model_call
from app.graph.validators.requirements import sanitize_budget, sanitize_travel_styles, validate_requirements
from app.main import app
from app.schemas.travel import VALID_TRANSPORT


@pytest.fixture
async def authed_client():
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        username="neg",
        email="neg@t.com",
        password_hash="x",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    async def _db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_invalid_uuid_chat_history_400(authed_client: AsyncClient) -> None:
    """TC-NEG-003: 非法 UUID → 400。"""
    resp = await authed_client.get("/api/v1/chat/history/not-a-uuid")
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_invalid_uuid_chat_stream_400(authed_client: AsyncClient) -> None:
    resp = await authed_client.post(
        "/api/v1/chat/stream/not-a-uuid",
        json={"content": "hi"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_random_uuid_session_not_found(authed_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-NEG-004: 不存在会话 → 404。"""
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=None),
    )
    resp = await authed_client.get(f"/api/v1/sessions/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_past_departure_date_validation() -> None:
    """TC-NEG-010: 过去日期触发校验警告。"""
    errors = validate_requirements(
        {
            "departure_city": "上海",
            "departure_date": "2020-01-01",
            "travel_days": 3,
            "budget_min": 1000,
            "budget_max": 3000,
        },
    )
    assert any("早于今天" in e for e in errors)


def test_valid_transport_enum_excludes_ship() -> None:
    """TC-NEG-005: 非法交通 enum 不在 VALID_TRANSPORT。"""
    assert "train" in VALID_TRANSPORT
    assert "ship" not in VALID_TRANSPORT


def test_graph_missing_transport_requires() -> None:
    """TC-NEG-023: 缺 selected_transport 时 step requires 报错。"""
    with pytest.raises(ValueError, match="selected_transport"):
        apply_step_config_for_model_call(
            "plan_stay_and_food",
            {"selected_destination": "北京"},
            instruction="hi",
        )


@pytest.mark.asyncio
async def test_empty_message_stream_422(authed_client: AsyncClient) -> None:
    """TC-NEG-001 / TC-CHAT-008: 空 content → 422。"""
    resp = await authed_client.post(
        f"/api/v1/chat/stream/{uuid.uuid4()}",
        json={"content": ""},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_whitespace_message_stream_422(authed_client: AsyncClient) -> None:
    """TC-NEG-002: 仅空白字符 → 422。"""
    resp = await authed_client.post(
        f"/api/v1/chat/stream/{uuid.uuid4()}",
        json={"content": "   "},
    )
    assert resp.status_code == 422


def test_invalid_transport_ship_not_extracted() -> None:
    """TC-NEG-005 / TC-PLAN-011: ship 不在 VALID_TRANSPORT。"""
    from app.graph.nl_extract import _rule_based_selection

    assert "ship" not in VALID_TRANSPORT
    assert _rule_based_selection("坐船").selected_transport is None


def test_sem_032_fuzzy_clarify_loop_guard() -> None:
    """TC-NEG-025 / TC-SEM-032: 连续模糊输入仍返回 frame。"""
    from app.graph.semantic.slot_tracker import bind_utterance_to_slots

    state: dict = {}
    for _ in range(10):
        frame = bind_utterance_to_slots("天堂", state, state)
        assert frame is not None
        if frame.pending_clarification:
            state["pending_clarification"] = frame.pending_clarification


@pytest.mark.asyncio
async def test_neg_018_long_username_422() -> None:
    """TC-NEG-018: 超长 username → 422。"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/users/register",
            json={
                "username": "u" * 256,
                "email": "long@example.com",
                "password": "secret12",
            },
        )
    assert resp.status_code == 422


def test_sanitize_clears_hallucinated_slots() -> None:
    """TC-NEG-024: sanitize 清除幻觉槽位。"""
    fields = {
        "destination": "北京",
        "budget_min": 2000,
        "budget_max": 5000,
        "travel_styles": ["culture"],
    }
    dialogue = "用户: 北京\n助手: 好的"
    cleaned = sanitize_budget(
        sanitize_travel_styles(fields, dialogue_text=dialogue),
        dialogue_text=dialogue,
    )
    assert "budget_min" not in cleaned
    assert cleaned.get("travel_styles") in (None, [])


def test_neg_008_negative_travel_days_validation() -> None:
    """TC-NEG-008: 无效 travel_days < 1 触发校验。"""
    errors = validate_requirements(
        {
            "departure_city": "上海",
            "departure_date": "2026-06-19",
            "travel_days": 0,
            "budget_min": 1000,
            "budget_max": 3000,
        },
    )
    assert any("至少为 1" in e for e in errors)


def test_neg_009_extreme_travel_days_validation() -> None:
    """TC-NEG-009: 999 天触发合理上限警告。"""
    errors = validate_requirements(
        {
            "departure_city": "上海",
            "departure_date": "2026-06-19",
            "travel_days": 999,
            "budget_min": 1000,
            "budget_max": 3000,
        },
    )
    assert any("60" in e for e in errors)


def test_neg_019_emoji_only_no_slot_pollution() -> None:
    """TC-NEG-019: emoji 仅消息不污染 destination 槽。"""
    from app.graph.semantic.slot_tracker import bind_utterance_to_slots

    fields = {"destination": "北京", "departure_city": "上海", "departure_date": "2026-06-19"}
    frame = bind_utterance_to_slots("😀😀", fields, {})
    assert frame is not None
    updates = frame.slot_updates or {}
    assert "destination" not in updates
    assert "departure_city" not in updates


@pytest.mark.asyncio
async def test_neg_022_bare_revision_routes_to_revise() -> None:
    """TC-NEG-022: approval 阶段仅「修改」→ 进入 revise 并给出调整提示。"""
    from langchain_core.messages import HumanMessage

    from app.graph.nodes.approval_node import approval_node

    result = await approval_node(
        {
            "itinerary": [{"day_number": 1}],
            "messages": [HumanMessage(content="修改")],
        }
    )
    assert result["current_step"] == "revise_itinerary"
    assert "调整" in result["messages"][0].content


def test_neg_020_xss_payload_not_accepted_as_city() -> None:
    """TC-NEG-020: XSS payload 不被当作有效目的地。"""
    from app.graph.semantic.destination_resolver import resolve_destination_input

    res = resolve_destination_input("<script>alert(1)</script>")
    assert res.city is None
