"""Approve-or-revise stage."""

from __future__ import annotations

from app.graph.routers.approval_router import user_wants_approval, user_wants_revision
from app.runtime.finalization.approval_payload import build_pending_approval
from app.runtime.quality.revision_agent import RevisionAgent
from app.runtime.quality.verifier import QualityVerifier
from app.runtime.stages.base import StageResult
from app.runtime.state import (
    RuntimeState,
    clear_pending_approval,
    increment_revision_count,
    set_approval_status,
    set_itinerary_draft,
    set_pending_approval,
    set_quality_report,
)

STAGE_NAME = "approve_or_revise"
_REVISION_PROMPT = (
    "行程已根据您的意见更新，请查看右侧行程卡片。\n"
    "若满意请回复「确认」；如需继续调整请说明修改点。"
)


class ApproveOrReviseStageHandler:
    stage_name = STAGE_NAME

    def __init__(
        self,
        *,
        revision_agent: RevisionAgent | None = None,
        verifier: QualityVerifier | None = None,
    ) -> None:
        self._revision_agent = revision_agent or RevisionAgent()
        self._verifier = verifier or QualityVerifier()

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

        if approval_status == "approved" or (
            user_wants_approval(input_message) and not user_wants_revision(input_message)
        ):
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
            revised = self._revision_agent.revise_from_user_feedback(state, input_message)
            revised_dict = revised.to_runtime_dict()
            updated_state = increment_revision_count(
                set_itinerary_draft(state, revised_dict),
            )
            report = self._verifier.verify(updated_state)
            updated_state = set_quality_report(updated_state, report.to_runtime_dict())
            return _waiting_result(
                updated_state,
                public_prompt=_REVISION_PROMPT,
                summary="revision applied and awaiting re-approval",
                quality_report=report.to_runtime_dict(),
            )

        pending = build_pending_approval(state)
        return _waiting_result(
            state,
            public_prompt=pending.public_prompt,
            summary="awaiting itinerary approval",
        )


def _waiting_result(
    state: RuntimeState,
    *,
    public_prompt: str,
    summary: str,
    quality_report: dict | None = None,
) -> StageResult:
    pending = build_pending_approval(state)
    pending_dict = pending.to_runtime_dict()
    pending_dict["public_prompt"] = public_prompt
    draft_dict = state.get("itinerary_draft")
    updated_state = set_pending_approval(
        set_approval_status(state, "pending"),
        pending_dict,
    )
    return StageResult(
        stage=STAGE_NAME,
        status="waiting",
        summary=summary,
        data={
            "approval_status": "pending",
            "pending_approval": pending_dict,
            "itinerary_draft": draft_dict,
            "public_reply": public_prompt,
            "quality_report": quality_report,
            "state": updated_state,
        },
    )
