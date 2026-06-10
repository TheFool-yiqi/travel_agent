"""Finalize stage."""

from __future__ import annotations

from app.runtime.finalization.final_response import FinalResponseGenerator
from app.runtime.finalization.persistence import StubItineraryPersistenceAdapter
from app.runtime.finalization.schemas import FinalizationResult
from app.runtime.planning.schemas import ItineraryDraft
from app.runtime.stages.base import StageResult
from app.runtime.state import RuntimeState, set_finalization_result, set_order_id

STAGE_NAME = "finalize"


class FinalizeStageHandler:
    stage_name = STAGE_NAME

    def __init__(
        self,
        *,
        response_generator: FinalResponseGenerator | None = None,
        persistence: StubItineraryPersistenceAdapter | None = None,
    ) -> None:
        self._response_generator = response_generator or FinalResponseGenerator()
        self._persistence = persistence

    async def handle(self, state: RuntimeState) -> StageResult:
        if state.get("approval_status") != "approved":
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="finalize requires approved itinerary",
                data={
                    "error": {
                        "type": "approval_not_granted",
                        "message": "finalize requires approval_status=approved",
                    },
                },
            )

        draft_raw = state.get("itinerary_draft")
        if not draft_raw:
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="finalize requires itinerary_draft",
                data={
                    "error": {
                        "type": "missing_itinerary_draft",
                        "message": "finalize requires itinerary_draft",
                    },
                },
            )

        draft = ItineraryDraft.from_runtime_dict(draft_raw)
        existing_order_id = state.get("order_id")
        finalization = self._response_generator.build(
            draft,
            order_id=existing_order_id,
        )

        if self._persistence is not None:
            session_id = state.get("conversation_id")
            user_id = state.get("user_id")
            if session_id and user_id:
                persist_result = await self._persistence.persist_approved_itinerary(
                    session_id=session_id,
                    user_id=user_id,
                    itinerary_draft=draft,
                    order_id=finalization.order_id,
                )
                finalization = FinalizationResult(
                    **{
                        **finalization.to_runtime_dict(),
                        "persisted": bool(persist_result.get("persisted")),
                        "itinerary_id": persist_result.get("itinerary_id"),
                    },
                )

        finalization_dict = finalization.to_runtime_dict()
        updated_state = set_finalization_result(
            set_order_id(state, finalization.order_id),
            finalization_dict,
        )

        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary="finalization completed",
            data={
                "finalization_result": finalization_dict,
                "order_id": finalization.order_id,
                "public_reply": finalization.final_message,
                "state": updated_state,
            },
        )
