"""Finalize stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "finalize"


class FinalizeStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "finalization skeleton completed"
