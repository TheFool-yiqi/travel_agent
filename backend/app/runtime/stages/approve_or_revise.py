"""Approve-or-revise stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "approve_or_revise"


class ApproveOrReviseStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "approval skeleton completed"
