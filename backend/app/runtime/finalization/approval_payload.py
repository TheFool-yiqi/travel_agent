"""Build pending approval payload from runtime state."""

from __future__ import annotations

from app.runtime.finalization.schemas import PendingApproval
from app.runtime.planning.schemas import ItineraryDraft
from app.runtime.state import RuntimeState

_APPROVAL_PROMPT = (
    "行程草案已生成，请查看右侧行程卡片。\n"
    "若满意请回复「确认」；如需调整请说明修改点或回复「修改行程」。"
)


def build_pending_approval(state: RuntimeState) -> PendingApproval:
    draft = ItineraryDraft.from_runtime_dict(state["itinerary_draft"])
    quality = state.get("quality_report") or {}
    return PendingApproval(
        status="pending",
        itinerary_summary=draft.summary,
        destination=draft.destination,
        travel_days=draft.travel_days,
        assumption_summary=list(draft.assumptions),
        evidence_card_ids=list(draft.evidence_card_ids),
        quality_summary={
            "is_acceptable": quality.get("is_acceptable"),
            "suggested_action": quality.get("suggested_action"),
            "score": quality.get("score"),
        },
        public_prompt=_APPROVAL_PROMPT,
    )
