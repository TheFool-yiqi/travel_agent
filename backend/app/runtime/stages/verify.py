"""Verify stage."""

from __future__ import annotations

from app.runtime.quality.revision_agent import RevisionAgent
from app.runtime.quality.schemas import QualityReport
from app.runtime.quality.verifier import QualityVerifier
from app.runtime.stages.base import StageResult
from app.runtime.state import (
    RuntimeState,
    increment_revision_count,
    set_itinerary_draft,
    set_quality_report,
)

STAGE_NAME = "verify"
MAX_AUTO_REVISION = 1


class VerifyStageHandler:
    stage_name = STAGE_NAME

    def __init__(
        self,
        *,
        verifier: QualityVerifier | None = None,
        revision_agent: RevisionAgent | None = None,
    ) -> None:
        self._verifier = verifier or QualityVerifier()
        self._revision_agent = revision_agent or RevisionAgent()

    async def handle(self, state: RuntimeState) -> StageResult:
        if not state.get("itinerary_draft"):
            return StageResult(
                stage=self.stage_name,
                status="failed",
                summary="verify requires itinerary_draft",
                data={
                    "error": {
                        "type": "missing_itinerary_draft",
                        "message": "verify requires itinerary_draft",
                    },
                },
            )

        updated_state = RuntimeState(**state)
        report = self._verifier.verify(updated_state)

        if (
            report.has_blocking_issues
            and int(updated_state.get("revision_count") or 0) < MAX_AUTO_REVISION
        ):
            revised_draft = self._revision_agent.revise(updated_state, report)
            updated_state = increment_revision_count(
                set_itinerary_draft(updated_state, revised_draft.to_runtime_dict()),
            )
            report = self._verifier.verify(updated_state)
            report = QualityReport(
                **{
                    **report.to_runtime_dict(),
                    "revision_applied": True,
                },
            )

        if report.has_blocking_issues or report.unsupported_claims:
            report = QualityReport(
                **{
                    **report.to_runtime_dict(),
                    "suggested_action": "surface_to_user",
                    "is_acceptable": False,
                },
            )

        report_dict = report.to_runtime_dict()
        updated_state = set_quality_report(updated_state, report_dict)

        summary = (
            "quality verification completed"
            if report.is_acceptable
            else "quality verification completed with issues requiring user attention"
        )
        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary=summary,
            data={
                "quality_report": report_dict,
                "state": updated_state,
            },
        )
