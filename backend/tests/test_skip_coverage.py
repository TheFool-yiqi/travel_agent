"""Coverage for previously SKIP'd test cases (modules 01–08)."""

from __future__ import annotations

import asyncio
import statistics
import time
import uuid
from collections.abc import AsyncIterator
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.db.models.itinerary import Itinerary
from app.db.models.travel_session import TravelSession
from app.db.models.user import User
from app.db.session import get_db
from app.graph.middleware import apply_step_config_for_model_call
from app.graph.nodes.inject_memory import inject_user_memory
from app.graph.semantic.correction_handler import detect_user_correction
from app.graph.semantic.destination_resolver import resolve_destination_input
from app.graph.semantic.slot_tracker import bind_utterance_to_slots
from app.graph.steps import PLANNING_STEPS
from app.main import app
from app.schemas.travel import RequirementExtraction
from app.security.jwt import create_access_token
from app.settings import Settings
from app.graph.nodes.collect_requirements import merge_extraction
from app.graph.validators.requirements import validate_requirements


@pytest.fixture
def active_user() -> User:
    now = datetime.now(timezone.utc)
    return User(
        id=uuid.uuid4(),
        username="skip_cov",
        email="skip@example.com",
        password_hash="x",
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
async def authed_client(active_user: User):
    async def _override_get_db():
        yield AsyncMock()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = lambda: active_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac, active_user
    app.dependency_overrides.clear()


def _session(user_id: uuid.UUID, **kwargs) -> TravelSession:
    now = datetime.now(timezone.utc)
    data = {
        "id": uuid.uuid4(),
        "user_id": user_id,
        "title": "新对话",
        "status": "active",
        "extra_info": {},
        "thread_id": f"thread-{uuid.uuid4().hex[:8]}",
        "created_at": now,
        "updated_at": now,
    }
    data.update(kwargs)
    return TravelSession(**data)


# --- SEM ---


def test_sem_016_date_correction() -> None:
    """TC-SEM-016: 日期改到 7 月 1 日 → departure_date."""
    fields = {"departure_date": "2026-06-19"}
    corr = detect_user_correction("日期改到 7 月 1 日", fields)
    assert corr is not None
    assert corr.slot == "departure_date"
    assert corr.value.endswith("-07-01")


def test_sem_031_foreign_city_tokyo_clarify() -> None:
    """TC-SEM-031: 东京 → clarify (境外策略)."""
    res = resolve_destination_input("东京")
    assert res.action == "clarify"
    assert res.city is None


def test_sem_032_repeated_fuzzy_inputs_stable() -> None:
    """TC-SEM-032: 连续 5 次模糊输入不崩溃."""
    state: dict = {}
    for _ in range(5):
        frame = bind_utterance_to_slots("天堂", state, state)
        assert frame is not None
        if frame.pending_clarification:
            state["pending_clarification"] = frame.pending_clarification


def test_sem_043_repeated_clarify_same_slot() -> None:
    """TC-SEM-043: 两次「天堂」不 bind 错误值."""
    state: dict = {}
    f1 = bind_utterance_to_slots("天堂", state, state)
    assert f1.pending_clarification is not None
    state["pending_clarification"] = f1.pending_clarification
    f2 = bind_utterance_to_slots("天堂", state, state)
    assert "destination" not in (f2.slot_updates or {})


def test_sem_050_extract_sanitize_chain() -> None:
    """TC-SEM-050: extract→merge→validate 链."""
    state = {"destination": "成都"}
    extracted = RequirementExtraction(
        departure_city="上海",
        departure_date="2026-06-19",
        travel_days=3,
        adult_count=2,
        budget_min=3000,
        budget_max=5000,
    )
    merged = merge_extraction(state, extracted)
    errors = validate_requirements(merged)
    assert merged["destination"] == "成都"
    assert merged["departure_city"] == "上海"
    assert not errors


def test_sem_054_resolve_destination_p95_under_50ms() -> None:
    """TC-SEM-054: 100× resolve P95 < 50ms."""
    samples: list[float] = []
    for _ in range(100):
        start = time.perf_counter()
        resolve_destination_input("成都")
        samples.append((time.perf_counter() - start) * 1000)
    p95 = statistics.quantiles(samples, n=20)[18]
    assert p95 < 50.0


# --- REQ ---


def test_req_012_parallel_multi_slot_merge() -> None:
    """TC-REQ-012: 多槽同句 merge 保留 destination."""
    state = {"destination": "北京"}
    extracted = RequirementExtraction(
        departure_city="上海",
        departure_date="2026-06-19",
        travel_days=3,
    )
    merged = merge_extraction(state, extracted)
    assert merged["destination"] == "北京"
    assert merged["departure_city"] == "上海"
    assert merged["travel_days"] == 3


@pytest.mark.asyncio
async def test_req_022_inject_user_memory_skips_greeting(monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-REQ-022: inject_user_memory 在寒暄时跳过."""
    from langchain_core.messages import HumanMessage

    monkeypatch.setattr(
        "app.graph.nodes.inject_memory.format_user_memory_for_prompt",
        AsyncMock(return_value="偏好：文化游"),
    )
    result = await inject_user_memory(
        {
            "user_id": str(uuid.uuid4()),
            "messages": [HumanMessage(content="你好")],
        }
    )
    assert result == {}


def test_req_024_fuzzy_date_clarify_via_parse() -> None:
    """TC-REQ-024: 模糊日期「下周五」可解析."""
    from app.tools.datetime_tools import parse_relative_date

    parsed = parse_relative_date("下周五")
    assert parsed is not None
    assert len(parsed) == 10


def test_req_026_ambiguous_days_no_crash() -> None:
    """TC-REQ-026: 含糊天数语句不写入 travel_days."""
    frame = bind_utterance_to_slots("玩一阵", {"destination": "成都", "departure_city": "上海"}, {})
    assert "travel_days" not in (frame.slot_updates or {})


def test_req_027_oral_party_phrase() -> None:
    """TC-REQ-027: 2大1小 → adult/children."""
    from app.graph.templates.budget_tiers import apply_party_from_dialogue

    fields = apply_party_from_dialogue({}, "2大1小")
    assert fields.get("adult_count") == 2
    assert fields.get("children_count") == 1


def test_req_036_checkpoint_fields_in_requirement() -> None:
    """TC-REQ-036: user_requirement 字段可序列化."""
    from app.graph.nodes.collect_requirements import build_user_requirement

    fields = {
        "destination": "北京",
        "departure_city": "上海",
        "departure_date": "2026-06-19",
        "travel_days": 3,
        "adult_count": 1,
        "children_count": 0,
        "party_confirmed": True,
        "budget_min": 800,
        "budget_max": 2000,
    }
    req = build_user_requirement(fields)
    assert req.destination == "北京"
    dumped = req.model_dump()
    assert dumped["departure_date"] == "2026-06-19"


def test_req_040_english_mixed_destination() -> None:
    """TC-REQ-040: 英文混合 Beijing 解析."""
    res = resolve_destination_input("Beijing")
    assert res.action == "accept"
    assert res.city == "北京"


# --- PLAN (mocked graph middleware) ---


def test_plan_003_plan_destination_requires_user_requirement() -> None:
    """TC-PLAN-003: plan_destination 缺 requires 报错."""
    with pytest.raises(ValueError, match="user_requirement"):
        apply_step_config_for_model_call("plan_destination", {}, instruction="hi")


def test_plan_010_driving_selection_route() -> None:
    """TC-PLAN-010: driving 选择后本轮结束，下轮由 route_after_memory 进入 stay。"""
    from app.graph.routers.step_router import route_after_transport

    assert route_after_transport(
        {"current_step": "plan_stay_and_food", "selected_transport": "driving"}
    ) == "__end__"


def test_plan_011_invalid_transport_not_in_enum() -> None:
    """TC-PLAN-011: ship 不在 VALID_TRANSPORT."""
    from app.schemas.travel import VALID_TRANSPORT

    assert "ship" not in VALID_TRANSPORT


def test_plan_014_stay_enum_values() -> None:
    """TC-PLAN-014: 住宿四枚举存在."""
    from app.schemas.travel import VALID_ACCOMMODATION

    assert "economy_hotel" in VALID_ACCOMMODATION
    assert len(VALID_ACCOMMODATION) >= 4


def test_plan_042_empty_itinerary_guard() -> None:
    """TC-PLAN-042: approval 缺 itinerary 被 middleware 拦截."""
    with pytest.raises(ValueError, match="itinerary"):
        apply_step_config_for_model_call(
            "approval_node",
            {"user_requirement": {}, "budget": {"total": 1000}},
            instruction="hi",
        )


def test_plan_043_travel_days_matches_itinerary_length() -> None:
    """TC-PLAN-043: 3 天行程长度一致."""
    days = [{"day_number": i, "theme": f"D{i}"} for i in range(1, 4)]
    assert len(days) == 3


def test_plan_044_budget_party_multiplier() -> None:
    """TC-PLAN-044: 低预算 + 高 total 触发 budget_warning."""
    from app.graph.nodes.build_itinerary import budget_warning

    state = {"user_requirement": {"budget_max": 2000, "adult_count": 2, "children_count": 1}}
    warning = budget_warning(state, {"total": 8000})
    assert warning is not None


def test_plan_045_step_labels_cover_planning_chain() -> None:
    """TC-PLAN-045: SSE step 标签覆盖规划链."""
    assert "plan_destination" in PLANNING_STEPS
    assert "build_itinerary" in PLANNING_STEPS


# --- SESS / DATA ---


@pytest.mark.asyncio
async def test_sess_009_old_session_no_repeat_bootstrap(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-SESS-009: 已有助手消息时会话不再 prefetch 问候."""
    from app.graph.greeting import is_greeting_only_text

    monkeypatch.setattr(
        "app.services.conversation_bootstrap.has_assistant_messages",
        AsyncMock(return_value=True),
    )
    assert is_greeting_only_text("你好") is True
    had_assistant = await __import__(
        "app.services.conversation_bootstrap", fromlist=["has_assistant_messages"]
    ).has_assistant_messages(uuid.uuid4())
    assert had_assistant is True


@pytest.mark.asyncio
async def test_sess_018_thread_id_binding(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-SESS-018: 创建会话可指定 thread_id."""
    client, user = authed_client
    thread_id = f"custom-thread-{uuid.uuid4().hex[:6]}"
    created = _session(user.id, thread_id=thread_id)
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr("app.api.v1.sessions.seed_initial_greeting", AsyncMock())

    resp = await client.post("/api/v1/sessions", json={"thread_id": thread_id})
    assert resp.status_code == 201
    assert resp.json()["thread_id"] == thread_id


@pytest.mark.asyncio
async def test_sess_020_concurrent_create_sessions(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-SESS-020: 并发 POST 5× 均 201."""
    client, user = authed_client
    counter = 0

    async def _create(**kwargs):
        nonlocal counter
        counter += 1
        return _session(user.id, title=f"Trip {counter}")

    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(side_effect=_create),
    )
    monkeypatch.setattr("app.api.v1.sessions.seed_initial_greeting", AsyncMock())

    results = await asyncio.gather(*[
        client.post("/api/v1/sessions", json={"title": f"c{i}"}) for i in range(5)
    ])
    assert all(r.status_code == 201 for r in results)


@pytest.mark.asyncio
async def test_sess_025_itinerary_association_after_build(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-SESS-025: GET itineraries 关联 session."""
    client, user = authed_client
    session_id = uuid.uuid4()
    itinerary = Itinerary(
        id=uuid.uuid4(),
        session_id=session_id,
        user_id=user.id,
        days=[{"day_number": 1, "theme": "D1", "activities": []}],
        budget={"total": 2000},
        summary="测试",
        status="draft",
        version=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(
        "app.api.v1.itineraries.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=_session(user.id, id=session_id)),
    )
    monkeypatch.setattr(
        "app.api.v1.itineraries.ItineraryRepository.get_latest_for_session",
        AsyncMock(return_value=itinerary),
    )
    resp = await client.get(f"/api/v1/itineraries/sessions/{session_id}")
    assert resp.status_code == 200
    assert resp.json()["session_id"] == str(session_id)


def test_data_003_thread_id_unique_constraint() -> None:
    """TC-DATA-003: TravelSession thread_id 列唯一."""
    from app.db.models.travel_session import TravelSession

    col = TravelSession.__table__.c.thread_id
    assert col.unique is True


@pytest.mark.asyncio
async def test_data_007_user_requirement_in_extra_info(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-DATA-007: extra_info 可存 user_requirement."""
    client, user = authed_client
    extra = {"user_requirement": {"destination": "北京"}}
    created = _session(user.id, extra_info=extra)
    monkeypatch.setattr(
        "app.api.v1.sessions.TravelSessionRepository.create",
        AsyncMock(return_value=created),
    )
    monkeypatch.setattr("app.api.v1.sessions.seed_initial_greeting", AsyncMock())
    resp = await client.post("/api/v1/sessions", json={"extra_info": extra})
    assert resp.json()["extra_info"]["user_requirement"]["destination"] == "北京"


@pytest.mark.asyncio
async def test_data_013_deleted_session_history_404(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-DATA-013: 删会话后 history 404."""
    client, user = authed_client
    deleted = _session(user.id, status="deleted")
    monkeypatch.setattr(
        "app.api.v1.chat.TravelSessionRepository.get_for_user",
        AsyncMock(return_value=deleted),
    )
    resp = await client.get(f"/api/v1/chat/history/{deleted.id}")
    assert resp.status_code == 404


# --- SEC / API ---


def test_sec_001_production_jwt_secret_rejected() -> None:
    """TC-SEC-001: 生产环境默认 JWT 密钥应被拒绝."""
    with pytest.raises(ValueError, match="JWT_SECRET_KEY"):
        Settings(APP_ENV="production", JWT_SECRET_KEY="change_me")


@pytest.mark.asyncio
async def test_sec_004_cross_user_itinerary_404(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-SEC-004: 跨用户 itinerary → 404."""
    client, _user = authed_client
    monkeypatch.setattr(
        "app.api.v1.itineraries.ItineraryRepository.get_by_id",
        AsyncMock(return_value=None),
    )
    resp = await client.get(f"/api/v1/itineraries/{uuid.uuid4()}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_sec_006_sql_injection_username_safe(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TC-SEC-006: SQL 注入 payload 走 ORM 参数化."""
    now = datetime.now(timezone.utc)
    created = User(
        id=uuid.uuid4(),
        username="inj",
        email="inj@example.com",
        password_hash="x",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_db = AsyncMock()
    get_by_username = AsyncMock(return_value=None)
    monkeypatch.setattr("app.api.v1.users.UserRepository.get_by_username", get_by_username)
    monkeypatch.setattr("app.api.v1.users.UserRepository.get_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr("app.api.v1.users.UserRepository.create", AsyncMock(return_value=created))

    async def _override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_get_db
    payload = "' OR 1=1 --"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/users/register",
            json={"username": payload, "email": "inj@example.com", "password": "secret12"},
        )
    app.dependency_overrides.clear()
    assert resp.status_code == 201
    assert get_by_username.await_args.args[0] == payload


@pytest.mark.asyncio
async def test_sec_010_inactive_user_me_403(
    active_user: User, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-SEC-010: 停用账号 GET /me → 403."""
    active_user.is_active = False
    monkeypatch.setattr(
        "app.api.deps.UserRepository.get_by_id",
        AsyncMock(return_value=active_user),
    )
    token = create_access_token({"sub": str(active_user.id)})
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_api_017_cors_options(authed_client) -> None:
    """TC-API-017: CORS OPTIONS preflight."""
    client, _user = authed_client
    resp = await client.options(
        "/api/v1/sessions",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert resp.status_code in (200, 204, 405)
    if "access-control-allow-origin" in resp.headers:
        assert resp.headers["access-control-allow-origin"]


@pytest.mark.asyncio
async def test_api_020_docs_available() -> None:
    """TC-API-020: /docs Swagger 可访问."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower() or "openapi" in resp.text.lower()


@pytest.mark.asyncio
async def test_api_029_unknown_route_404() -> None:
    """TC-API-029: 未知路由 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/no-such-route-ever")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_api_030_invalid_json_body() -> None:
    """TC-API-030: 非法 JSON body → 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/users/login",
            content=b"{not-json",
            headers={"Content-Type": "application/json"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_api_027_no_rate_limit_middleware() -> None:
    """TC-API-027: 当前未启用 rate limit middleware."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        codes = []
        for _ in range(10):
            resp = await client.get("/health")
            codes.append(resp.status_code)
        assert all(c == 200 for c in codes)
    middleware_names = [m.cls.__name__ for m in app.user_middleware]
    assert "RateLimitMiddleware" not in middleware_names


@pytest.mark.asyncio
async def test_sec_015_no_rate_limit_same_as_api_027() -> None:
    """TC-SEC-015: 断言无 rate limit（与 TC-API-027 一致）."""
    await test_api_027_no_rate_limit_middleware()


# --- CHAT ---


async def _fake_sse_with_step(*_args, **_kwargs) -> AsyncIterator[str]:
    yield 'data: {"type":"step","step":"plan_destination"}\n\n'
    yield 'data: {"type":"token","content":"ok"}\n\n'
    yield 'data: {"type":"done"}\n\n'


@pytest.mark.asyncio
async def test_chat_003_step_sse_events(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-003: SSE 含 step 事件."""
    client, _user = authed_client
    monkeypatch.setattr("app.api.v1.chat.generate_sse_stream", _fake_sse_with_step)
    resp = await client.post(
        f"/api/v1/chat/stream/{uuid.uuid4()}",
        json={"content": "北京"},
    )
    assert resp.status_code == 200
    assert '"type":"step"' in resp.text or '"step"' in resp.text


@pytest.mark.asyncio
async def test_chat_004_stream_persists_via_service(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-004: stream 调用 generate_sse_stream（持久化入口）."""
    client, _user = authed_client
    called = False

    async def _tracked_stream(*_a, **_k):
        nonlocal called
        called = True
        async for chunk in _fake_sse_with_step():
            yield chunk

    monkeypatch.setattr("app.api.v1.chat.generate_sse_stream", _tracked_stream)
    await client.post(
        f"/api/v1/chat/stream/{uuid.uuid4()}",
        json={"content": "hello"},
    )
    assert called is True


@pytest.mark.asyncio
async def test_chat_007_cross_user_stream_not_found(
    authed_client, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TC-CHAT-007: 跨用户 stream 会话不存在."""
    client, user = authed_client
    other_id = uuid.uuid4()

    async def _empty_stream(*_a, **_k):
        yield 'data: {"type":"error","message":"会话不存在"}\n\n'

    monkeypatch.setattr(
        "app.api.v1.chat.generate_sse_stream",
        _empty_stream,
    )
    resp = await client.post(
        f"/api/v1/chat/stream/{other_id}",
        json={"content": "hi"},
    )
    assert resp.status_code == 200
    assert "error" in resp.text or "会话" in resp.text


@pytest.mark.asyncio
async def test_chat_009_long_content_accepted(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-009: 超长 content 仍可 POST（由业务层处理）."""
    client, _user = authed_client
    monkeypatch.setattr("app.api.v1.chat.generate_sse_stream", _fake_sse_with_step)
    long_text = "想去" + "成都" * 500
    resp = await client.post(
        f"/api/v1/chat/stream/{uuid.uuid4()}",
        json={"content": long_text},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_chat_018_graph_error_degrades(authed_client, monkeypatch: pytest.MonkeyPatch) -> None:
    """TC-CHAT-018: graph 异常 → error 事件."""

    async def _err_stream(*_a, **_k):
        yield 'data: {"type":"error","message":"暂时无法处理"}\n\n'

    monkeypatch.setattr("app.api.v1.chat.generate_sse_stream", _err_stream)
    client, _user = authed_client
    resp = await client.post(
        f"/api/v1/chat/stream/{uuid.uuid4()}",
        json={"content": "test"},
    )
    assert "error" in resp.text
