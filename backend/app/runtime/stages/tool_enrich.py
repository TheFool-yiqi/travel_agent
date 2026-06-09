"""Tool-enrich stage."""

from __future__ import annotations

from app.runtime.stages.base import StageResult
from app.runtime.state import RuntimeState, set_tool_context
from app.runtime.tools.service import ToolService

STAGE_NAME = "tool_enrich"


class ToolEnrichStageHandler:
    stage_name = STAGE_NAME

    def __init__(self, *, tool_service: ToolService | None = None) -> None:
        self._tool_service = tool_service or ToolService()

    async def handle(self, state: RuntimeState) -> StageResult:
        planning_need = state.get("planning_need")
        if not planning_need:
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="tool_enrich requires planning_need",
                data={
                    "error": {
                        "type": "missing_planning_need",
                        "message": "tool_enrich requires planning_need",
                    },
                },
            )

        base_context = state.get("base_context")
        tool_context = self._tool_service.enrich(planning_need, base_context)
        tool_context_dict = tool_context.to_runtime_dict()
        updated_state = set_tool_context(state, tool_context_dict)

        weather = tool_context.weather
        if weather is not None and weather.status == "available":
            summary = "tool enrichment completed"
        else:
            summary = "tool enrichment completed with weather unavailable"

        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary=summary,
            data={
                "tool_context": tool_context_dict,
                "state": updated_state,
            },
        )
