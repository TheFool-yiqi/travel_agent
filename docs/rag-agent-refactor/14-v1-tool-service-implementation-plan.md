# V1 ToolService Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Slice 5 from
> [10-v1-implementation-roadmap.md](10-v1-implementation-roadmap.md).

**Goal:** 让 PlanningRuntime 的 `tool_enrich` 阶段通过 **ToolService allowlist** 调用
`WeatherTool`，将裁剪后的结果写入 `ToolContext.weather`；工具失败时不阻断后续 stage。

**Architecture:** `ToolEnrichStageHandler` 调用 `ToolService.enrich()`。Service 负责
allowlist 校验、超时/降级、调用 Runtime adapter；adapter 复用现有
`tools/weather.py` → `mcp/adapters/weather_adapter.py`，不把 MCP 暴露给 Agent。
Stage 只写 RuntimeState 结构化输出，Planner 通过 `ContextAssembler` 读取 weather summary。

**Tech Stack:** Python, Pydantic, pytest-asyncio, 复用现有 QWeather / MCP weather 路径。

**Prerequisites:** Slice 4 已完成（`retrieve_evidence` 真实实现、101 runtime 测试全绿）。

---

## 1. Scope

本文只冻结并实现 Slice 5。

```text
Slice 5: ToolService allowlist + WeatherTool + tool_enrich stage
```

### In Scope

```text
ToolContext / WeatherContext / ToolWarning Pydantic schemas
Tool allowlist registry (weather.get_forecast + deterministic helper names reserved)
WeatherTool runtime adapter (wrap existing fetch_weather_info, trim to summary/risks)
ToolService.enrich() with unavailable fallback
RuntimeState tool_context field + set_tool_context helper
真实 ToolEnrichStageHandler（替换 skeleton）
ContextAssembler 扩展 weather summary 可见性
backend/tests/runtime/ tool tests + integration smoke
更新 runtime-framework-inventory.md
```

### Out Of Scope

```text
DomainPlannerGroup / Integrator / Judge
date/holiday helper 作为 ToolService 可调用项（V1 仅注册名称，collect 侧继续使用）
search / maps / transport / hotel MCP 工具
ToolContext 写入长期知识库
frontend RuntimeEvent switch
Runtime 成为默认 chat path
LangSmith tool tracing
```

V1 唯一进入 `ToolContext` 的实时工具是 **weather**；date/holiday 留在 collect 解析层。

## 2. Directory Freeze For Slice 5

### Create Now

```text
backend/app/runtime/tools/
  __init__.py
  schemas.py
  allowlist.py
  service.py
  weather_adapter.py

backend/app/runtime/stages/tool_enrich.py   # replace skeleton
backend/tests/runtime/
  test_tool_schemas.py
  test_tool_service.py
  test_tool_enrich_stage.py
  test_tool_context_smoke.py
```

### Reuse, Do Not Break

```text
backend/app/tools/weather.py
backend/app/mcp/adapters/weather_adapter.py
backend/app/mcp/providers/qweather.py
backend/tests/test_mcp_weather.py           -> compatibility; do not route Runtime around adapter
backend/app/runtime/context/assembler.py  -> extend specs for tool_context.weather
backend/app/runtime/context/specs.py
backend/app/runtime/planning_runtime.py     -> apply tool_context in _apply_stage_state_updates
```

### Do Not Create Yet

```text
backend/app/runtime/tools/search_adapter.py
backend/app/runtime/tools/maps_adapter.py
backend/app/runtime/skills/
Automatic LangChain BaseTool discovery for Runtime agents
```

## 3. Runtime And Tool Contract

### RuntimeState Additions

```python
class RuntimeState(TypedDict, total=False):
    # ... existing fields ...
    tool_context: dict[str, Any] | None
```

Rules:

```text
tool_context 只在 tool_enrich 完成后写入
tool_enrich 读取 planning_need / base_context（destination + travel dates），不读取 collect_context
weather unavailable 时仍 completed（不 blocking），ToolContext.weather.status = unavailable
非 allowlist 工具调用在 ToolService 层拒绝
```

### ToolContext V1 Shape

```python
class WeatherContext(BaseModel):
    status: Literal["available", "unavailable"]
    destination: str | None = None
    date_range: str | None = None
    summary: str = ""
    risks: list[str] = Field(default_factory=list)
    source: str = "qweather"
    fetched_at: str | None = None

class ToolWarning(BaseModel):
    code: str
    message: str

class ToolContext(BaseModel):
    weather: WeatherContext | None = None
    tool_warnings: list[ToolWarning] = Field(default_factory=list)
```

V1 不把 weather 原始 markdown 完整下发给 Agent；`summary` / `risks` 是裁剪结果。

### Tool Allowlist V1

```text
weather.get_forecast          -> writes ToolContext.weather
date.resolve_relative_date    -> registered only; collect helper, not invoked in tool_enrich
holiday.resolve_holiday_hint  -> registered only; collect helper, not invoked in tool_enrich
```

## 4. Task Plan

### Task 1: Define ToolContext Schemas

**Files:**

```text
Create: backend/app/runtime/tools/__init__.py
Create: backend/app/runtime/tools/schemas.py
Create: backend/tests/runtime/test_tool_schemas.py
```

**Required behavior:**

```text
WeatherContext, ToolWarning, ToolContext pydantic models
status validator accepts available | unavailable only
serialize/deserialize round-trip helpers (to_runtime_dict / from_runtime_dict)
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_tool_schemas.py -q
```

### Task 2: Implement Tool Allowlist Registry

**Files:**

```text
Create: backend/app/runtime/tools/allowlist.py
Modify: backend/tests/runtime/test_tool_service.py
```

**Required behavior:**

```text
V1_TOOL_ALLOWLIST frozen set
is_allowlisted(tool_name) -> bool
assert_allowlisted(tool_name) raises ValueError for unknown tools
weather.get_forecast is allowlisted; search/maps/transport are not
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_tool_service.py -k allowlist -q
```

### Task 3: Implement WeatherTool Runtime Adapter

**Files:**

```text
Create: backend/app/runtime/tools/weather_adapter.py
Modify: backend/tests/runtime/test_tool_service.py
```

**Required behavior:**

```text
WeatherToolAdapter.fetch_forecast(destination, date_range) -> WeatherContext
wraps app.tools.weather.fetch_weather_info (injectable for tests)
parses markdown/text into summary + risks (deterministic line-based trim for V1)
on empty destination or adapter exception -> status=unavailable + tool_warnings
sets fetched_at ISO timestamp when available
does not expose raw MCP response on ToolContext
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_tool_service.py -k weather -q
```

### Task 4: Implement ToolService Core

**Files:**

```text
Create: backend/app/runtime/tools/service.py
Modify: backend/tests/runtime/test_tool_service.py
```

**Required behavior:**

```text
ToolService.enrich(planning_need, base_context) -> ToolContext
resolves destination and date_range from PlanningNeed / BaseContext planning_need_summary
calls WeatherToolAdapter when destination present
skips weather gracefully when destination missing (unavailable + warning)
never calls non-allowlisted tools
returns ToolContext even when weather fails
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_tool_service.py -q
```

### Task 5: Extend RuntimeState And Helpers

**Files:**

```text
Modify: backend/app/runtime/state.py
Modify: backend/app/runtime/planning_runtime.py
Modify: backend/tests/runtime/test_runtime_state.py
```

**Required behavior:**

```text
tool_context field on RuntimeState
set_tool_context helper
create_initial_runtime_state initializes tool_context to None
_apply_stage_state_updates merges tool_context from stage data
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_state.py -q
```

### Task 6: Replace ToolEnrich Stage Skeleton

**Files:**

```text
Modify: backend/app/runtime/stages/tool_enrich.py
Create: backend/tests/runtime/test_tool_enrich_stage.py
Modify: backend/tests/runtime/test_stage_skeleton.py
```

**Required behavior:**

```text
ToolEnrichStageHandler calls ToolService.enrich
requires planning_need; uses base_context if present
writes tool_context to RuntimeState
returns completed even when weather unavailable
does not read collect_context
injects ToolService in __init__ for tests
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_tool_enrich_stage.py -q
```

### Task 7: Extend ContextAssembler For ToolContext

**Files:**

```text
Modify: backend/app/runtime/context/specs.py
Modify: backend/app/runtime/context/assembler.py
Modify: backend/tests/runtime/test_context_assembler.py
```

**Required behavior:**

```text
route_transport_activity_planner and itinerary_integrator may read weather_summary
formal planning specs receive trimmed weather (summary + risks + status), not raw markdown
still reject collect_context
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_context_assembler.py -q
```

### Task 8: Slice 5 Integration Smoke Test

**Files:**

```text
Create: backend/tests/runtime/test_tool_context_smoke.py
```

**Required behavior:**

```text
after Slice 4 path, tool_enrich produces ToolContext with weather attempt
weather unavailable stub still completes stage and runtime continues
full path: collect ready -> prepare -> retrieve -> tool_enrich -> skeleton stages continue
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime -q
uv run pytest backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py -q
```

### Task 9: Update Runtime Framework Inventory

**Files:**

```text
Modify: docs/rag-agent-refactor/runtime-framework-inventory.md
Modify: docs/rag-agent-refactor/README.md
```

**Required updates:**

```text
Add runtime/tools/*.py
Mark tool_enrich.py as active
Record tools/weather.py and mcp weather as compatibility reuse
Update last_verified_date
```

## 5. Integration Rules

### Existing Weather Stack

Runtime must route through:

```text
ToolEnrichStageHandler -> ToolService -> WeatherToolAdapter -> tools/weather.py -> mcp/adapters
```

Do not let StageHandler or future Agents call `get_weather_forecast` directly.

### Old Graph step_context Tools

`backend/app/graph/step_context.py` `run_step_tools()` remains old-graph compatibility.
Slice 5 does not migrate transport/search tools into Runtime.

### PlanningRuntime

`tool_enrich` returns `completed` for both available and unavailable weather.
Downstream stages read `tool_context.weather.status` rather than blocking here.

## 6. Verification Commands

Run after each task:

```powershell
uv run pytest backend/tests/runtime/test_tool_schemas.py -q
uv run pytest backend/tests/runtime/test_tool_service.py -q
uv run pytest backend/tests/runtime/test_tool_enrich_stage.py -q
uv run pytest backend/tests/runtime/test_context_assembler.py -q
```

Final Slice 5 verification:

```powershell
uv run pytest backend/tests/runtime backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py -q
uv run pytest backend/tests/test_mcp_weather.py -q
```

Expected:

```text
WeatherTool writes ToolContext.weather when adapter succeeds
unavailable weather does not block planning
non-allowlisted tools are rejected at ToolService
ContextAssembler exposes weather summary to formal planners without collect_context
Slice 1-4 runtime tests still pass
```

## 7. Completion Criteria

Slice 5 is complete when:

```text
ToolContext / WeatherContext / ToolWarning schemas exist
Tool allowlist rejects non-V1 tools
WeatherToolAdapter trims existing weather response into summary/risks
ToolService.enrich() writes ToolContext with graceful degradation
ToolEnrichStageHandler replaces skeleton behavior
RuntimeState stores tool_context
ContextAssembler updated for weather visibility
Slice 5 tests and smoke test pass without breaking Slice 1-4 tests
runtime-framework-inventory.md updated
```

After this, the next implementation plan should be:

```text
15-v1-domain-planner-implementation-plan.md
```

It should cover:

```text
DestinationPlanner / RouteTransportActivityPlanner / StayFoodPlanner
DomainPlannerGroup orchestration
PlanProposal schema
domain_plan stage real implementation
```
