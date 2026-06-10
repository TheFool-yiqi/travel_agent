"""Finalization schema tests."""

from __future__ import annotations

from app.runtime.finalization.schemas import FinalizationResult, PendingApproval


def test_pending_approval_round_trip() -> None:
    pending = PendingApproval(
        itinerary_summary="成都 3天草案",
        destination="成都",
        travel_days=3,
        assumption_summary=["证据不足假设"],
    )
    restored = PendingApproval.from_runtime_dict(pending.to_runtime_dict())
    assert restored == pending


def test_finalization_result_round_trip() -> None:
    result = FinalizationResult(
        order_id="ORDER-ABC12345",
        final_message="订单生成成功",
        destination="成都",
        travel_days=3,
        persisted=True,
        itinerary_id="itinerary-1",
    )
    restored = FinalizationResult.from_runtime_dict(result.to_runtime_dict())
    assert restored == result
