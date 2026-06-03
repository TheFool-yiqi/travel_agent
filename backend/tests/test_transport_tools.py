"""交通 tools/ 层单元测试（Route 1 入口）。"""

from __future__ import annotations

import pytest

import app.tools.transport as transport_module
from app.tools.transport import query_transport_options


@pytest.mark.asyncio
async def test_query_transport_options_delegates_to_coordinator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    async def fake_async(
        origin: str,
        destination: str,
        departure_date: str,
        *,
        transport_type: str | None = None,
        passenger_count: int = 1,
        user_preference: str = "",
    ) -> str:
        captured.update(
            {
                "origin": origin,
                "destination": destination,
                "departure_date": departure_date,
                "transport_type": transport_type,
                "passenger_count": passenger_count,
            }
        )
        return "mock transport report"

    monkeypatch.setattr(
        transport_module,
        "fetch_transport_options_async",
        fake_async,
    )

    result = await query_transport_options.ainvoke(
        {
            "origin_city": "北京",
            "destination_city": "西安",
            "departure_date": "2026-06-03",
            "transport_type": "train",
            "passenger_count": 2,
        }
    )

    assert result == "mock transport report"
    assert captured == {
        "origin": "北京",
        "destination": "西安",
        "departure_date": "2026-06-03",
        "transport_type": "train",
        "passenger_count": 2,
    }


@pytest.mark.asyncio
async def test_query_transport_options_empty_type_becomes_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_async(*_args, transport_type=None, **_kwargs) -> str:
        assert transport_type is None
        return "ok"

    monkeypatch.setattr(transport_module, "fetch_transport_options_async", fake_async)

    result = await query_transport_options.ainvoke(
        {
            "origin_city": "北京",
            "destination_city": "上海",
            "departure_date": "2026-06-03",
            "transport_type": "",
        }
    )
    assert result == "ok"
