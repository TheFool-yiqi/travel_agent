"""Integrate stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "integrate"


class IntegrateStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "integration skeleton completed"
