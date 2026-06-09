"""Retrieve-evidence stage."""

from __future__ import annotations

from typing import Any

from app.knowledge.evidence_engine import EvidenceEngine
from app.runtime.stages.base import StageResult
from app.runtime.state import RuntimeState, set_evidence_context, set_sufficiency_result

STAGE_NAME = "retrieve_evidence"


class RetrieveEvidenceStageHandler:
    stage_name = STAGE_NAME

    def __init__(self, *, evidence_engine: EvidenceEngine | None = None) -> None:
        self._evidence_engine = evidence_engine or EvidenceEngine()

    async def handle(self, state: RuntimeState) -> StageResult:
        planning_need = state.get("planning_need")
        if not planning_need:
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="retrieve_evidence requires planning_need",
                data={
                    "error": {
                        "type": "missing_planning_need",
                        "message": "retrieve_evidence requires planning_need",
                    },
                },
            )

        base_context = state.get("base_context")
        evidence_context, sufficiency_result = self._evidence_engine.retrieve(
            planning_need,
            base_context,
        )
        evidence_context_dict = evidence_context.to_runtime_dict()
        sufficiency_result_dict = sufficiency_result.to_runtime_dict()

        updated_state = set_sufficiency_result(
            set_evidence_context(state, evidence_context_dict),
            sufficiency_result_dict,
        )

        summary = (
            "evidence retrieval completed"
            if sufficiency_result.is_sufficient
            else "evidence retrieval completed with assumptions required"
        )
        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary=summary,
            data={
                "evidence_context": evidence_context_dict,
                "sufficiency_result": sufficiency_result_dict,
                "state": updated_state,
            },
        )
