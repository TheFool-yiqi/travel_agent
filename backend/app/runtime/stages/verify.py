"""Verify stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "verify"


class VerifyStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "verification skeleton completed"
