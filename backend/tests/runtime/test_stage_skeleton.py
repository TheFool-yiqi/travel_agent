import pytest

from app.runtime.manifest import V1_STAGE_NAMES
from app.runtime.stages.base import build_default_stage_handlers
from app.runtime.stages.collect import CollectStageHandler
from app.runtime.stages.prepare_base_context import PrepareBaseContextStageHandler
from app.runtime.stages.retrieve_evidence import RetrieveEvidenceStageHandler
from app.runtime.stages.tool_enrich import ToolEnrichStageHandler
from app.runtime.state import create_initial_runtime_state


@pytest.mark.asyncio
async def test_all_stage_handlers_return_matching_stage_names() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    handlers = build_default_stage_handlers()

    assert tuple(handler.stage_name for handler in handlers) == V1_STAGE_NAMES

    for handler in handlers:
        result = await handler.handle(state)
        assert result["stage"] == handler.stage_name
        if isinstance(handler, CollectStageHandler):
            assert result["status"] == "waiting"
        elif isinstance(handler, PrepareBaseContextStageHandler):
            assert result["status"] == "failed"
        elif isinstance(handler, RetrieveEvidenceStageHandler):
            assert result["status"] == "failed"
        elif isinstance(handler, ToolEnrichStageHandler):
            assert result["status"] == "failed"
        else:
            assert result["status"] == "completed"
        assert result["summary"]


@pytest.mark.asyncio
async def test_stage_handlers_do_not_mutate_input_runtime_state() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    original = dict(state)

    for handler in build_default_stage_handlers():
        await handler.handle(state)

    assert state == original
