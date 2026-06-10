# V1 DomainPlannerGroup And Integrator Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Slice 6 from
> [10-v1-implementation-roadmap.md](10-v1-implementation-roadmap.md).

**Goal:** 让 PlanningRuntime 的 `domain_plan` 与 `integrate` 阶段产出结构化
`PlanProposal` 与 `ItineraryDraft`，替换旧 `plan_*` / `build_itinerary` 节点在
新 Runtime 中的职责。

**Architecture:** `DomainPlanStageHandler` 调用 `DomainPlannerGroup.run()`，按
Destination → RouteTransportActivity + StayFood 顺序生成三个 `PlanProposal`。
`IntegrateStageHandler` 调用 `ItineraryIntegrator.integrate()` 合并为
`ItineraryDraft`。V1 使用 **deterministic rule-based planners**（不调用 LLM），
通过 `ContextAssembler` 读取正式规划视图，不读取 `collect_context`。

**Tech Stack:** Python, Pydantic, pytest-asyncio, 复用现有 `ContextAssembler`、
EvidenceContext、ToolContext。

**Prerequisites:** Slice 5 已完成（`tool_enrich` 真实实现、126 runtime 测试全绿）。

---

## 1. Scope

```text
Slice 6: DomainPlannerGroup + ItineraryIntegrator + domain_plan / integrate stages
```

### In Scope

```text
PlanProposal / ItineraryDraft Pydantic schemas
DestinationPlanner / RouteTransportActivityPlanner / StayFoodPlanner (V1 deterministic)
DomainPlannerGroup orchestration
ItineraryIntegrator merge logic
RuntimeState plan_proposals / itinerary_draft fields
真实 DomainPlanStageHandler / IntegrateStageHandler
Slice 6 integration smoke test
更新 runtime-framework-inventory.md
```

### Out Of Scope

```text
LLM-backed planner prompts (Slice 6.5 or Slice 7 前可选增量)
QualityVerifier / Judge
approval interrupt / finalize persistence
frontend RuntimeEvent switch
Skill package directories
Parallel asyncio planner execution (V1 sequential is acceptable)
```

V1 planners 从 EvidenceCard claims 和 PlanningNeed 推导建议，证据不足处写入
`assumptions`，不编造 unsupported 活动名称。

## 2. Directory Freeze For Slice 6

### Create Now

```text
backend/app/runtime/planning/
  __init__.py
  schemas.py
  destination_planner.py
  route_transport_activity_planner.py
  stay_food_planner.py
  planner_group.py
  integrator.py

backend/app/runtime/stages/domain_plan.py   # replace skeleton
backend/app/runtime/stages/integrate.py   # replace skeleton
backend/tests/runtime/
  test_planning_schemas.py
  test_domain_planner_group.py
  test_itinerary_integrator.py
  test_domain_plan_stage.py
  test_integrate_stage.py
  test_domain_planning_smoke.py
```

## 3. Runtime Contract

### RuntimeState Additions

```python
plan_proposals: list[dict[str, Any]] | None
itinerary_draft: dict[str, Any] | None
```

Rules:

```text
plan_proposals 只在 domain_plan 完成后写入
itinerary_draft 只在 integrate 完成后写入
domain_plan 读取 planning_need / base_context / evidence_context / tool_context
integrate 读取 plan_proposals；不读取 collect_context
domain_plan / integrate 证据或天气不足时仍 completed，assumptions 写入 proposal/draft
```

## 4. Task Plan

### Task 1–5: Schemas, Planners, Group, Integrator

See sections above; verification via unit tests.

### Task 6: RuntimeState + planning_runtime merge

### Task 7–8: Stage handlers

### Task 9: Integration smoke test

### Task 10: Inventory + README

## 5. Completion Criteria

```text
Three PlanProposal outputs with evidence_card_ids and assumptions when needed
ItineraryDraft.days length matches travel_days
Integrator only uses proposal/evidence entities
domain_plan and integrate replace skeletons
Slice 6 tests pass without breaking Slice 1-5 tests
```

Next plan: `16-v1-quality-verifier-implementation-plan.md`
