# Runtime Framework Inventory

本文记录 PlanningRuntime 新框架当前真实存在的文件、复用边界、兼容旧流程和后续删除
门禁。它是迁移事实清单，不是目标目录草图，也不是立即删除旧文件的授权。

```text
Inventory scope: Slice 1 / Slice 2
Last verified date: 2026-06-06
Runtime status values: active / compatibility / reserved / candidate_redundant
```

生成产物如 `__pycache__/`、测试缓存和本地运行文件不属于框架资产，不纳入本清单。

## New Runtime Files

### Runtime Core

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/__init__.py` | Runtime package boundary | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/manifest.py` | Frozen V1 stage names and validation | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/state.py` | Runtime-owned structured execution state and update helpers | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/events.py` | Internal RuntimeEvent contract and transport-neutral event factories | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/planning_runtime.py` | Sequential stage dispatcher and RuntimeEvent producer | Slice 1 | active | — | — | 2026-06-06 |

### Runtime Stages

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/stages/__init__.py` | Stage package boundary | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/base.py` | StageHandler contract, StageResult, skeleton registry | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/collect.py` | Collect stage skeleton; real collect behavior enters later Slice | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/prepare_base_context.py` | Base-context stage skeleton | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/retrieve_evidence.py` | Evidence retrieval stage skeleton | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/tool_enrich.py` | Tool enrichment stage skeleton | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/domain_plan.py` | Domain planning stage skeleton | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/integrate.py` | Itinerary integration stage skeleton | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/verify.py` | Quality verification stage skeleton | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/approve_or_revise.py` | Approval and revision routing stage skeleton | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/finalize.py` | Finalization stage skeleton | Slice 1 | active | — | — | 2026-06-06 |

### Runtime Executor And Stream

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/executor/__init__.py` | Runtime executor package boundary | Slice 2 | active | — | — | 2026-06-06 |
| `backend/app/runtime/executor/graph_builder.py` | Independent 9-stage LangGraph StateGraph builder | Slice 2 | active | — | — | 2026-06-06 |
| `backend/app/runtime/executor/langgraph_executor.py` | Stable RuntimeEvent stream adapter; checkpointer bridge reserved | Slice 2 | active | — | — | 2026-06-06 |
| `backend/app/services/runtime_chat_stream.py` | RuntimeEvent and single public-token stream multiplexer | Slice 2 | active | — | — | 2026-06-06 |

### Runtime Tests

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/tests/runtime/__init__.py` | Runtime test package boundary | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_state.py` | Manifest and RuntimeState contract tests | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_events.py` | RuntimeEvent contract tests | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_stage_skeleton.py` | Nine-stage handler skeleton tests | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_planning_runtime.py` | Sequential dispatcher and failure behavior tests | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_graph_builder.py` | Runtime StateGraph and executor adapter tests | Slice 2 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_chat_stream.py` | RuntimeEvent/token multiplexer tests | Slice 2 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_skeleton_smoke.py` | Slice 1/2 end-to-end RuntimeEvent smoke test | Slice 2 | active | — | — | 2026-06-06 |

## Reused Existing Files

这些文件仍由现有系统拥有。Slice 1/2 只复用其能力、接口经验或回归测试，不迁移其
所有权。

| Path | Owner / responsibility | Introduced or reused by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|-------------------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/graph/checkpoint.py` | Existing LangGraph checkpointer creation and compatibility handling | Reused by future executor integration | compatibility | Runtime executor may consume its checkpointer through dependency injection | Runtime checkpointer/interrupt/resume integration verified before ownership changes | 2026-06-06 |
| `backend/app/services/chat_stream.py` | Existing graph-event/token streaming and message persistence | Slice 2 behavior reference and compatibility path | compatibility | `backend/app/services/runtime_chat_stream.py` only replaces multiplexing for new Runtime | New Runtime becomes default chat path and all persistence/transport behavior has equivalent coverage | 2026-06-06 |
| `backend/app/ws/chat_stream.py` | Existing WebSocket chat transport | Future Runtime transport integration | compatibility | No replacement confirmed; expected to reuse through adapter | Frontend and WebSocket switch approved and regression-tested | 2026-06-06 |
| `backend/tests/test_chat_stream.py` | Existing streaming compatibility tests | Slice 2 regression verification | compatibility | Runtime stream tests cover only new multiplexer behavior | Old stream path retired and equivalent persistence/transport tests exist | 2026-06-06 |
| `backend/tests/test_checkpoint.py` | Existing checkpoint compatibility tests | Slice 2 regression verification | compatibility | Future Runtime checkpoint tests | Runtime checkpoint/interrupt/resume tests provide equivalent coverage | 2026-06-06 |
| `backend/tests/test_approval_router.py` | Existing approval routing compatibility tests | Slice 2 regression verification | compatibility | Future `approve_or_revise` integration tests | Real Runtime approval/revision behavior is implemented and equivalent coverage exists | 2026-06-06 |

## Compatibility-Only Old Flow Files

下列文件仍是当前旧线上流程的一部分。它们只对新 Runtime 具有兼容和迁移参考价值，
但在 Runtime 成为默认主路径前仍不可删除。

| Path | Owner / responsibility | Introduced or reused by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|-------------------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/graph/builder.py` | Builds the existing travel graph | Existing old flow | compatibility | `backend/app/runtime/executor/graph_builder.py` | Runtime becomes default path; checkpoint, streaming, approval and finalization parity verified | 2026-06-06 |
| `backend/app/graph/state.py` | Existing graph `TravelState` | Existing old flow | compatibility | `backend/app/runtime/state.py` for new flow only | Old graph retired and no active API/service depends on TravelState | 2026-06-06 |
| `backend/app/graph/nodes/collect_requirements.py` | Existing multi-turn requirement collection node | Existing old flow | compatibility | `backend/app/runtime/stages/collect.py` plus future collect/context modules | Real Runtime collect Slice passes multi-turn, greeting and resume regression tests | 2026-06-06 |
| `backend/app/graph/nodes/plan_destination.py` | Existing destination planning node | Existing old flow | compatibility | `backend/app/runtime/stages/domain_plan.py` plus future domain agents | Real DomainPlannerGroup is implemented and old graph is retired | 2026-06-06 |
| `backend/app/graph/nodes/plan_transport.py` | Existing transport planning node | Existing old flow | compatibility | Future RouteTransportActivityPlanner through `domain_plan` | Transport constraints and degradation behavior pass Runtime tests | 2026-06-06 |
| `backend/app/graph/nodes/plan_stay_and_food.py` | Existing stay and food planning node | Existing old flow | compatibility | Future StayFoodPlanner through `domain_plan` | Stay/food proposal and integration behavior pass Runtime tests | 2026-06-06 |
| `backend/app/graph/nodes/plan_activities.py` | Existing activity planning node | Existing old flow | compatibility | Future RouteTransportActivityPlanner through `domain_plan` | Activity proposal and integration behavior pass Runtime tests | 2026-06-06 |
| `backend/app/graph/nodes/build_itinerary.py` | Existing itinerary assembly node | Existing old flow | compatibility | `backend/app/runtime/stages/integrate.py` plus future integrator | Real integration, budget and persistence parity verified | 2026-06-06 |
| `backend/app/graph/nodes/approval_node.py` | Existing approval node | Existing old flow | compatibility | `backend/app/runtime/stages/approve_or_revise.py` | Runtime approval interrupt/resume is implemented and frontend switched | 2026-06-06 |
| `backend/app/graph/nodes/revise_itinerary.py` | Existing itinerary revision node | Existing old flow | compatibility | Future RevisionAgent through `approve_or_revise` | Runtime revision routing and quality verification pass regression tests | 2026-06-06 |
| `backend/app/graph/nodes/final_response.py` | Existing final response and order generation node | Existing old flow | compatibility | `backend/app/runtime/stages/finalize.py` plus future finalization modules | Runtime finalization persists itinerary/order exactly once and frontend consumes events | 2026-06-06 |
| `backend/app/graph/routers/step_router.py` | Existing graph step routing | Existing old flow | compatibility | Runtime manifest edges and future stage policies | Old graph retired and no active caller imports router | 2026-06-06 |
| `backend/app/graph/routers/approval_router.py` | Existing approval routing | Existing old flow | compatibility | Future `approve_or_revise` routing policy | Runtime approval/revision tests replace existing behavior coverage | 2026-06-06 |

## Future Slice Files Not Created Yet

本节是已确认但尚不存在的规划路径，不属于当前真实文件清单。只有进入对应 Slice 后才能
创建；每个 Slice 完成后应将实际创建的路径迁入 `New Runtime Files`。

| Planned path | Intended responsibility | Earliest slice | Current existence | Creation gate | Last verified date |
|--------------|-------------------------|----------------|-------------------|---------------|-------------------|
| `backend/app/runtime/context/` | ContextAssembler and ContextSpec | Slice 3 | absent | Approved collect/context implementation plan | 2026-06-06 |
| `backend/app/runtime/memory/` | Runtime memory read boundary | Slice 3 or later | absent | Approved memory implementation plan | 2026-06-06 |
| `backend/app/runtime/semantic/` | Collect semantic migration | Slice 3 | absent | Approved collect/context implementation plan | 2026-06-06 |
| `backend/app/runtime/agents/` | Runtime-owned Agent roles | Slice 6 | absent | Approved multi-agent implementation plan | 2026-06-06 |
| `backend/app/runtime/skills/` | Explicit Skill packages and registry | Slice 3 or later | absent | First real Skill implementation plan | 2026-06-06 |
| `backend/app/runtime/tools/` | ToolService and Runtime tool adapters | Slice 5 | absent | Approved ToolService implementation plan | 2026-06-06 |
| `backend/app/runtime/quality/` | QualityVerifier and quality schemas | Slice 7 | absent | Approved quality/revision implementation plan | 2026-06-06 |
| `backend/app/runtime/finalization/` | Final response, order and finalization schemas | Slice 8 | absent | Approved approval/finalization implementation plan | 2026-06-06 |
| `backend/app/runtime/observability/` | Runtime trace recorder and optional LangSmith adapter | Later approved Slice | absent | Approved observability implementation plan | 2026-06-06 |
| `backend/app/ai/prompts/runtime/` | Runtime Agent and Skill prompt files | First real Agent/Skill Slice | absent | Approved prompt owner and input schema | 2026-06-06 |
| `backend/app/knowledge/tokenizers.py` | ChineseTokenizer boundary and Jieba adapter | Slice 4 | absent | Approved EvidenceEngine implementation plan | 2026-06-06 |

## Candidate Redundant Files

当前没有文件满足 `candidate_redundant` 条件。

原因：

```text
PlanningRuntime 尚未成为默认 chat path
Runtime stages 仍是 skeleton，不具备旧 graph 的真实业务能力
checkpoint / interrupt / resume 尚未接入 Runtime executor
finalize、持久化和前端 RuntimeEvent 切换尚未实现
```

旧流程文件只能保持 `compatibility` 状态。后续将文件标记为 `candidate_redundant` 时，
必须新增包含以下全部字段的记录：

| Path | Owner / responsibility | Introduced or reused by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|-------------------------------|----------------|------------------|------------------------|-------------------|
| No candidate identified | — | — | — | — | — | 2026-06-06 |

## Deletion Gate

任何旧文件删除前必须同时满足：

```text
1. 已存在并验证 replacement path
2. replacement 已成为默认线上主路径
3. 对应真实业务能力已迁移，不只是 skeleton
4. API / DB / frontend 契约影响已获得用户确认
5. 旧路径调用方搜索结果为空，或调用方已全部迁移
6. 新路径具备等价或更强的自动化测试覆盖
7. Runtime 全量测试和旧路径兼容测试通过
8. 删除动作拥有独立、明确的用户确认
```

删除前最低验证：

```powershell
rg -n "<candidate module or symbol>" backend frontend
uv run pytest backend/tests/runtime -q
uv run pytest backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py -q
```

本清单不会自行授权删除。每次完成后续 Slice 时，应更新状态、replacement path、
deletion prerequisites 和 `last_verified_date`。
