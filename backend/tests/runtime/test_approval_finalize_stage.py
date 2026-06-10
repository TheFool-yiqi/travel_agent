"""Approve-or-revise and finalize stage tests."""

from __future__ import annotations

import pytest

from app.runtime.finalization.persistence import StubItineraryPersistenceAdapter
from app.runtime.stages.approve_or_revise import ApproveOrReviseStageHandler
from app.runtime.stages.finalize import FinalizeStageHandler
from app.runtime.stages.verify import VerifyStageHandler

from .test_verify_stage import _state_after_integrate


@pytest.mark.asyncio
async def test_approve_or_revise_waits_without_approval_keyword() -> None:
    state = await _state_after_integrate()
    state = {**state, "input_message": "我先看看行程草案"}

    result = await ApproveOrReviseStageHandler().handle(state)

    assert result["status"] == "waiting"
    assert result["data"]["pending_approval"]["destination"] == "成都"
    assert result["data"]["state"]["pending_approval"] is not None


@pytest.mark.asyncio
async def test_approve_or_revise_applies_user_revision_and_reopens_approval() -> None:
    state = await _state_after_integrate()
    verify_result = await VerifyStageHandler().handle(state)
    state = verify_result["data"]["state"]
    state = {**state, "input_message": "我想修改行程，请根据我的偏好重新调整。"}

    result = await ApproveOrReviseStageHandler().handle(state)

    assert result["status"] == "waiting"
    assert result["data"]["approval_status"] == "pending"
    assert result["data"]["itinerary_draft"] is not None
    assert "按用户偏好调整后的体验" in str(result["data"]["itinerary_draft"])
    assert result["data"]["state"]["revision_count"] == 1
    assert result["data"]["quality_report"] is not None


@pytest.mark.asyncio
async def test_approve_or_revise_completes_on_confirm() -> None:
    state = await _state_after_integrate()
    state = {**state, "input_message": "确认"}

    result = await ApproveOrReviseStageHandler().handle(state)

    assert result["status"] == "completed"
    assert result["data"]["approval_status"] == "approved"


@pytest.mark.asyncio
async def test_finalize_generates_order_and_persists_with_stub() -> None:
    state = await _state_after_integrate()
    verify_result = await VerifyStageHandler().handle(state)
    state = verify_result["data"]["state"]
    approve_result = await ApproveOrReviseStageHandler().handle(
        {**state, "input_message": "确认"},
    )
    state = approve_result["data"]["state"]

    persistence = StubItineraryPersistenceAdapter()
    finalize_result = await FinalizeStageHandler(persistence=persistence).handle(
        {
            **state,
            "conversation_id": "conv_1",
            "user_id": "user_1",
        },
    )

    assert finalize_result["status"] == "completed"
    assert finalize_result["data"]["order_id"].startswith("ORDER-")
    assert finalize_result["data"]["finalization_result"]["persisted"] is True
    assert len(persistence.records) == 1


@pytest.mark.asyncio
async def test_finalize_fails_without_approval() -> None:
    state = await _state_after_integrate()

    result = await FinalizeStageHandler().handle(state)

    assert result["status"] == "failed"
