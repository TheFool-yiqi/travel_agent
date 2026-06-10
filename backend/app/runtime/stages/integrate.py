"""Integrate stage."""

from __future__ import annotations

from app.runtime.planning.integrator import ItineraryIntegrator
from app.runtime.planning.schemas import PlanProposal
from app.runtime.stages.base import StageResult
from app.runtime.state import RuntimeState, set_itinerary_draft

STAGE_NAME = "integrate"


class IntegrateStageHandler:
    stage_name = STAGE_NAME

    def __init__(self, *, integrator: ItineraryIntegrator | None = None) -> None:
        self._integrator = integrator or ItineraryIntegrator()

    async def handle(self, state: RuntimeState) -> StageResult:
        raw_proposals = state.get("plan_proposals")
        if not raw_proposals:
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="integrate requires plan_proposals",
                data={
                    "error": {
                        "type": "missing_plan_proposals",
                        "message": "integrate requires plan_proposals",
                    },
                },
            )

        proposals = [PlanProposal.from_runtime_dict(item) for item in raw_proposals]
        itinerary_draft = self._integrator.integrate(state, proposals)
        draft_dict = itinerary_draft.to_runtime_dict()
        updated_state = set_itinerary_draft(state, draft_dict)

        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary="itinerary integration completed",
            data={
                "itinerary_draft": draft_dict,
                "state": updated_state,
            },
        )
