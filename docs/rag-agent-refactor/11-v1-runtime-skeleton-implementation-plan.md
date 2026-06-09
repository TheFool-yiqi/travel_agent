# V1 Runtime Skeleton Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers only Slice 1 and Slice 2 from
> [10-v1-implementation-roadmap.md](10-v1-implementation-roadmap.md).

**Goal:** 建立 PlanningRuntime 的最小可运行骨架，让 9 个 stage 能被 LangGraph executor
顺序推动，并能输出可复用的 RuntimeEvent / token 合流接口。

**Architecture:** V1 Skeleton 先搭运行时承载面，不迁移真实 collect、EvidenceEngine、
ToolService、多 Agent 或 finalize 业务。LangGraph 只负责执行、checkpoint 和事件桥接；
业务阶段由 `backend/app/runtime/stages/` 的 StageHandler 承载。

**Tech Stack:** Python, FastAPI project layout, LangGraph, pytest, Pydantic or dataclass typed
schemas, existing `backend/app/services/chat_stream.py` streaming pattern.

---

## 1. Scope

本文只冻结并实现 Slice 1 / Slice 2。

```text
Slice 1: RuntimeState + RuntimeEvent + 9 stage skeleton
Slice 2: LangGraph executor adapter + event stream adapter
```

### In Scope

```text
backend/app/runtime/ package
RuntimeState / RuntimeSnapshot / StageStatus
RuntimeEvent / TokenEvent / RuntimeCompletedEvent / ApprovalRequiredEvent
Runtime manifest with exactly 9 V1 stages
StageHandler protocol
9 minimal stage handler files
PlanningRuntime sequential dispatcher
LangGraph executor adapter skeleton
RuntimeEvent + public token multiplex helper
backend/tests/runtime/ basic tests
```

### Out Of Scope

```text
real collect migration
ContextAssembler
EvidenceEngine
ToolService / WeatherTool
DomainPlannerGroup
Skill package implementation
Prompt migration
QualityVerifier
RevisionAgent
real approval interrupt
real order_id / itinerary persistence
frontend event switch
DB migrations
LangSmith integration
```

这些留给后续 Slice。此阶段可以为它们预留 typed fields，但不创建空目录。

## 2. Directory Freeze For Slice 1/2

### Create Now

```text
backend/app/runtime/
  __init__.py
  state.py
  events.py
  manifest.py
  planning_runtime.py

backend/app/runtime/stages/
  __init__.py
  base.py
  collect.py
  prepare_base_context.py
  retrieve_evidence.py
  tool_enrich.py
  domain_plan.py
  integrate.py
  verify.py
  approve_or_revise.py
  finalize.py

backend/app/runtime/executor/
  __init__.py
  graph_builder.py
  langgraph_executor.py

backend/app/services/
  runtime_chat_stream.py

backend/tests/runtime/
  test_runtime_state.py
  test_runtime_events.py
  test_stage_skeleton.py
  test_planning_runtime.py
  test_runtime_graph_builder.py
  test_runtime_chat_stream.py

docs/rag-agent-refactor/
  runtime-framework-inventory.md
```

### Do Not Create Yet

```text
backend/app/runtime/context/
backend/app/runtime/memory/
backend/app/runtime/semantic/
backend/app/runtime/agents/
backend/app/runtime/skills/
backend/app/runtime/tools/
backend/app/runtime/quality/
backend/app/runtime/finalization/
backend/app/runtime/observability/
backend/app/ai/prompts/runtime/
```

Reason: these directories should appear when their first real implementation slice starts, not as empty
architecture theater.

## 3. Runtime Contract

### V1 Stage Names

The manifest must define exactly these stage names and order:

```text
collect
prepare_base_context
retrieve_evidence
tool_enrich
domain_plan
integrate
verify
approve_or_revise
finalize
```

No old graph node names may appear in the Runtime manifest:

```text
collect_requirements
plan_destination
plan_transport
plan_stay_and_food
plan_activities
build_itinerary
approval_node
final_response
```

### RuntimeState Minimal Shape

RuntimeState should be serializable and small.

```python
class RuntimeState(TypedDict, total=False):
    run_id: str
    conversation_id: str
    user_id: str | None
    input_message: str
    current_stage: str
    completed_stages: list[str]
    stage_outputs: dict[str, dict[str, Any]]
    pending_approval: dict[str, Any] | None
    public_messages: list[dict[str, Any]]
    private_notes: list[dict[str, Any]]
    errors: list[dict[str, Any]]
```

Rules:

```text
RuntimeState stores structured facts and stage outputs.
RuntimeState does not store assembled prompt text.
RuntimeState does not replace TravelState globally.
RuntimeState may be wrapped by LangGraph checkpoint, but remains Runtime-owned.
```

### RuntimeEvent Minimal Shape

```python
class RuntimeEvent(BaseModel):
    event_id: str
    run_id: str
    stage: str | None
    type: str
    visibility: Literal["public", "internal", "external_trace"]
    payload: dict[str, Any]
```

Required event types:

```text
stage_started
stage_completed
token_delta
approval_required
runtime_completed
runtime_failed
```

V1 skeleton should emit:

```text
stage_started / stage_completed for every stage
runtime_completed after finalize
runtime_failed if dispatcher catches an exception
```

## 4. Task Plan

### Task 1: Create Runtime Package Skeleton

**Files:**

```text
Create: backend/app/runtime/__init__.py
Create: backend/app/runtime/stages/__init__.py
Create: backend/app/runtime/executor/__init__.py
Create: backend/tests/runtime/__init__.py
```

**Implementation notes:**

```text
__init__.py files should be minimal.
Do not export large convenience surfaces yet.
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime -q
```

Expected after Task 1: no runtime tests exist or collection succeeds once tests are added in later tasks.

### Task 2: Define Runtime Manifest

**Files:**

```text
Create: backend/app/runtime/manifest.py
Test: backend/tests/runtime/test_runtime_state.py
```

**Required behavior:**

```text
V1_STAGE_NAMES contains exactly 9 names.
Stage order matches 09 and 10.
is_valid_stage(name) returns true only for V1 stage names.
```

**Suggested implementation surface:**

```python
V1_STAGE_NAMES: tuple[str, ...] = (
    "collect",
    "prepare_base_context",
    "retrieve_evidence",
    "tool_enrich",
    "domain_plan",
    "integrate",
    "verify",
    "approve_or_revise",
    "finalize",
)

def is_valid_stage(stage: str) -> bool:
    return stage in V1_STAGE_NAMES
```

**Required tests:**

```python
def test_v1_stage_names_are_frozen() -> None:
    assert V1_STAGE_NAMES == (
        "collect",
        "prepare_base_context",
        "retrieve_evidence",
        "tool_enrich",
        "domain_plan",
        "integrate",
        "verify",
        "approve_or_revise",
        "finalize",
    )


def test_old_graph_names_are_not_runtime_stages() -> None:
    for old_name in {
        "collect_requirements",
        "plan_destination",
        "plan_transport",
        "plan_stay_and_food",
        "plan_activities",
        "build_itinerary",
        "approval_node",
        "final_response",
    }:
        assert not is_valid_stage(old_name)
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_state.py -q
```

Expected: pass.

### Task 3: Define RuntimeState Helpers

**Files:**

```text
Create: backend/app/runtime/state.py
Modify: backend/tests/runtime/test_runtime_state.py
```

**Required behavior:**

```text
create_initial_runtime_state creates a minimal RuntimeState.
mark_stage_started updates current_stage.
record_stage_output appends completed stage and stores output.
record_runtime_error appends structured error.
```

**Suggested implementation surface:**

```python
def create_initial_runtime_state(
    *,
    run_id: str,
    conversation_id: str,
    input_message: str,
    user_id: str | None = None,
) -> RuntimeState:
    ...

def mark_stage_started(state: RuntimeState, stage: str) -> RuntimeState:
    ...

def record_stage_output(
    state: RuntimeState,
    *,
    stage: str,
    output: dict[str, Any],
) -> RuntimeState:
    ...
```

Implementation rule:

```text
Return a new dict or clearly controlled shallow copy.
Do not mutate nested values in surprising ways.
Validate stage names through manifest.py.
```

**Required tests:**

```python
def test_create_initial_runtime_state_has_no_prompt_context() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        user_id="user_1",
        input_message="成都三天低强度",
    )

    assert state["run_id"] == "run_1"
    assert state["current_stage"] == "collect"
    assert state["completed_stages"] == []
    assert state["stage_outputs"] == {}
    assert "prompt" not in state
    assert "assembled_context" not in state


def test_record_stage_output_tracks_completion() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    updated = record_stage_output(
        state,
        stage="collect",
        output={"status": "completed"},
    )

    assert updated["completed_stages"] == ["collect"]
    assert updated["stage_outputs"]["collect"] == {"status": "completed"}
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_state.py -q
```

Expected: pass.

### Task 4: Define RuntimeEvent Schemas

**Files:**

```text
Create: backend/app/runtime/events.py
Create: backend/tests/runtime/test_runtime_events.py
```

**Required behavior:**

```text
make_stage_started_event returns public stage_started event.
make_stage_completed_event returns public stage_completed event.
make_runtime_completed_event returns public runtime_completed event.
make_runtime_failed_event returns public or internal runtime_failed event.
RuntimeEvent can be converted to existing transport dict.
```

**Suggested implementation surface:**

```python
def make_stage_started_event(*, run_id: str, stage: str) -> RuntimeEvent:
    ...

def make_stage_completed_event(
    *,
    run_id: str,
    stage: str,
    output: dict[str, Any] | None = None,
) -> RuntimeEvent:
    ...

def make_runtime_completed_event(*, run_id: str) -> RuntimeEvent:
    ...

def runtime_event_to_transport(event: RuntimeEvent) -> dict[str, Any]:
    ...
```

Transport dict should be stable:

```json
{
  "type": "runtime_event",
  "event_type": "stage_started",
  "stage": "collect",
  "visibility": "public",
  "payload": {}
}
```

**Required tests:**

```python
def test_stage_started_event_transport_shape() -> None:
    event = make_stage_started_event(run_id="run_1", stage="collect")
    payload = runtime_event_to_transport(event)

    assert payload["type"] == "runtime_event"
    assert payload["event_type"] == "stage_started"
    assert payload["stage"] == "collect"
    assert payload["visibility"] == "public"


def test_runtime_completed_event_has_no_stage() -> None:
    event = make_runtime_completed_event(run_id="run_1")

    assert event.type == "runtime_completed"
    assert event.stage is None
    assert event.visibility == "public"
```

`done / error` are transport compatibility event names and must not be used as internal
`RuntimeEvent.type` values.

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_events.py -q
```

Expected: pass.

### Task 5: Implement StageHandler Base And 9 Minimal Stages

**Files:**

```text
Create: backend/app/runtime/stages/base.py
Create: backend/app/runtime/stages/collect.py
Create: backend/app/runtime/stages/prepare_base_context.py
Create: backend/app/runtime/stages/retrieve_evidence.py
Create: backend/app/runtime/stages/tool_enrich.py
Create: backend/app/runtime/stages/domain_plan.py
Create: backend/app/runtime/stages/integrate.py
Create: backend/app/runtime/stages/verify.py
Create: backend/app/runtime/stages/approve_or_revise.py
Create: backend/app/runtime/stages/finalize.py
Create: backend/tests/runtime/test_stage_skeleton.py
```

**Required behavior:**

```text
Each stage exposes STAGE_NAME.
Each stage has async handle(state) -> StageResult.
Each minimal StageResult includes status, stage, and summary.
No stage calls LLM, DB, MCP, HTTP, or old graph nodes in Slice 1/2.
```

**Suggested implementation surface:**

```python
class StageResult(TypedDict, total=False):
    stage: str
    status: Literal["completed", "waiting", "failed"]
    summary: str
    data: dict[str, Any]


class StageHandler(Protocol):
    stage_name: str

    async def handle(self, state: RuntimeState) -> StageResult:
        ...
```

Minimal stage summary examples:

```text
collect -> "collect skeleton completed"
prepare_base_context -> "base context skeleton completed"
retrieve_evidence -> "evidence retrieval skeleton completed"
tool_enrich -> "tool enrichment skeleton completed"
domain_plan -> "domain planning skeleton completed"
integrate -> "integration skeleton completed"
verify -> "verification skeleton completed"
approve_or_revise -> "approval skeleton completed"
finalize -> "finalization skeleton completed"
```

**Required tests:**

```python
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
        assert result["status"] == "completed"
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_stage_skeleton.py -q
```

Expected: pass.

### Task 6: Implement PlanningRuntime Sequential Dispatcher

**Files:**

```text
Create: backend/app/runtime/planning_runtime.py
Create: backend/tests/runtime/test_planning_runtime.py
```

**Required behavior:**

```text
PlanningRuntime accepts a list of StageHandler.
run(initial_state) executes handlers in manifest order.
run emits stage_started and stage_completed events.
run records stage outputs into RuntimeState.
run emits runtime_completed after finalize.
If a handler raises, run emits runtime_failed and stops.
```

**Suggested implementation surface:**

```python
class PlanningRuntime:
    def __init__(self, handlers: Sequence[StageHandler]) -> None:
        ...

    async def run(
        self,
        state: RuntimeState,
    ) -> AsyncIterator[RuntimeEvent]:
        ...
```

Runtime should keep internal state update deterministic:

```text
stage_started event
handler.handle
record_stage_output
stage_completed event
next stage
runtime_completed event
```

**Required tests:**

```python
@pytest.mark.asyncio
async def test_runtime_emits_9_stage_pairs_and_done() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )
    runtime = PlanningRuntime(build_default_stage_handlers())

    events = [event async for event in runtime.run(state)]

    stage_started = [e.stage for e in events if e.type == "stage_started"]
    stage_completed = [e.stage for e in events if e.type == "stage_completed"]

    assert tuple(stage_started) == V1_STAGE_NAMES
    assert tuple(stage_completed) == V1_STAGE_NAMES
    assert events[-1].type == "runtime_completed"
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_planning_runtime.py -q
```

Expected: pass.

### Task 7: Implement LangGraph Runtime Graph Builder

**Files:**

```text
Create: backend/app/runtime/executor/graph_builder.py
Create: backend/tests/runtime/test_runtime_graph_builder.py
```

**Required behavior:**

```text
Build a StateGraph over RuntimeState.
Graph contains exactly 9 stage nodes.
Edges follow V1 manifest order.
START routes to collect.
finalize routes to END.
This graph is separate from backend/app/graph/builder.py.
```

**Suggested implementation surface:**

```python
def build_runtime_graph(*, checkpointer: BaseCheckpointSaver | None = None):
    ...
```

For Slice 1/2, stage nodes may call the same minimal stage handlers used by PlanningRuntime.

**Required tests:**

```python
def test_runtime_graph_builder_uses_v1_stage_names() -> None:
    graph = build_runtime_graph(checkpointer=None)

    assert graph is not None
```

If LangGraph internals make node introspection brittle, test through execution instead:

```python
@pytest.mark.asyncio
async def test_runtime_graph_executes_happy_path_without_checkpointer() -> None:
    graph = build_runtime_graph(checkpointer=None)
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        input_message="成都三天低强度",
    )

    result = await graph.ainvoke(state)

    assert result["completed_stages"] == list(V1_STAGE_NAMES)
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_graph_builder.py -q
```

Expected: pass.

### Task 8: Implement LangGraph Executor Adapter

**Files:**

```text
Create: backend/app/runtime/executor/langgraph_executor.py
Modify: backend/tests/runtime/test_runtime_graph_builder.py
```

**Required behavior:**

```text
RuntimeLangGraphExecutor exposes stream(initial_state).
stream yields RuntimeEvent objects, not raw LangGraph internals.
Executor does not replace existing build_travel_graph.
Executor accepts optional checkpointer for future integration.
```

**Suggested implementation surface:**

```python
class RuntimeLangGraphExecutor:
    def __init__(self, *, checkpointer: BaseCheckpointSaver | None = None) -> None:
        ...

    async def stream(self, state: RuntimeState) -> AsyncIterator[RuntimeEvent]:
        ...
```

Slice 1/2 acceptable implementation:

```text
Use PlanningRuntime directly for RuntimeEvent stream.
Keep LangGraph graph_builder available and tested.
Wire raw LangGraph event conversion in a later transport slice if needed.
```

Reason: we want the RuntimeEvent contract stable before exposing raw graph event complexity.

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_graph_builder.py backend/tests/runtime/test_planning_runtime.py -q
```

Expected: pass.

### Task 9: Implement Runtime Stream Multiplexer

**Files:**

```text
Create: backend/app/services/runtime_chat_stream.py
Create: backend/tests/runtime/test_runtime_chat_stream.py
```

**Required behavior:**

```text
_iter_runtime_events_and_tokens multiplexes RuntimeEvent stream and token queue.
It mirrors the existing _iter_graph_events_and_tokens behavior.
Token events are yielded while Runtime events are still running.
When Runtime stream finishes, remaining tokens are drained.
```

**Suggested implementation surface:**

```python
async def _iter_runtime_events_and_tokens(
    runtime_events: AsyncIterator[RuntimeEvent],
    token_queue: asyncio.Queue[str],
) -> AsyncIterator[tuple[str, Any]]:
    ...
```

Output tuples:

```text
("event", RuntimeEvent)
("token", str)
```

Do not modify the existing `_iter_graph_events_and_tokens` in this task. Keep old streaming tests intact.

**Required tests:**

```python
@pytest.mark.asyncio
async def test_iter_runtime_events_and_tokens_drains_tokens() -> None:
    async def events() -> AsyncIterator[RuntimeEvent]:
        yield make_stage_started_event(run_id="run_1", stage="collect")
        yield make_runtime_completed_event(run_id="run_1")

    token_queue: asyncio.Queue[str] = asyncio.Queue()
    await token_queue.put("hello")

    items = [
        item async for item in _iter_runtime_events_and_tokens(events(), token_queue)
    ]

    assert ("token", "hello") in items
    assert any(
        kind == "event" and value.type == "runtime_completed"
        for kind, value in items
    )
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_chat_stream.py backend/tests/test_chat_stream.py -q
```

Expected: new runtime stream tests pass and old chat stream tests remain passing.

### Task 10: Add Runtime Skeleton Smoke Test

**Files:**

```text
Create: backend/tests/runtime/test_runtime_skeleton_smoke.py
```

**Required behavior:**

```text
One test proves the new skeleton can run end-to-end without DB, LLM, MCP, HTTP, or frontend.
```

**Required test:**

```python
@pytest.mark.asyncio
async def test_runtime_skeleton_happy_path() -> None:
    state = create_initial_runtime_state(
        run_id="run_1",
        conversation_id="conv_1",
        user_id="user_1",
        input_message="成都三天低强度，喜欢美食",
    )
    executor = RuntimeLangGraphExecutor(checkpointer=None)

    events = [event async for event in executor.stream(state)]

    assert [e.stage for e in events if e.type == "stage_started"] == list(V1_STAGE_NAMES)
    assert [e.stage for e in events if e.type == "stage_completed"] == list(V1_STAGE_NAMES)
    assert events[-1].type == "runtime_completed"
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime -q
```

Expected: all runtime skeleton tests pass.

### Task 11: Record Runtime Framework Inventory

**Files:**

```text
Create: docs/rag-agent-refactor/runtime-framework-inventory.md
```

**Goal:**

在 Slice 1/2 实现和验证完成后，记录新框架实际包含的目录、文件、职责和迁移状态，为后续
识别并删除冗余文件提供事实依据。

**Required inventory sections:**

```text
New Runtime Files
Reused Existing Files
Compatibility-Only Old Flow Files
Future Slice Files Not Created Yet
Candidate Redundant Files
Deletion Gate
```

**Required record fields:**

```text
path
owner / responsibility
introduced_or_reused_by_slice
runtime_status: active / compatibility / reserved / candidate_redundant
replacement_path
deletion_prerequisites
last_verified_date
```

**Inventory rules:**

```text
Only record files and directories that actually exist.
Do not mark a file redundant only because a new similarly named file exists.
Candidate redundant files must include their replacement and deletion prerequisites.
Do not delete files while performing this inventory task.
Future Slice plans must update this inventory after their implementation completes.
```

**Example entry:**

```markdown
| Path | Responsibility | Slice | Status | Replacement | Deletion prerequisites |
|------|----------------|-------|--------|-------------|------------------------|
| `backend/app/runtime/state.py` | Runtime-owned structured execution state | Slice 1 | active | — | — |
| `backend/app/graph/state.py` | Old graph `TravelState` | Existing | compatibility | `backend/app/runtime/state.py` for new flow | New Runtime is default path and old graph regression coverage is retired |
```

**Verification:**

```powershell
Test-Path docs/rag-agent-refactor/runtime-framework-inventory.md
rg -n "New Runtime Files|Reused Existing Files|Compatibility-Only Old Flow Files|Future Slice Files Not Created Yet|Candidate Redundant Files|Deletion Gate" docs/rag-agent-refactor/runtime-framework-inventory.md
```

Expected:

```text
inventory file exists
all required sections exist
every candidate redundant file has replacement and deletion prerequisites
no files are deleted by this task
```

## 5. Integration Rules

### Existing Graph

Do not modify:

```text
backend/app/graph/builder.py
backend/app/graph/state.py
backend/app/graph/routers/
```

During Slice 1/2, the new Runtime graph is parallel. It must not become the default chat path yet.

### Existing Stream

Do not replace:

```text
backend/app/services/chat_stream.py
backend/app/ws/chat_stream.py
```

Only add:

```text
backend/app/services/runtime_chat_stream.py
```

The switch from old chat stream to Runtime stream belongs to a later frontend / transport slice.

### Existing Tests

Keep these passing:

```text
backend/tests/test_chat_stream.py
backend/tests/test_checkpoint.py
backend/tests/test_approval_router.py
```

If they fail after Slice 1/2, the implementation leaked into old flow and should be corrected.

## 6. Verification Commands

Run narrow tests after each task:

```powershell
uv run pytest backend/tests/runtime/test_runtime_state.py -q
uv run pytest backend/tests/runtime/test_runtime_events.py -q
uv run pytest backend/tests/runtime/test_stage_skeleton.py -q
uv run pytest backend/tests/runtime/test_planning_runtime.py -q
uv run pytest backend/tests/runtime/test_runtime_graph_builder.py -q
uv run pytest backend/tests/runtime/test_runtime_chat_stream.py -q
```

Run final Slice 1/2 verification:

```powershell
uv run pytest backend/tests/runtime backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py -q
```

Expected:

```text
all runtime skeleton tests pass
existing chat stream multiplex tests pass
existing checkpoint tests pass
existing approval router tests pass
```

## 7. Completion Criteria

Slice 1/2 is complete when:

```text
backend/app/runtime/ exists with core, stages, executor files
V1 manifest has exactly 9 stage names
RuntimeState can be initialized and updated
RuntimeEvent transport shape is stable
PlanningRuntime emits stage_started / stage_completed / runtime_completed
Runtime graph can execute happy path without checkpointer
Runtime stream multiplexer works without changing old stream
runtime skeleton tests pass
old chat/checkpoint/approval tests still pass
runtime-framework-inventory.md records the actual Slice 1/2 file layout and migration status
README and roadmap docs point to this plan
```

After this, the next implementation plan is
[12-v1-collect-context-implementation-plan.md](12-v1-collect-context-implementation-plan.md).
