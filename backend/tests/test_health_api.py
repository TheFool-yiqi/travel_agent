"""Root / health API tests."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") == "ok"


@pytest.mark.asyncio
async def test_api_v1_routes_under_prefix() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register = await client.post(
            "/api/v1/users/register",
            json={"username": "x", "email": "not-email", "password": "short"},
        )
    assert register.status_code == 422
