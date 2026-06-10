"""Approve-or-revise stage."""

from __future__ import annotations

from app.graph.routers.approval_router import user_wants_approval, user_wants_revision
from app.runtime.finalization.approval_payload import build_pending_approval
from app.runtime.stages.base import StageResult
from app.runtime.state import RuntimeState, clear_pending_approval, set_approval_status, set_pending_approval

STAGE_NAME = "approve_or_revise"


class ApproveOrReviseStageHandler:
    stage_name = STAGE_NAME

    async def handle(self, state: RuntimeState) -> StageResult:
        if not state.get("itinerary_draft"):
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="approve_or_revise requires itinerary_draft",
                data={
                    "error": {
                        "type": "missing_itinerary_draft",
                        "message": "approve_or_revise requires itinerary_draft",
                    },
                },
            )

        input_message = str(state.get("input_message") or "").strip()
        approval_status = state.get("approval_status")

        if approval_status == "approved" or user_wants_approval(input_message):
            updated_state = clear_pending_approval(
                set_approval_status(state, "approved"),
            )
            return StageResult(
                stage=self.stage_name,
                status="completed",
                summary="itinerary approved",
                data={
                    "approval_status": "approved",
                    "public_reply": "已确认行程，正在生成订单…",
                    "state": updated_state,
                },
            )

        if user_wants_revision(input_message):
            pending = build_pending_approval(state)
            pending_dict = pending.to_runtime_dict()
            pending_dict["status"] = "revising"
            pending_dict["public_prompt"] = "已收到修改意见。V1 Runtime 将在后续 Slice 接入完整修订路由。"
            updated_state = set_pending_approval(
                set_approval_status(state, "revising"),
                pending_dict,
            )
            return StageResult(
                stage=self.stage_name,
                status="waiting",
                summary="revision feedback received",
                data={
                    "approval_status": "revising",
                    "pending_approval": pending_dict,
                    "public_reply": pending_dict["public_prompt"],
                    "state": updated_state,
                },
            )

        pending = build_pending_approval(state)
        pending_dict = pending.to_runtime_dict()
        updated_state = set_pending_approval(
            set_approval_status(state, "pending"),
            pending_dict,
        )
        return StageResult(
            stage=self.stage_name,
            status="waiting",
            summary="awaiting itinerary approval",
            data={
                "approval_status": "pending",
                "pending_approval": pending_dict,
                "public_reply": pending_dict["public_prompt"],
                "state": updated_state,
            },
        )
