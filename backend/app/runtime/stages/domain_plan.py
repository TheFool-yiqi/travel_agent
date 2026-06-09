"""Domain-plan stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "domain_plan"


class DomainPlanStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "domain planning skeleton completed"
