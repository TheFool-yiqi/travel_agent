# V1 Collect And Context Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Slice 3 from
> [10-v1-implementation-roadmap.md](10-v1-implementation-roadmap.md).

**Goal:** 将现有多轮 collect 体验迁移到 PlanningRuntime 的 `collect` 与
`prepare_base_context` 阶段，建立 `CollectContext → PlanningNeed → BaseContext →
ContextAssembler` 边界，且不降低 greeting、语义规则、pending clarification 和确认摘要体验。

**Architecture:** `CollectStageHandler` 是 stage facade，内部调用 `CollectRuntime.process_turn()`。
语义规则与 LLM 抽取分层执行；只有经 `PlanningInputValidator` 和用户确认（或显式“先出一版”）
后的 `PlanningNeed` 才能进入 `prepare_base_context`。正式规划 Agent 通过 `ContextAssembler`
获取视图，不得读取 raw `CollectContext`。

**Tech Stack:** Python, Pydantic schemas, pytest-asyncio, 复用现有
`backend/app/graph/semantic/`、`greeting.py`、`collect_requirements.py` 行为参考。

**Prerequisites:** Slice 1/2 已完成（`backend/app/runtime/` 骨架、RuntimeEvent、LangGraph adapter、
runtime stream multiplexer、runtime tests 全绿）。

---

## 1. Scope

本文只冻结并实现 Slice 3。

```text
Slice 3: intelligent collect migration + PlanningNeed boundary + ContextAssembler
```

### In Scope

```text
RuntimeState 扩展 collect_context / planning_need / base_context 结构化字段
CollectContext / PlanningNeed / BaseContext Pydantic schemas
CollectSemanticLayer（迁移 graph/semantic 核心规则）
GreetingPolicy / GreetingResponder
CollectRuntime.process_turn()
HybridReadinessEvaluator
PlanningInputCompiler / PlanningInputValidator
真实 CollectStageHandler（替换 skeleton）
真实 PrepareBaseContextStageHandler（最小 BaseContext 生成）
ContextSpec registry
ContextAssembler（按 Agent/Stage 过滤可见上下文）
backend/tests/runtime/ collect + context 测试
更新 runtime-framework-inventory.md
```

### Out Of Scope

```text
EvidenceEngine / retrieve_evidence 真实实现
ToolService / WeatherTool
DomainPlannerGroup / Integrator / Judge
Skill package 目录与 runner 文件
Prompt 迁移到 backend/app/ai/prompts/runtime/
DiscoveryProfile 离线投影器（backend/app/runtime/discovery/ 仅预留接口或最小 stub）
Runtime 成为默认 chat 路径
DB migrations
frontend event switch
LangSmith integration
```

Slice 3 完成后，`collect` 与 `prepare_base_context` 应能在 PlanningRuntime 内独立验收；
后续 stage 仍可使用 skeleton 行为直至对应 Slice 落地。

## 2. Directory Freeze For Slice 3

### Create Now

```text
backend/app/runtime/collect/
  __init__.py
  schemas.py
  runtime.py
  readiness.py
  planning_input.py
  greeting.py
  conversation_policy.py

backend/app/runtime/context/
  __init__.py
  schemas.py
  specs.py
  assembler.py

backend/app/runtime/semantic/
  __init__.py
  normalizer.py
  slot_binding.py
  collection_frame.py

backend/tests/runtime/
  test_collect_context.py
  test_planning_input.py
  test_context_assembler.py
  test_collect_stage.py
  test_prepare_base_context_stage.py
```

### Reuse, Do Not Duplicate Yet

```text
backend/app/graph/semantic/semantic_pipeline.py   -> 行为参考，逐步迁入 CollectSemanticLayer
backend/app/graph/greeting.py                      -> GreetingPolicy 复用逻辑来源
backend/app/graph/nodes/collect_requirements.py    -> 多轮策略与 merge 行为参考
backend/app/graph/validators/requirements.py       -> PlanningInputValidator 规则来源
backend/app/schemas/travel.py                      -> TripSpec / UserRequirement 字段对齐
```

### Do Not Create Yet

```text
backend/app/runtime/discovery/catalog.py           -> Slice 4 前仅允许 typed stub
backend/app/runtime/memory/
backend/app/runtime/agents/
backend/app/runtime/skills/
backend/app/ai/prompts/runtime/
```

## 3. Runtime Contract Extensions

### RuntimeState Additions

在 `backend/app/runtime/state.py` 增加结构化字段（不得存 assembled prompt）：

```python
class RuntimeState(TypedDict, total=False):
    # ... existing Slice 1/2 fields ...
    collect_context: dict[str, Any] | None
    planning_need: dict[str, Any] | None
    base_context: dict[str, Any] | None
    awaiting_user: bool
    collect_turn_count: int
```

Rules:

```text
collect_context 只在 collect 阶段完整读写
planning_need 只在 collect 退出且校验通过后写入
base_context 只在 prepare_base_context 完成后写入
awaiting_user=True 时 PlanningRuntime 应停止后续 stage（V1 顺序 dispatcher 在 collect 返回 waiting）
RuntimeState 不得包含 prompt / assembled_context / full dialogue transcript
```

### CollectContext Minimal Shape

```python
class CollectContext(BaseModel):
    trip_spec: dict[str, Any]
    conversation_state: dict[str, Any]
    discovery_state: dict[str, Any]
    readiness_state: dict[str, Any]
    pending_clarification: dict[str, Any] | None
    rejected_assumptions: list[dict[str, Any]]
```

### PlanningNeed Minimal Shape

```python
class PlanningNeed(BaseModel):
    confirmed_facts: list[dict[str, Any]]
    derived_facts: list[dict[str, Any]]
    approved_assumptions: list[dict[str, Any]]
    constraints: list[dict[str, Any]]
    preferences: list[dict[str, Any]]
    missing_but_accepted_fields: list[str]
    risk_flags: list[str]
```

每条 fact 必须带轻量 provenance：

```text
fact_type: confirmed | derived | approved_assumption
source: user | rule | discovery_confirmed | explicit_draft_request
```

### BaseContext Minimal Shape

```python
class BaseContext(BaseModel):
    planning_need_summary: dict[str, Any]
    session_facts: list[dict[str, Any]]
    memory_snippets: list[dict[str, Any]]
    decision_snippets: list[dict[str, Any]]
```

### ContextSpec Rules

```text
destination_planner:
  may read: PlanningNeed, BaseContext.planning_need_summary, BaseContext.preferences
  must not read: CollectContext, raw messages, tool raw responses

formal planning agents (V1 placeholder spec for Slice 6):
  may read: PlanningNeed, BaseContext, future EvidenceContext, future ToolContext
  must not read: CollectContext
```

## 4. Task Plan

### Task 1: Extend RuntimeState And Helpers

**Files:**

```text
Modify: backend/app/runtime/state.py
Modify: backend/tests/runtime/test_runtime_state.py
```

**Required behavior:**

```text
create_initial_runtime_state initializes collect_context=None, planning_need=None, base_context=None
set_collect_context / set_planning_need / set_base_context helpers return new state copies
record_collect_waiting sets awaiting_user=True and stops stage chain semantics for tests
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_state.py -q
```

### Task 2: Define Collect And Context Schemas

**Files:**

```text
Create: backend/app/runtime/collect/schemas.py
Create: backend/app/runtime/context/schemas.py
Create: backend/tests/runtime/test_collect_context.py
```

**Required behavior:**

```text
CollectContext, PlanningNeed, BaseContext pydantic models with validation
PlanningNeed rejects entries without fact_type / source
serialize/deserialize round-trip for RuntimeState storage
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_collect_context.py -q
```

### Task 3: Migrate CollectSemanticLayer

**Files:**

```text
Create: backend/app/runtime/semantic/normalizer.py
Create: backend/app/runtime/semantic/slot_binding.py
Create: backend/app/runtime/semantic/collection_frame.py
Create: backend/app/runtime/semantic/__init__.py
```

**Required behavior:**

```text
Wrap or re-export existing graph/semantic behavior without changing old graph imports
normalize_text, bind slots, build/apply semantic frame available to CollectRuntime
semantic rules run before LLM extraction in CollectRuntime.process_turn
```

**Reuse map (from 09 blueprint):**

| Existing | New |
|----------|-----|
| `graph/semantic/normalizer.py` | `runtime/semantic/normalizer.py` |
| slot binding in semantic_pipeline | `runtime/semantic/slot_binding.py` |
| semantic frame lifecycle | `runtime/semantic/collection_frame.py` |

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_collect_context.py backend/tests/test_nl_extract_selection.py -q
```

### Task 4: Implement GreetingPolicy And GreetingResponder

**Files:**

```text
Create: backend/app/runtime/collect/greeting.py
Modify: backend/tests/runtime/test_collect_stage.py
```

**Required behavior:**

```text
greeting-only first turn with no prior assistant message -> public greeting, awaiting_user=True
does not write PlanningNeed
does not advance to prepare_base_context
reuses build_greeting_reply / is_greeting_only logic from graph/greeting.py
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_collect_stage.py -k greeting -q
```

### Task 5: Implement HybridReadinessEvaluator

**Files:**

```text
Create: backend/app/runtime/collect/readiness.py
Modify: backend/tests/runtime/test_collect_stage.py
```

**Required behavior:**

```text
mirrors can_advance_to_planning / is_requirement_complete semantics from collect_requirements
returns readiness_status: continue_collect | ready_for_confirmation | ready_for_planning
vague confirmation does not mark missing slots as confirmed
unconfirmed DiscoveryHypothesis does not enter PlanningNeed
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_collect_stage.py -k readiness -q
```

### Task 6: Implement PlanningInputCompiler And Validator

**Files:**

```text
Create: backend/app/runtime/collect/planning_input.py
Create: backend/tests/runtime/test_planning_input.py
```

**Required behavior:**

```text
PlanningInputCompiler only compiles confirmed / derived / approved_assumption facts
PlanningInputValidator rejects invented destinations, dates, party sizes
explicit draft request recorded in risk_flags / approved_assumptions with provenance
does not pass raw CollectContext to output
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_planning_input.py -q
```

### Task 7: Implement CollectRuntime.process_turn

**Files:**

```text
Create: backend/app/runtime/collect/runtime.py
Create: backend/app/runtime/collect/conversation_policy.py
Create: backend/app/runtime/collect/__init__.py
Modify: backend/tests/runtime/test_collect_stage.py
```

**Required behavior:**

```text
CollectRuntime.process_turn(state, user_message) -> CollectTurnResult
CollectTurnResult includes: status (continue | waiting | ready), public_reply, updated CollectContext, optional PlanningNeed
pending clarification resumes correctly across turns
emits no LLM/DB/MCP in unit tests when using injected extractors
ConversationPolicy chooses follow-up vs confirmation vs exploration (template-first parity with collect_requirements)
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_collect_stage.py -q
```

### Task 8: Replace Collect Stage Skeleton With Real Handler

**Files:**

```text
Modify: backend/app/runtime/stages/collect.py
Modify: backend/app/runtime/planning_runtime.py
Modify: backend/tests/runtime/test_planning_runtime.py
```

**Required behavior:**

```text
CollectStageHandler calls CollectRuntime.process_turn
if status=continue or waiting: StageResult.status=waiting, PlanningRuntime stops after collect
if status=ready: write planning_need to RuntimeState, StageResult.status=completed
stage_started / stage_completed events still emitted for collect
waiting collect does not run prepare_base_context in same run
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_collect_stage.py backend/tests/runtime/test_planning_runtime.py -q
```

### Task 9: Implement ContextSpec And ContextAssembler

**Files:**

```text
Create: backend/app/runtime/context/specs.py
Create: backend/app/runtime/context/assembler.py
Create: backend/app/runtime/context/__init__.py
Create: backend/tests/runtime/test_context_assembler.py
```

**Required behavior:**

```text
ContextSpec registry keyed by agent_name or stage
ContextAssembler.assemble(agent_name, state) -> AgentContext dict
formal planning specs reject raw CollectContext keys
AgentContext contains only allowed sections from PlanningNeed / BaseContext
no prompt text in output
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_context_assembler.py -q
```

### Task 10: Implement PrepareBaseContext Stage

**Files:**

```text
Modify: backend/app/runtime/stages/prepare_base_context.py
Create: backend/tests/runtime/test_prepare_base_context_stage.py
```

**Required behavior:**

```text
requires planning_need present; otherwise failed/waiting with structured error
builds BaseContext from PlanningNeed + optional memory snippets (injected stub in tests)
does not read CollectContext
writes base_context to RuntimeState.stage_outputs and top-level base_context field
subsequent skeleton stages unchanged
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_prepare_base_context_stage.py -q
```

### Task 11: Update Runtime Framework Inventory

**Files:**

```text
Modify: docs/rag-agent-refactor/runtime-framework-inventory.md
Modify: docs/rag-agent-refactor/README.md
```

**Required inventory updates:**

```text
Add runtime/collect/, runtime/context/, runtime/semantic/ files with Slice 3 status
Mark collect.py / prepare_base_context.py as active (no longer skeleton-only)
Record graph/semantic as compatibility reference until old graph retires
Update last_verified_date
```

**Verification:**

```powershell
Test-Path docs/rag-agent-refactor/runtime-framework-inventory.md
uv run pytest backend/tests/runtime -q
```

### Task 12: Slice 3 Integration Smoke Test

**Files:**

```text
Modify: backend/tests/runtime/test_runtime_skeleton_smoke.py
或 Create: backend/tests/runtime/test_collect_context_smoke.py
```

**Required behavior:**

```text
multi-turn collect: greeting -> follow-up -> confirmation -> planning_need -> base_context
single-run PlanningRuntime stops on first collect waiting turn
full collect-ready path runs collect + prepare_base_context then skeleton stages through finalize
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime -q
uv run pytest backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py -q
```

## 5. Integration Rules

### Existing Graph

Do not delete or rewrite in Slice 3:

```text
backend/app/graph/nodes/collect_requirements.py
backend/app/graph/builder.py
backend/app/services/chat_stream.py default path
```

Collect migration should be behavior-parity driven: port logic into Runtime modules, keep old
graph passing existing tests until Phase 9 retirement.

### Existing Semantic Tests

Keep passing:

```text
backend/tests/test_nl_extract.py
backend/tests/test_nl_extract_selection.py
backend/tests/test_step_context_memory.py
backend/tests/test_context_flow_fixes.py
```

If Runtime semantic layer wraps graph modules initially, both test suites must stay green.

### PlanningRuntime Stop Semantics

Slice 3 introduces first `waiting` stage behavior:

```text
collect waiting -> emit stage_completed(collect, status=waiting) -> runtime pauses without runtime_completed
resume with new user message -> collect runs again in a new PlanningRuntime.run() invocation
collect ready -> continue to prepare_base_context and remaining skeleton stages
```

Document this in `planning_runtime.py` docstring when implementing Task 8.

## 6. Verification Commands

Run after each task:

```powershell
uv run pytest backend/tests/runtime/test_runtime_state.py -q
uv run pytest backend/tests/runtime/test_collect_context.py -q
uv run pytest backend/tests/runtime/test_planning_input.py -q
uv run pytest backend/tests/runtime/test_context_assembler.py -q
uv run pytest backend/tests/runtime/test_collect_stage.py -q
uv run pytest backend/tests/runtime/test_prepare_base_context_stage.py -q
```

Final Slice 3 verification:

```powershell
uv run pytest backend/tests/runtime backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py backend/tests/test_nl_extract.py backend/tests/test_context_flow_fixes.py -q
```

Expected:

```text
all new collect/context runtime tests pass
Slice 1/2 runtime tests still pass
old graph/stream/checkpoint/approval tests still pass
collect waiting/resume semantics verified
PlanningNeed boundary enforced in ContextAssembler tests
```

## 7. Completion Criteria

Slice 3 is complete when:

```text
CollectContext / PlanningNeed / BaseContext schemas exist and round-trip through RuntimeState
GreetingPolicy prevents planning on greeting-only first turn
semantic rules run before LLM extraction in CollectRuntime
pending clarification resumes correctly
PlanningInputCompiler does not invent missing facts
ContextAssembler rejects raw CollectContext for formal planning specs
prepare_base_context builds BaseContext only from PlanningNeed
CollectStageHandler and PrepareBaseContextStageHandler replace skeleton behavior for those stages
runtime-framework-inventory.md updated for Slice 3
Slice 3 tests pass without breaking Slice 1/2 or old graph compatibility tests
```

After this, the next implementation plan is
[13-v1-evidence-engine-implementation-plan.md](13-v1-evidence-engine-implementation-plan.md).
