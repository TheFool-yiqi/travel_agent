# V1 Implementation Roadmap

本文承接 [09-planning-runtime-blueprint.md](09-planning-runtime-blueprint.md)，把已经确认的
PlanningRuntime 蓝图拆成可落地的 V1 实施路线。

09 定义目标架构和模块边界；本文定义实现顺序、最小闭环、文件落点、验证方式和暂缓项。
如果本文与 09 在架构语义上冲突，以 09 为准，并同步修订本文。

## 1. Roadmap Goal

V1 的目标不是一次性重写完整旅行 Agent，而是跑通一个可演示、可验证、可继续扩展的新
Runtime 闭环：

```text
collect
  -> prepare_base_context
  -> retrieve_evidence
  -> tool_enrich
  -> domain_plan
  -> integrate
  -> verify
  -> approve_or_revise
  -> finalize
```

V1 成功标准：

```text
用户可以完成一次多轮旅行需求收集
系统可以从 EvidenceCard 知识库取证据
系统可以接入最小实时工具 WeatherTool
三个领域 Planner 可以生成结构化 proposal
Integrator 可以生成 itinerary draft
Judge 可以发现 unsupported claims / blocking issues
审批可以暂停并恢复
finalize 可以生成最终用户消息、itinerary 结果和 order_id
前端可以收到稳定的 RuntimeEvent / token / approval / order / done 事件
```

## 2. Implementation Principle

### Runtime First, Replacement Later

V1 不直接删除旧 graph 主流程。先并行搭建 PlanningRuntime，再通过 adapter 接入现有
chat streaming / approval / itinerary 能力。

```text
Old graph = compatibility path
PlanningRuntime = new source of truth
LangGraph = executor / checkpoint / interrupt layer
StageHandler = business boundary
```

### Minimal Real Closure

每个阶段都必须有真实接口和可测试输出，但不要求每个阶段第一版都具备完整智能能力。

允许：

```text
Planner 使用简化 prompt
Skill runner 先显式注册，不做自动发现
Observability 先写本地 runtime_events，不依赖 LangSmith
WeatherTool 是唯一真实外部工具
EvidenceEngine 先实现 approved EvidenceCard retrieval + sufficiency
```

不允许：

```text
用一个大 node 吞掉 9 个阶段
把旧 TravelState 继续扩成新 RuntimeState
让 Agent 直接调用 MCP / HTTP / SQL
让多个 Planner token 直接交错输出到前端
在 finalize 阶段新增 itinerary 中没有的事实
```

## 3. Priority Definition

### P0: V1 Closure Required

没有这些，V1 新范式无法闭环：

```text
RuntimeState / RuntimeEvent
PlanningRuntime / StageHandler skeleton
LangGraph executor adapter
collect multi-turn compatibility
CollectContext -> PlanningNeed validated boundary
ContextAssembler with visibility enforcement
EvidenceEngine minimal implementation
ToolService with WeatherTool allowlist
DomainPlannerGroup with 3 planner outputs
ItineraryIntegrator
QualityVerifier
approval_required interrupt event
finalize order / itinerary / final message
RuntimeEvent -> existing SSE / WS adapter
core tests for stage contracts
```

### P1: V1 Demo Strongly Recommended

这些能体现新范式质量，但不阻塞第一条可运行链路：

```text
Skill package folders with SKILL.md / schemas.py / runner.py
Prompt version metadata
RuntimeObservability local summary trace
LangSmith optional semantic tracing
anti-hallucination unsupported-claim report
evidence / assumption summary in approval UI
degraded handling for planner / tool / judge failure
```

### P2: V1.5 / V2 Reserved

这些不进入 V1：

```text
retrieval eval metrics
external temporary EvidenceCard
search / map / transport / hotel real-time tools
multi-channel parallel planner token UI
full trace browser UI
dynamic model routing
automatic skill discovery / plugin system
long-term memory auto-writeback
online knowledge ingestion
```

## 4. File Landing Map

V1 不新增仓库顶层目录。新 Runtime 放在 `backend/app/runtime/`。

### Runtime Core

```text
backend/app/runtime/
  __init__.py
  planning_runtime.py
  state.py
  events.py
  manifest.py
  model_profiles.py
```

职责：

```text
planning_runtime.py -> run / resume / dispatch stages
state.py            -> RuntimeState, StageStatus, RuntimeSnapshot
events.py           -> RuntimeEvent, TokenEvent, ApprovalRequiredEvent, DoneEvent
manifest.py         -> V1 stage list, stage capabilities, public visibility policy
model_profiles.py  -> generator / judge / cheap profile names
```

落地难度：中。关键风险是不要把它做成另一个 `TravelState` 大杂烩。

### Stage Handlers

```text
backend/app/runtime/stages/
  collect.py
  prepare_base_context.py
  retrieve_evidence.py
  tool_enrich.py
  domain_plan.py
  integrate.py
  verify.py
  approve_or_revise.py
  finalize.py
```

职责：

```text
每个文件只处理一个 stage
stage 读取 RuntimeState
stage 调用 Runtime service / agent / skill
stage 写回结构化 stage output
stage 发 RuntimeEvent
```

落地难度：中高。风险是把旧 graph node 逻辑原样搬进 stage。

### Executor Adapter

```text
backend/app/runtime/executor/
  langgraph_executor.py
  graph_builder.py
```

职责：

```text
graph_builder.py      -> build 9-stage StateGraph
langgraph_executor.py -> bridge LangGraph events, checkpoint, interrupt, resume
```

现有可参考：

```text
backend/app/graph/builder.py
backend/app/graph/checkpoint.py
backend/app/services/chat_stream.py
```

落地难度：高。主要风险是 streaming、checkpoint 和 human-in-the-loop 恢复。

### Context And Memory

```text
backend/app/runtime/context/
  assembler.py
  specs.py
  schemas.py

backend/app/runtime/memory/
  manager.py
  schemas.py
```

职责：

```text
ContextAssembler -> 按 Agent / Stage 动态组装 AgentContext
ContextSpec      -> 定义每类 Agent 可见上下文，并禁止正式规划读取 raw CollectContext
MemoryManager    -> V1 只读用户偏好 / session facts，不做长期自动写入
```

V1 上下文边界：

```text
CollectContext
  -> PlanningInputCompiler
  -> PlanningInputValidator
  -> user confirmation or explicit draft request
  -> PlanningNeed
  -> prepare_base_context
  -> BaseContext
  -> ContextAssembler
  -> temporary AgentContext
```

正式规划事实使用轻量 provenance：

```text
confirmed
derived
approved_assumption
evidence_supported
tool_observed
```

落地难度：中。关键是 RuntimeState 存结构化事实、不存完整 prompt context，并通过
`ContextSpec` 控制可见性，而不是把整个 RuntimeState 传给 Agent。

### Semantic Collect Migration

```text
backend/app/runtime/collect/
  runtime.py
  schemas.py
  readiness.py
  planning_input.py
  conversation_policy.py

backend/app/runtime/semantic/
  normalizer.py
  slot_binding.py
  collection_frame.py

backend/app/runtime/discovery/
  catalog.py
  matcher.py
  advisor.py
```

职责：

```text
normalizer.py        -> 复用或迁移现有语义归一化规则
slot_binding.py      -> 将用户输入绑定到 TripSpec slots
collection_frame.py  -> 管理 CollectContext 中的多轮收集进度
CollectRuntime       -> 协调单轮收集策略，不展开为 LangGraph nodes
readiness.py         -> HybridReadinessEvaluator
planning_input.py    -> PlanningInputCompiler / PlanningInputValidator
conversation_policy  -> 决定单轮目标、追问或探索策略
runtime/discovery    -> 使用 EvidenceCard 派生目录辅助需求探索
```

落地难度：中高。这里必须兼容并提升现有多轮收集体验，不能退化成一次性抽取或机械
补字段。DiscoveryProfile 的离线投影器归后续 Knowledge Factory 对应 Slice，不在
Slice 3 提前创建。

### Evidence System

```text
backend/app/knowledge/
  evidence_factory.py
  evidence_engine.py
  evidence_repository.py
  evidence_schemas.py
  evidence_report.py
  tokenizers.py
```

职责：

```text
evidence_factory.py    -> offline rebuild: extract, hard rules, dedupe, verifier, index
evidence_engine.py     -> online retrieval: vector + BM25 + RRF + hydration + sufficiency
evidence_repository.py -> PostgreSQL access through repository boundary
evidence_schemas.py    -> SourceDocument / DocumentChunk / EvidenceCard runtime schemas
evidence_report.py     -> build report
tokenizers.py          -> ChineseTokenizer protocol and JiebaTokenizer adapter
```

现有可复用：

```text
backend/app/knowledge/document_loader.py
backend/app/knowledge/document_splitter.py
backend/app/knowledge/vector_store.py
backend/app/knowledge/hybrid_retriever.py
backend/app/knowledge/parent_store.py
```

落地难度：高。这里涉及数据模型、索引重建和检索对象从 chunk 到 EvidenceCard 的迁移。

当前 `jieba==0.42.1` 会通过 `pkg_resources` 产生 setuptools 废弃警告。Runtime
Skeleton 阶段允许该非阻塞警告，不修改依赖、不全局屏蔽。进入 EvidenceEngine Slice
时必须通过 `ChineseTokenizer` 边界隔离 Jieba，并用中文分词与 BM25 检索回归测试验证
未来替换能力。

### ToolService

```text
backend/app/runtime/tools/
  service.py
  schemas.py
  weather_tool.py
```

职责：

```text
service.py      -> allowlist, timeout, fallback, ToolContext write
schemas.py      -> ToolRequest / ToolResult / ToolContext
weather_tool.py -> adapter over backend/app/tools/weather.py
```

V1 只 allowlist：

```text
WeatherTool
date / holiday deterministic helpers
```

落地难度：中。难点不是调用工具，而是限制工具边界和失败降级。

### Agents And Skills

```text
backend/app/runtime/agents/
  base.py
  registry.py
  collect_agent.py
  destination_planner.py
  route_transport_activity_planner.py
  stay_food_planner.py
  itinerary_integrator.py
  revision_agent.py

backend/app/runtime/skills/
  registry.py
  extract_trip_spec/
  clarify_requirements/
  compose_destination_strategy/
  compose_route_transport_activity/
  compose_stay_food/
  merge_domain_proposals/
  resolve_plan_conflicts/
  build_itinerary_draft/
  judge_itinerary_quality/
  classify_revision_feedback/
  revise_itinerary_with_quality_report/
  revise_itinerary_with_user_feedback/
  generate_final_response/
```

V1 规则：

```text
Agent = 角色责任
Skill = 可复用能力包
Prompt = 语言模板
Skill 不直接持久化数据
Agent 不直接访问 DB / MCP / HTTP
```

落地难度：中高。风险是 Skill 目录变成形式主义，所以 V1 只实现真正被 stage 调用的
runner。

### Prompts

```text
backend/app/ai/prompts/runtime/
  agents/
    collect_agent.md
    destination_planner.md
    route_transport_activity_planner.md
    stay_food_planner.md
    itinerary_integrator.md
    revision_agent.md

  skills/
    extract_trip_spec.md
    clarify_requirements.md
    compose_destination_strategy.md
    compose_route_transport_activity.md
    compose_stay_food.md
    merge_domain_proposals.md
    resolve_plan_conflicts.md
    build_itinerary_draft.md
    judge_itinerary_quality.md
    classify_revision_feedback.md
    revise_itinerary_with_quality_report.md
    revise_itinerary_with_user_feedback.md
    generate_final_response.md
```

落地难度：中。重点是 prompt 与 skill 分离，且每个 prompt 都有明确输入 schema。

### Quality And Finalization

```text
backend/app/runtime/quality/
  verifier.py
  schemas.py

backend/app/runtime/finalization/
  final_response.py
  order_service.py
  schemas.py
```

职责：

```text
QualityVerifier -> generator output + judge output + blocking decision
FinalResponse   -> 用户可见最终回复，不新增事实
OrderService    -> 生成或复用 order_id，持久化 itinerary 关联
```

现有可参考：

```text
backend/app/services/itinerary_service.py
backend/app/services/approval_service.py
backend/app/db/repositories/itinerary_repository.py
backend/app/ai/prompts/final_response.md
```

落地难度：高。风险是 order、itinerary、final message、前端事件分散在多个层里。

### Streaming And Transport Adapter

```text
backend/app/services/runtime_chat_stream.py
backend/app/ws/chat_stream.py
backend/app/api/v1/chat.py
```

职责：

```text
runtime_chat_stream.py -> merge RuntimeEvent + public token stream
ws/chat_stream.py      -> 保持现有 WebSocket 入口，切换到 Runtime adapter
api/v1/chat.py         -> SSE 入口如存在，同样使用 Runtime adapter
```

现有可参考：

```text
backend/app/services/chat_stream.py
backend/tests/test_chat_stream.py
```

落地难度：高。V1 只公开一个主 token owner，不交错输出多个 planner token。

### Database

```text
backend/app/db/models/
backend/app/db/repositories/
backend/alembic/versions/
docs/database.md
```

V1 推荐三批 migration：

```text
0003 knowledge evidence cards
0004 runtime observability
0005 runtime result links
```

落地难度：高。规则是不做破坏式迁移，不删除旧表，不要求回填旧会话 trace。

## 5. Phase Plan

### Phase 0: Documentation Freeze

目标：让实现前没有明显架构漂移。

产物：

```text
09 blueprint confirmed
10 roadmap confirmed
README index updated
implementation cutline confirmed
```

验收：

```text
01-08 不再和 V1 主流程产生误导
09 和 10 对 V1 / V1.5 / V2 归属一致
```

落地难度：低。

### Phase 1: Runtime Skeleton

目标：建立 9 阶段可运行空骨架。

实现：

```text
RuntimeState
RuntimeEvent
PlanningRuntime.run()
StageHandler protocol
9 stage handlers with minimal outputs
LangGraph executor adapter
runtime event stream adapter
```

最小行为：

```text
输入用户消息
依次进入 9 个 stage
每个 stage 发 stage_started / stage_completed
finalize 发 done
```

验收：

```text
unit: RuntimeState 初始化和 stage output 写入
unit: RuntimeEvent public/private visibility
integration: Runtime happy path emits 9 stage events in order
```

落地难度：中。

### Phase 2: Collect And Context

目标：迁移多轮收集，不降低现有首轮和追问体验。

实现：

```text
GreetingPolicy / GreetingResponder
CollectSemanticLayer
TripSpecExtractorSkill
CollectRuntime
DiscoveryHypothesis lifecycle
HybridReadinessEvaluator
ConversationPolicyPlanner / ConversationResponseGenerator
PlanningInputCompiler / PlanningInputValidator
PlanningNeed
ContextAssembler
ContextSpec
```

最小行为：

```text
首轮 greeting 不误触规划
缺少核心字段时可自然探索或追问，并停留在 collect
用户补充信息后 RuntimeState.collect_context 更新 TripSpec
未确认的 DiscoveryHypothesis 不进入 PlanningNeed
用户确认或明确要求先出一版后，才能生成 PlanningNeed
prepare_base_context 只根据 PlanningNeed 生成 BaseContext
正式规划 Agent 不读取 raw CollectContext
```

验收：

```text
semantic rules run before LLM extraction
pending clarification resumes correctly
vague confirmation does not fill missing slots
PlanningInputCompiler does not invent missing facts
approved assumptions retain provenance
formal planning ContextSpec rejects raw CollectContext
RuntimeState does not store full prompt text
```

落地难度：中高。

### Phase 3: Knowledge Factory And EvidenceEngine

目标：让 Runtime 能消费 EvidenceCard，而不是旧 chunk RAG。

实现：

```text
EvidenceCard schema / repository
KnowledgeFactory rebuild / query / inspect-card
EvidenceEngine retrieval
ChineseTokenizer protocol + JiebaTokenizer adapter
sufficiency_result
EvidenceContext
```

最小行为：

```text
只检索 approved EvidenceCard
Chroma + BM25 + RRF 返回 evidence_card_id
PostgreSQL hydration 返回结构化 EvidenceCard
证据不足时 suggested_action = mark_assumptions_and_continue
```

验收：

```text
retrieves approved cards only
returns sufficiency_result
marks assumptions when evidence is insufficient
does not call external search in V1
isolates Chinese tokenization behind ChineseTokenizer
passes Chinese tokenization and BM25 retrieval regression tests
```

落地难度：高。

### Phase 4: ToolService

目标：验证 Runtime 工具边界。

实现：

```text
ToolService
ToolContext
WeatherTool adapter
date / holiday deterministic helper access
tool timeout / unavailable fallback
```

最小行为：

```text
tool_enrich 调 WeatherTool
天气可用时写入 ToolContext.weather
天气不可用时写入 degraded status
Planner 和 Judge 能看到 weather summary / risks
```

验收：

```text
WeatherTool writes ToolContext.weather
unavailable weather does not block planning
non-allowlisted tools are rejected
```

落地难度：中。

### Phase 5: Multi-Agent Planning

目标：替换旧 plan_* 节点式逻辑。

实现：

```text
DestinationPlanner
RouteTransportActivityPlanner
StayFoodPlanner
DomainPlannerGroup
PlanProposal schema
ItineraryIntegrator
```

最小行为：

```text
DestinationPlanner 先给目的地策略
RouteTransportActivityPlanner 和 StayFoodPlanner 可并行
三个 planner 输出 PlanProposal
Integrator 合并为 itinerary draft
```

验收：

```text
DestinationPlanner runs before parallel planners
parallel planners do not emit public interleaved token stream
PlanProposal contains evidence ids and assumptions
Integrator does not invent unsupported activities
```

落地难度：高。

### Phase 6: Quality, Revision, And Anti-Hallucination

目标：让生成质量由 Judge 阻断，而不是只靠 prompt 自觉。

实现：

```text
QualityVerifier
Judge model profile
QualityReport
RevisionAgent
max_auto_revision = 1
unsupported claim detector
```

最小行为：

```text
Judge 标记 blocking issue
系统自动修订一次
第二次仍失败时不静默通过
质量报告进入 approval summary
```

验收：

```text
blocking issue triggers one revision
unsupported claims are flagged
second failure is surfaced to user or approval layer
```

落地难度：中高。

### Phase 7: Approval, Finalize, And Persistence

目标：补齐用户旅程最后一步。

实现：

```text
approve_or_revise stage
approval_required RuntimeEvent
FinalResponseGenerator
OrderService
itinerary persistence adapter
order / done events
```

最小行为：

```text
审批前暂停
用户确认后进入 finalize
finalize 生成或复用 order_id
itinerary 写入现有 itinerary 表或关联结构
最终用户消息只总结已确认行程
前端收到 order -> done
```

验收：

```text
approved itinerary persists exactly once
order_id generated or reused exactly once
final message does not invent new facts
order / done events are emitted in stable order
```

落地难度：高。

### Phase 8: Streaming / Frontend Adapter

目标：保持核心用户体验。

实现：

```text
RuntimeEvent -> SSE / WS adapter
public token owner policy
approval_required transport
frontend runtime event display
finalize display text
```

最小行为：

```text
前端展示阶段进度
前端展示主回复 token
审批卡片可显示 itinerary / evidence summary / assumptions
用户确认或修改通过结构化事件返回
```

验收：

```text
RuntimeEvent maps to existing event contract
parallel planners do not interleave public token stream
approval_required pauses and resumes via structured event
```

落地难度：高。

### Phase 9: Old Flow Retirement

目标：V1 demo 稳定后切主路径。

前置条件：

```text
KnowledgeFactory demo works
PlanningRuntime happy path works
collect pause/resume works
EvidenceContext enters planning
WeatherTool degradation works
Judge blocking revision works
finalize emits order and done
frontend consumes RuntimeEvent
core regression cases pass
```

动作：

```text
保留旧 graph 兼容入口
新 chat path 默认走 PlanningRuntime
旧 graph node order 测试改为兼容测试或退休
docs/architecture.md 更新为 Runtime 主路径
```

落地难度：中高。

## 6. Suggested First Implementation Slice

第一刀不要从最复杂的 EvidenceEngine 或 streaming 开始。推荐顺序：

```text
Slice 1: RuntimeState + RuntimeEvent + 9 stage skeleton
Slice 2: LangGraph executor adapter + event stream adapter
Slice 3: intelligent collect migration + PlanningNeed boundary + ContextAssembler
Slice 4: EvidenceEngine minimal fake/repository-backed retrieval
Slice 5: ToolService WeatherTool
Slice 6: DomainPlannerGroup + Integrator
Slice 7: QualityVerifier + RevisionAgent
Slice 8: approval/finalize/persistence
Slice 9: frontend event adapter
```

Slice 1 的目标是先证明新范式能运行起来：

```text
POST / chat or WS message
  -> PlanningRuntime
  -> 9 stage RuntimeEvents
  -> done
```

此时每个 stage 可以输出最小结构，但接口必须与后续真实实现一致。

## 7. Implementation Cutline

### V1 Must Implement

```text
Runtime skeleton
multi-turn collect compatibility
ContextAssembler
EvidenceEngine minimal retrieval
WeatherTool ToolService
3 Planner DomainPlannerGroup
Integrator
Judge verifier
single auto revision
approval interrupt
finalize order / itinerary / final response
RuntimeEvent transport adapter
core tests
```

### V1 Can Stub Internally

```text
Planner prompt quality can be simple
Skill registry can be explicit
LangSmith can be no-op when disabled
KnowledgeFactory can start with small local dataset
EvidenceEngine can use small approved EvidenceCard fixture before full rebuild CLI is complete
```

### V1 Must Not Implement

```text
external temporary evidence
retrieval eval metrics
real map / POI / transport / hotel supply tools
automatic long-term memory writeback
multi-model voting beyond generator + judge
full trace UI
dynamic model routing
```

## 8. Test Plan Summary

V1 测试不追求覆盖所有旧系统细节，而是覆盖新 Runtime 的边界。

```text
backend/tests/runtime/
  test_runtime_state.py
  test_runtime_events.py
  test_context_assembler.py
  test_collect_stage.py
  test_planning_input.py
  test_evidence_engine.py
  test_tool_service.py
  test_domain_planner_group.py
  test_quality_verifier.py
  test_finalize_stage.py
  test_runtime_stream_adapter.py
```

保留旧测试：

```text
backend/tests/test_chat_stream.py
backend/tests/test_checkpoint.py
backend/tests/test_approval_router.py
```

迁移旧测试：

```text
collect_requirements tests -> runtime collect tests
approval/final_response tests -> approve_or_revise/finalize tests
graph node order tests -> compatibility tests, not product truth
```

V1 不要求：

```text
full retrieval eval metrics
LangSmith dataset experiments
golden answer scoring
browser trace UI tests
```

## 9. Risk Register

| 风险 | 影响 | V1 控制方式 |
|------|------|-------------|
| RuntimeState 变成第二个 TravelState | 新架构失去意义 | RuntimeState 只存结构化事实、stage outputs、event refs |
| collect 被简化成一次性抽取或机械补字段 | 首轮体验倒退 | CollectRuntime 保留 semantic rules、探索假设、自然策略和多轮恢复 |
| 未确认假设污染正式规划 | 产生幻觉或错误约束 | PlanningNeed 是唯一正式输入，ContextSpec 禁止 Planner 读取 raw CollectContext |
| assumption 被伪装为用户事实 | Judge 无法识别风险 | 正式规划事实保留轻量 provenance |
| EvidenceEngine 被旧 RAG 混用 | RAG 边界不清 | PlanningRuntime 只消费 EvidenceCard / EvidenceContext |
| ToolService 挂回所有旧 MCP | V1 范围失控 | allowlist 只开 WeatherTool 和 deterministic helpers |
| 并行 Planner token 交错 | 前端体验混乱 | V1 只公开主 token owner，Planner 发 progress event |
| finalize 分散在 stream / graph / service | 订单与最终回复不一致 | finalize stage 统一生成 final response / order / done |
| Judge 只做装饰 | 质量验证无效 | blocking issue 必须触发一次 revision 或显式降级 |
| DB migration 破坏旧流程 | 现有功能回归 | V1 只新增，不删除，不强制回填 |

## 10. Next Planning Artifact

本文确认后，下一份文档应进入更细的任务拆分：

```text
11-v1-runtime-skeleton-implementation-plan.md
```

Slice 1/2 实施计划：[11-v1-runtime-skeleton-implementation-plan.md](11-v1-runtime-skeleton-implementation-plan.md)（已完成）。

Slice 3 实施计划：[12-v1-collect-context-implementation-plan.md](12-v1-collect-context-implementation-plan.md)（已完成）。

Slice 4 实施计划：[13-v1-evidence-engine-implementation-plan.md](13-v1-evidence-engine-implementation-plan.md)。

11 只覆盖 Slice 1 和 Slice 2：

```text
RuntimeState
RuntimeEvent
PlanningRuntime skeleton
9 stage handlers
LangGraph executor adapter
runtime stream adapter
basic tests
```

原因：这两个 Slice 是所有后续能力的承载面。先把运行时骨架和事件通路跑起来，再迁移
collect、evidence、tool 和 multi-agent，会更稳。
