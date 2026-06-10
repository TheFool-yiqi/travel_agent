"""Frontend adapter unit tests."""

from __future__ import annotations

from app.runtime.events import (
    make_runtime_completed_event,
    make_runtime_failed_event,
    make_stage_completed_event,
    make_stage_started_event,
)
from app.runtime.streaming.frontend_adapter import adapt_runtime_event_to_frontend_events
from app.runtime.streaming.stage_labels import assert_labels_cover_manifest


def test_runtime_stage_labels_cover_manifest() -> None:
    assert_labels_cover_manifest()


def test_adapt_stage_started_to_step() -> None:
    event = make_stage_started_event(run_id="run_1", stage="domain_plan")
    payloads = adapt_runtime_event_to_frontend_events(event)

    assert payloads == [
        {
            "type": "step",
            "step": "domain_plan",
            "label": "领域规划",
        },
    ]


def test_adapt_integrate_emits_itinerary() -> None:
    event = make_stage_completed_event(
        run_id="run_1",
        stage="integrate",
        output={
            "status": "completed",
            "data": {
                "itinerary_draft": {
                    "destination": "成都",
                    "travel_days": 2,
                    "days": [{"day_number": 1, "theme": "抵达", "activities": ["宽窄巷子"]}],
                    "budget": {"total": 3000},
                },
            },
        },
    )
    payloads = adapt_runtime_event_to_frontend_events(event)

    assert any(
        item["type"] == "itinerary"
        and item["itinerary"][0]["theme"] == "抵达"
        and item["budget"]["total"] == 3000
        for item in payloads
    )


def test_adapt_approve_waiting_emits_approval_required_and_token() -> None:
    event = make_stage_completed_event(
        run_id="run_1",
        stage="approve_or_revise",
        output={
            "status": "waiting",
            "data": {
                "pending_approval": {
                    "status": "pending",
                    "public_prompt": "请确认行程草案",
                },
                "itinerary_draft": {
                    "destination": "成都",
                    "travel_days": 2,
                    "days": [{"day_number": 1, "theme": "抵达", "activities": []}],
                    "budget": {"total": 3000},
                },
                "public_reply": "请确认行程草案",
            },
        },
    )
    payloads = adapt_runtime_event_to_frontend_events(event)

    assert any(item["type"] == "itinerary" for item in payloads)
    assert {"type": "approval_required", "message": "请确认行程草案"} in payloads
    assert {"type": "token", "content": "请确认行程草案"} in payloads


def test_adapt_finalize_emits_order_and_token() -> None:
    event = make_stage_completed_event(
        run_id="run_1",
        stage="finalize",
        output={
            "status": "completed",
            "data": {
                "order_id": "ORDER-123",
                "public_reply": "订单已生成，编号 ORDER-123。",
            },
        },
    )
    payloads = adapt_runtime_event_to_frontend_events(event)

    assert {"type": "order", "order_id": "ORDER-123"} in payloads
    assert {"type": "token", "content": "订单已生成，编号 ORDER-123。"} in payloads


def test_adapt_runtime_completed_to_done() -> None:
    event = make_runtime_completed_event(run_id="run_1")
    assert adapt_runtime_event_to_frontend_events(event) == [{"type": "done"}]


def test_adapt_runtime_failed_to_error() -> None:
    event = make_runtime_failed_event(
        run_id="run_1",
        stage="collect",
        error={"message": "collect failed"},
    )
    payloads = adapt_runtime_event_to_frontend_events(event)

    assert payloads == [{"type": "error", "message": "collect failed"}]


def test_adapt_skips_internal_visibility_events() -> None:
    event = make_runtime_failed_event(
        run_id="run_1",
        stage="collect",
        error={"message": "hidden"},
        visibility="internal",
    )
    assert adapt_runtime_event_to_frontend_events(event) == []
