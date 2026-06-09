# RAG Agent Refactor Design

本目录记录 Travel Agent 下一阶段的 RAG Agent 范式升级方案。目标不是简单把文档放进向量库，而是构建一套可解释、可评估、可观测的旅行规划知识系统，让 Agent 在行程编排时基于结构化证据做决策。

## 设计目标

- 以 RAG 为项目主线，突出面试展示价值。
- 从传统固定流程应用升级为 Agentic RAG 架构。
- 将知识库设计为可生产、可审核、可检索、可评测的工程体系。
- 将 V1 CLI 定位为本地知识构建与查询工作台，V1.5 扩展为检索评测工作台。
- 第一版控制范围，避免过早引入复杂增量更新和长期外部知识沉淀。

## 文档层级

本目录中的文档分为两个层级：

```text
01-08 = RAG / EvidenceCard / 在线检索流程的局部设计
09 = PlanningRuntime 新内核的 V1 架构蓝图
10 = V1 实施路线图和落地切片
11+ = 按切片拆分的实施计划（11 = Runtime Skeleton，12 = Collect & Context，13 = EvidenceEngine）
```

当 `06-agent-flow-context.md` 或 `08-v1-scope.md` 中的旧式线上流程与
`09-planning-runtime-blueprint.md` 冲突时，以 `09` 为准。`06` 仍作为
TripSpec、需求成熟度、EvidenceContext 和 RAG 节点边界的背景设计参考。
`10-v1-implementation-roadmap.md` 不替代 09 的架构定义，只说明 V1 如何分阶段落地。
`11-v1-runtime-skeleton-implementation-plan.md` 是第一份实施计划，只覆盖 Runtime
Skeleton 与 LangGraph / streaming adapter，不进入 collect、Evidence、Tool 或多 Agent
实现。

## 文件说明

| 文件 | 内容 |
|------|------|
| [01-overview.md](01-overview.md) | 总体架构、分阶段目标和核心取舍 |
| [02-knowledge-model.md](02-knowledge-model.md) | SourceDocument、DocumentChunk、EvidenceCard 三层知识结构 |
| [03-storage-design.md](03-storage-design.md) | PostgreSQL、Chroma、BM25、data 目录的物理存储设计 |
| [04-offline-pipeline-cli.md](04-offline-pipeline-cli.md) | 离线全量构建、EvidenceCard 抽取、归一化、去重、审核、构建报告和 CLI |
| [05-hybrid-retrieval-eval.md](05-hybrid-retrieval-eval.md) | EvidenceCard 主检索、Chroma + BM25 + RRF、V1.5 retrieval eval |
| [06-agent-flow-context.md](06-agent-flow-context.md) | 线上 Agent 流程、意图挖掘、RAG 节点、PlanningEvidenceContext |
| [07-external-temporary-evidence.md](07-external-temporary-evidence.md) | 本地证据不足时的外部检索与 temporary EvidenceCard 方案 |
| [08-v1-scope.md](08-v1-scope.md) | V1/V1.5/V2 范围边界和暂不实现项 |
| [09-planning-runtime-blueprint.md](09-planning-runtime-blueprint.md) | PlanningRuntime 新内核、Memory/Context、Skill/Prompt、多 Agent、工具、质量验证和可观测性蓝图 |
| [10-v1-implementation-roadmap.md](10-v1-implementation-roadmap.md) | V1 落地路线、文件落点、优先级、阶段切片、验证策略和风险控制 |
| [11-v1-runtime-skeleton-implementation-plan.md](11-v1-runtime-skeleton-implementation-plan.md) | RuntimeState、RuntimeEvent、9 阶段骨架、LangGraph executor adapter 和 runtime stream adapter 的实施计划 |
| [12-v1-collect-context-implementation-plan.md](12-v1-collect-context-implementation-plan.md) | Collect 迁移、PlanningNeed 边界、ContextAssembler 和 prepare_base_context 的 Slice 3 实施计划（**已完成**） |
| [13-v1-evidence-engine-implementation-plan.md](13-v1-evidence-engine-implementation-plan.md) | EvidenceCard 检索、EvidenceEngine、ChineseTokenizer 和 retrieve_evidence 的 Slice 4 实施计划 |

## 当前定稿结论

第一版采用以下策略。长期知识库仍由离线全量构建生成：

```text
离线全量构建长期知识库
  SourceDocument
    -> Parent/Child DocumentChunk
    -> EvidenceCard
    -> 归一化
    -> 硬规则校验
    -> 去重
    -> LLM 审核
    -> PostgreSQL + Chroma + BM25
```

线上规划以 `PlanningRuntime` 为新内核，V1 主流程为：

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

其中 LangGraph 作为执行引擎负责阶段编排、checkpoint、streaming 和
interrupt/resume；具体业务能力由 PlanningRuntime 的 Memory、Context、Evidence、
Tool、Skill、Agent、Quality 和 Observability 组件承载。

如果本地证据不足，V1 继续规划但显式标记假设，并由 Judge 严格检查。V1.5 才生成
temporary EvidenceCard 参与当前会话，不沉淀长期库。长期知识库仍由 CLI 全量重建
生成，保证可复现和易评测。
