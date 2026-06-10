# Runtime Framework Inventory

本文记录 PlanningRuntime 新框架当前真实存在的文件、复用边界、兼容旧流程和后续删除
门禁。它是迁移事实清单，不是目标目录草图，也不是立即删除旧文件的授权。

```text
Inventory scope: Slice 1 / Slice 2 / Slice 3 / Slice 4 / Slice 5 / Slice 6 / Slice 7 / Slice 8
Last verified date: 2026-06-09
Runtime status values: active / compatibility / reserved / candidate_redundant
```

生成产物如 `__pycache__/`、测试缓存和本地运行文件不属于框架资产，不纳入本清单。

## New Runtime Files

### Runtime Core

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/__init__.py` | Runtime package boundary | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/manifest.py` | Frozen V1 stage names and validation | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/state.py` | Runtime-owned structured execution state including plan proposals and itinerary draft | Slice 1 / Slice 3 / Slice 4 / Slice 5 / Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/events.py` | Internal RuntimeEvent contract and transport-neutral event factories | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/planning_runtime.py` | Sequential stage dispatcher, collect waiting pause, evidence/tool state merge, RuntimeEvent producer | Slice 1 / Slice 3 / Slice 4 / Slice 5 | active | — | — | 2026-06-09 |

### Runtime Stages

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/stages/__init__.py` | Stage package boundary | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/base.py` | StageHandler contract, StageResult, skeleton registry | Slice 1 | active | — | — | 2026-06-06 |
| `backend/app/runtime/stages/collect.py` | Collect stage facade over `CollectRuntime.process_turn()` | Slice 1 / Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/stages/prepare_base_context.py` | BaseContext builder from validated `PlanningNeed` | Slice 1 / Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/stages/retrieve_evidence.py` | EvidenceEngine retrieval stage; writes `evidence_context` and `sufficiency_result` | Slice 1 / Slice 4 | active | — | — | 2026-06-09 |
| `backend/app/runtime/stages/tool_enrich.py` | ToolService weather enrichment stage; writes `tool_context` | Slice 1 / Slice 5 | active | — | — | 2026-06-09 |
| `backend/app/runtime/stages/domain_plan.py` | DomainPlannerGroup stage; writes `plan_proposals` | Slice 1 / Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/stages/integrate.py` | ItineraryIntegrator stage; writes `itinerary_draft` | Slice 1 / Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/stages/verify.py` | QualityVerifier stage; writes `quality_report`, optional auto-revision | Slice 1 / Slice 7 | active | — | — | 2026-06-10 |
| `backend/app/runtime/stages/approve_or_revise.py` | Approval waiting/completion stage; writes `pending_approval` | Slice 1 / Slice 8 | active | — | — | 2026-06-10 |
| `backend/app/runtime/stages/finalize.py` | Finalization stage; order_id + final message + persistence | Slice 1 / Slice 8 | active | — | — | 2026-06-10 |

### Runtime Collect

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/collect/__init__.py` | Collect package boundary | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/collect/schemas.py` | `CollectContext`, `PlanningNeed`, provenance schemas | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/collect/greeting.py` | GreetingPolicy / GreetingResponder | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/collect/readiness.py` | HybridReadinessEvaluator | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/collect/planning_input.py` | PlanningInputCompiler / Validator | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/collect/conversation_policy.py` | Collect reply policy | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/collect/runtime.py` | `CollectRuntime.process_turn()` orchestrator | Slice 3 | active | — | — | 2026-06-09 |

### Runtime Context

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/context/__init__.py` | Context package boundary | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/context/schemas.py` | `BaseContext` schema | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/context/specs.py` | `ContextSpec` registry and visibility policy including evidence and weather summaries | Slice 3 / Slice 4 / Slice 5 | active | — | — | 2026-06-09 |
| `backend/app/runtime/context/assembler.py` | `ContextAssembler` agent view builder with evidence and weather summaries | Slice 3 / Slice 4 / Slice 5 | active | — | — | 2026-06-09 |
| `backend/app/runtime/context/builder.py` | `BaseContext` builder from `PlanningNeed` | Slice 3 | active | — | — | 2026-06-09 |

### Runtime Semantic

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/semantic/__init__.py` | Semantic adapter package boundary | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/semantic/normalizer.py` | Text normalization adapter over graph semantic rules | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/semantic/slot_binding.py` | Slot binding adapter over graph semantic rules | Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/runtime/semantic/collection_frame.py` | `CollectSemanticLayer` semantic frame lifecycle | Slice 3 | active | — | — | 2026-06-09 |

### Runtime Executor And Stream

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/executor/__init__.py` | Runtime executor package boundary | Slice 2 | active | — | — | 2026-06-06 |
| `backend/app/runtime/executor/graph_builder.py` | Independent 9-stage LangGraph StateGraph builder | Slice 2 | active | — | — | 2026-06-06 |
| `backend/app/runtime/executor/langgraph_executor.py` | Stable RuntimeEvent stream adapter; optional handler injection | Slice 2 / Slice 3 | active | — | — | 2026-06-09 |
| `backend/app/services/runtime_chat_stream.py` | RuntimeEvent and single public-token stream multiplexer | Slice 2 | active | — | — | 2026-06-06 |

### Runtime Tests

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/tests/runtime/__init__.py` | Runtime test package boundary | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_state.py` | Manifest and RuntimeState contract tests | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_events.py` | RuntimeEvent contract tests | Slice 1 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_stage_skeleton.py` | Stage handler contract tests including collect/prepare behavior | Slice 1 / Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_planning_runtime.py` | Sequential dispatcher, collect waiting pause, failure behavior | Slice 1 / Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_runtime_graph_builder.py` | Runtime StateGraph and executor adapter tests | Slice 2 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_chat_stream.py` | RuntimeEvent/token multiplexer tests | Slice 2 | active | — | — | 2026-06-06 |
| `backend/tests/runtime/test_runtime_skeleton_smoke.py` | Slice 1/2 end-to-end RuntimeEvent smoke test with collect stub | Slice 2 / Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_collect_context.py` | CollectContext / PlanningNeed / BaseContext round-trip tests | Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_collect_stage.py` | Greeting, readiness and CollectRuntime tests | Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_planning_input.py` | PlanningNeed compilation tests | Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_semantic_layer.py` | Runtime semantic adapter tests | Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_context_assembler.py` | ContextSpec / ContextAssembler visibility tests | Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_prepare_base_context_stage.py` | Prepare-base-context stage tests | Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_collect_context_smoke.py` | Slice 3 multi-turn collect and base-context smoke tests | Slice 3 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_evidence_schemas.py` | EvidenceCard / EvidenceContext / SufficiencyResult schema tests | Slice 4 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_evidence_engine.py` | QueryAnalyzer, EvidenceEngine, SufficiencyEvaluator and repository tests | Slice 4 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_retrieve_evidence_stage.py` | Retrieve-evidence stage handler tests | Slice 4 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_evidence_context_smoke.py` | Slice 4 collect → prepare → retrieve integration smoke tests | Slice 4 | active | — | — | 2026-06-09 |
| `backend/tests/fixtures/evidence/approved_chengdu_cards.json` | Approved/pending Chengdu EvidenceCard fixture for V1 retrieval tests | Slice 4 | active | — | — | 2026-06-09 |

### Runtime Knowledge (EvidenceEngine)

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/knowledge/evidence_schemas.py` | EvidenceCard, EvidenceContext, SufficiencyResult runtime schemas | Slice 4 | active | — | — | 2026-06-09 |
| `backend/app/knowledge/tokenizers.py` | `ChineseTokenizer` protocol and `JiebaTokenizer` adapter | Slice 4 | active | — | — | 2026-06-09 |
| `backend/app/knowledge/evidence_repository.py` | `FixtureEvidenceRepository` and `PostgresEvidenceRepository` stub | Slice 4 | active | — | — | 2026-06-09 |
| `backend/app/knowledge/query_analyzer.py` | `build_retrieval_query()` from `PlanningNeed` and `BaseContext` | Slice 4 | active | — | — | 2026-06-09 |
| `backend/app/knowledge/evidence_engine.py` | Approved-card filter, BM25 + vector stub + RRF retrieval | Slice 4 | active | — | — | 2026-06-09 |
| `backend/app/knowledge/evidence_sufficiency.py` | Sufficiency evaluation with `mark_assumptions_and_continue` | Slice 4 | active | — | — | 2026-06-09 |

### Runtime Tools (ToolService)

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/tools/__init__.py` | Runtime tools package boundary | Slice 5 | active | — | — | 2026-06-09 |
| `backend/app/runtime/tools/schemas.py` | `ToolContext`, `WeatherContext`, `ToolWarning` schemas | Slice 5 | active | — | — | 2026-06-09 |
| `backend/app/runtime/tools/allowlist.py` | V1 tool allowlist registry | Slice 5 | active | — | — | 2026-06-09 |
| `backend/app/runtime/tools/weather_adapter.py` | Weather markdown trim adapter over existing weather stack | Slice 5 | active | — | — | 2026-06-09 |
| `backend/app/runtime/tools/service.py` | `ToolService.enrich()` orchestrator | Slice 5 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_tool_schemas.py` | ToolContext schema tests | Slice 5 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_tool_service.py` | ToolService / allowlist / weather adapter tests | Slice 5 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_tool_enrich_stage.py` | Tool-enrich stage handler tests | Slice 5 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_tool_context_smoke.py` | Slice 5 collect → tool_enrich integration smoke tests | Slice 5 | active | — | — | 2026-06-09 |

### Runtime Domain Planning

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/planning/__init__.py` | Domain planning package boundary | Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/planning/schemas.py` | `PlanProposal` and `ItineraryDraft` schemas | Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/planning/destination_planner.py` | DestinationPlanner deterministic V1 implementation | Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/planning/route_transport_activity_planner.py` | RouteTransportActivityPlanner V1 implementation | Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/planning/stay_food_planner.py` | StayFoodPlanner V1 implementation | Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/planning/planner_group.py` | DomainPlannerGroup orchestration | Slice 6 | active | — | — | 2026-06-09 |
| `backend/app/runtime/planning/integrator.py` | ItineraryIntegrator merge logic | Slice 6 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_planning_schemas.py` | PlanProposal / ItineraryDraft schema tests | Slice 6 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_domain_planner_group.py` | DomainPlannerGroup tests | Slice 6 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_itinerary_integrator.py` | ItineraryIntegrator tests | Slice 6 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_domain_plan_stage.py` | Domain-plan stage handler tests | Slice 6 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_integrate_stage.py` | Integrate stage handler tests | Slice 6 | active | — | — | 2026-06-09 |
| `backend/tests/runtime/test_domain_planning_smoke.py` | Slice 6 end-to-end domain_plan / integrate smoke tests | Slice 6 | active | — | — | 2026-06-09 |

### Runtime Quality

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/quality/__init__.py` | Quality package boundary | Slice 7 | active | — | — | 2026-06-10 |
| `backend/app/runtime/quality/schemas.py` | `QualityIssue` and `QualityReport` schemas | Slice 7 | active | — | — | 2026-06-10 |
| `backend/app/runtime/quality/verifier.py` | Deterministic QualityVerifier judge | Slice 7 | active | — | — | 2026-06-10 |
| `backend/app/runtime/quality/revision_agent.py` | Single-pass RevisionAgent auto-fix | Slice 7 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_quality_schemas.py` | Quality schema tests | Slice 7 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_quality_verifier.py` | Verifier and revision agent tests | Slice 7 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_verify_stage.py` | Verify stage handler tests | Slice 7 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_quality_smoke.py` | Slice 7 verify integration smoke tests | Slice 7 | active | — | — | 2026-06-10 |

### Runtime Finalization

| Path | Owner / responsibility | Introduced by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|---------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/runtime/finalization/__init__.py` | Finalization package boundary | Slice 8 | active | — | — | 2026-06-10 |
| `backend/app/runtime/finalization/schemas.py` | `PendingApproval` and `FinalizationResult` schemas | Slice 8 | active | — | — | 2026-06-10 |
| `backend/app/runtime/finalization/order_service.py` | Order id generation | Slice 8 | active | — | — | 2026-06-10 |
| `backend/app/runtime/finalization/final_response.py` | Final user message builder | Slice 8 | active | — | — | 2026-06-10 |
| `backend/app/runtime/finalization/persistence.py` | Itinerary persistence adapter + stub | Slice 8 | active | — | — | 2026-06-10 |
| `backend/app/runtime/finalization/approval_payload.py` | Pending approval payload builder | Slice 8 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_finalization_schemas.py` | Finalization schema tests | Slice 8 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_final_response.py` | Final response generator tests | Slice 8 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_approval_finalize_stage.py` | Approval/finalize stage tests | Slice 8 | active | — | — | 2026-06-10 |
| `backend/tests/runtime/test_approval_finalize_smoke.py` | Slice 8 end-to-end approval/finalize smoke tests | Slice 8 | active | — | — | 2026-06-10 |

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
| `backend/tests/test_context_flow_fixes.py` | Stream extra_info merge regression tests | Reused by Slice 3 verification | compatibility | Runtime stream adapter tests | Old stream path retired with equivalent coverage | 2026-06-09 |
| `backend/tests/test_nl_extract_selection.py` | NL selection rule tests referenced by semantic migration | Reused by Slice 3 verification | compatibility | Runtime semantic/collect tests | Old graph retired with equivalent coverage | 2026-06-09 |
| `backend/app/graph/semantic/semantic_pipeline.py` | Existing semantic frame pipeline | Reused by Slice 3 through runtime adapters | compatibility | `backend/app/runtime/semantic/collection_frame.py` | Runtime semantic layer owns behavior and old graph semantic path retires | 2026-06-09 |
| `backend/app/graph/semantic/normalizer.py` | Existing text normalization rules | Reused by Slice 3 through runtime adapters | compatibility | `backend/app/runtime/semantic/normalizer.py` | Runtime semantic layer owns behavior and old graph semantic path retires | 2026-06-09 |
| `backend/app/graph/semantic/slot_tracker.py` | Existing slot binding rules | Reused by Slice 3 through runtime adapters | compatibility | `backend/app/runtime/semantic/slot_binding.py` | Runtime semantic layer owns behavior and old graph semantic path retires | 2026-06-09 |
| `backend/app/graph/greeting.py` | Existing greeting-only detection and reply templates | Reused by Slice 3 collect greeting policy | compatibility | `backend/app/runtime/collect/greeting.py` | Runtime collect owns greeting behavior and old graph path retires | 2026-06-09 |
| `backend/app/knowledge/rag_service.py` | Existing chunk-oriented RAG service for old graph nodes | Existing old flow | compatibility | `backend/app/knowledge/evidence_engine.py` | Runtime retrieve_evidence is default path and old graph RAG nodes retire | 2026-06-09 |
| `backend/app/knowledge/rag_pipeline.py` | Existing chunk retrieval pipeline backing old RAG service | Existing old flow | compatibility | `backend/app/knowledge/evidence_engine.py` | Runtime retrieve_evidence is default path and old graph RAG nodes retire | 2026-06-09 |
| `backend/app/knowledge/hybrid_retriever.py` | Existing chunk hybrid retriever (Chroma + BM25 + RRF reference) | RRF pattern reference for Slice 4 | compatibility | `backend/app/knowledge/evidence_engine.py` | EvidenceEngine owns card retrieval and old chunk path retires | 2026-06-09 |
| `backend/app/tools/weather.py` | Existing LangChain weather tool entry | Reused by Slice 5 through WeatherToolAdapter | compatibility | `backend/app/runtime/tools/weather_adapter.py` | Runtime tool_enrich is default path and old graph weather path retires | 2026-06-09 |
| `backend/app/mcp/adapters/weather_adapter.py` | Existing QWeather / MCP weather adapter | Reused by Slice 5 through tools/weather.py | compatibility | `backend/app/runtime/tools/weather_adapter.py` | Runtime tool_enrich is default path | 2026-06-09 |

## Compatibility-Only Old Flow Files

下列文件仍是当前旧线上流程的一部分。它们只对新 Runtime 具有兼容和迁移参考价值，
但在 Runtime 成为默认主路径前仍不可删除。

| Path | Owner / responsibility | Introduced or reused by slice | Runtime status | Replacement path | Deletion prerequisites | Last verified date |
|------|------------------------|-------------------------------|----------------|------------------|------------------------|-------------------|
| `backend/app/graph/builder.py` | Builds the existing travel graph | Existing old flow | compatibility | `backend/app/runtime/executor/graph_builder.py` | Runtime becomes default path; checkpoint, streaming, approval and finalization parity verified | 2026-06-06 |
| `backend/app/graph/state.py` | Existing graph `TravelState` | Existing old flow | compatibility | `backend/app/runtime/state.py` for new flow only | Old graph retired and no active API/service depends on TravelState | 2026-06-06 |
| `backend/app/graph/nodes/collect_requirements.py` | Existing multi-turn requirement collection node | Existing old flow | compatibility | `backend/app/runtime/collect/` plus `backend/app/runtime/stages/collect.py` | Runtime collect is default path and multi-turn/greeting/resume regression coverage is migrated | 2026-06-09 |
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
| `backend/app/runtime/memory/` | Runtime memory read boundary | Slice 3+ | absent | Approved memory implementation plan | 2026-06-09 |
| `backend/app/runtime/discovery/` | Destination discovery catalog helpers | Slice 4+ | absent | Approved discovery implementation plan | 2026-06-09 |
| `backend/app/runtime/agents/` | Runtime-owned Agent roles | Slice 6+ | absent | Approved LLM agent implementation plan | 2026-06-09 |
| `backend/app/runtime/skills/` | Explicit Skill packages and registry | Slice 3+ | absent | First real Skill implementation plan | 2026-06-09 |
| `backend/app/runtime/observability/` | Runtime trace recorder and optional LangSmith adapter | Later approved Slice | absent | Approved observability implementation plan | 2026-06-09 |
| `backend/app/ai/prompts/runtime/` | Runtime Agent and Skill prompt files | First real Agent/Skill Slice | absent | Approved prompt owner and input schema | 2026-06-09 |

## Candidate Redundant Files

当前没有文件满足 `candidate_redundant` 条件。

原因：

```text
PlanningRuntime 尚未成为默认 chat path
Slice 8 已完成 approve_or_revise / finalize，但前端 RuntimeEvent 切换尚未实现
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
