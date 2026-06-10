"""Domain-plan stage."""

from __future__ import annotations

from app.runtime.planning.planner_group import DomainPlannerGroup
from app.runtime.stages.base import StageResult
from app.runtime.state import RuntimeState, set_plan_proposals

STAGE_NAME = "domain_plan"


class DomainPlanStageHandler:
    stage_name = STAGE_NAME

    def __init__(self, *, planner_group: DomainPlannerGroup | None = None) -> None:
        self._planner_group = planner_group or DomainPlannerGroup()

    async def handle(self, state: RuntimeState) -> StageResult:
        if not state.get("planning_need"):
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="domain_plan requires planning_need",
                data={
                    "error": {
                        "type": "missing_planning_need",
                        "message": "domain_plan requires planning_need",
                    },
                },
            )

        proposals = self._planner_group.run(state)
        proposal_dicts = [proposal.to_runtime_dict() for proposal in proposals]
        updated_state = set_plan_proposals(state, proposal_dicts)

        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary="domain planning completed",
            data={
                "plan_proposals": proposal_dicts,
                "state": updated_state,
            },
        )
