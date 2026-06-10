"""Base contracts and registry for PlanningRuntime stage handlers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Literal, Protocol, TypedDict

from app.runtime.state import RuntimeState


class StageResult(TypedDict):
    stage: str
    status: Literal["completed", "waiting", "failed"]
    summary: str
    data: dict[str, Any]


class StageHandler(Protocol):
    stage_name: str

    async def handle(self, state: RuntimeState) -> StageResult:
        ...


class SkeletonStageHandler:
    stage_name: str
    summary: str

    async def handle(self, state: RuntimeState) -> StageResult:
        """Return the minimal structured result without invoking business logic."""
        return StageResult(
            stage=self.stage_name,
            status="completed",
            summary=self.summary,
            data={},
        )


def build_production_stage_handlers() -> Sequence[StageHandler]:
    """Build V1 handlers wired for the default chat path."""
    from app.runtime.finalization.persistence import ServiceItineraryPersistenceAdapter
    from app.runtime.stages.approve_or_revise import ApproveOrReviseStageHandler
    from app.runtime.stages.collect import CollectStageHandler
    from app.runtime.stages.domain_plan import DomainPlanStageHandler
    from app.runtime.stages.finalize import FinalizeStageHandler
    from app.runtime.stages.integrate import IntegrateStageHandler
    from app.runtime.stages.prepare_base_context import PrepareBaseContextStageHandler
    from app.runtime.stages.retrieve_evidence import RetrieveEvidenceStageHandler
    from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
    from app.runtime.stages.verify import VerifyStageHandler

    return (
        CollectStageHandler(),
        PrepareBaseContextStageHandler(),
        RetrieveEvidenceStageHandler(),
        ToolEnrichStageHandler(),
        DomainPlanStageHandler(),
        IntegrateStageHandler(),
        VerifyStageHandler(),
        ApproveOrReviseStageHandler(),
        FinalizeStageHandler(persistence=ServiceItineraryPersistenceAdapter()),
    )


def build_default_stage_handlers() -> Sequence[StageHandler]:
    """Build the frozen V1 stage handler sequence."""
    from app.runtime.stages.approve_or_revise import ApproveOrReviseStageHandler
    from app.runtime.stages.collect import CollectStageHandler
    from app.runtime.stages.domain_plan import DomainPlanStageHandler
    from app.runtime.stages.finalize import FinalizeStageHandler
    from app.runtime.stages.integrate import IntegrateStageHandler
    from app.runtime.stages.prepare_base_context import PrepareBaseContextStageHandler
    from app.runtime.stages.retrieve_evidence import RetrieveEvidenceStageHandler
    from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
    from app.runtime.stages.verify import VerifyStageHandler

    return (
        CollectStageHandler(),
        PrepareBaseContextStageHandler(),
        RetrieveEvidenceStageHandler(),
        ToolEnrichStageHandler(),
        DomainPlanStageHandler(),
        IntegrateStageHandler(),
        VerifyStageHandler(),
        ApproveOrReviseStageHandler(),
        FinalizeStageHandler(),
    )
