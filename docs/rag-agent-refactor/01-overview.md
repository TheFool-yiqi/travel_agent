# Overview

## 背景问题

当前 Travel Agent 的基础流程已经具备 LangGraph、多轮收集、分域规划和审批能力，但整体更像传统流程应用：

- 流程固定，Agent 的自主判断和证据驱动不足。
- RAG 更像普通文档检索，没有形成可复用的决策证据层。
- Prompt、CLI、MCP、评测和知识生产管线没有形成统一架构叙事。
- 本地知识库价值不清晰，容易和外部检索重复。

本次重构目标是做一次范式升级：把项目从“旅行规划应用”升级为“以 RAG 为核心的 Agent 工程展示项目”。

## 核心定位

项目展示重点：

```text
RAG 主线
  + Agent 工作流
  + CLI 本地批处理
  + Hybrid Retrieval
  + EvidenceCard 决策证据
  + Retrieval Eval
  + 外部临时证据补充
```

RAG 不作为万能模块，而只用于知识密集型决策环节：

| 环节 | 推荐方式 |
|------|----------|
| 用户需求抽取 | LLM structured output + rules |
| 需求成熟度判断 | rules + LLM judge 可选 |
| 行程编排 | EvidenceCard RAG 核心使用场景 |
| 行程验证 | V1 预留，后续可做 EvidenceCard RAG |
| 实时信息 | MCP/tools/API，不进入长期 RAG |
| 业务约束 | Pydantic/schema/service rules |

## 总体架构

```text
data/documents or external sources
  -> SourceDocument
  -> Parent/Child DocumentChunk
  -> EvidenceCard extraction
  -> dedupe
  -> auto verification
  -> PostgreSQL authoritative store
  -> Chroma vector index
  -> BM25 keyword index

user conversation
  -> TripSpec extraction
  -> completeness check
  -> retrieve_planning_evidence
  -> EvidenceCard hybrid retrieval
  -> sufficiency check
  -> PlanningEvidenceContext
  -> itinerary planner
```

## 关键取舍

### EvidenceCard 为主，而不是普通 Chunk 为主

旅行规划不是普通文档问答。用户真正需要的是：

```text
景点能否组合
路线是否顺路
强度是否合适
区域如何安排
偏好是否匹配
```

这些更适合沉淀为结构化 EvidenceCard。DocumentChunk 保留为来源、抽取上下文和后续 fallback 支撑层。

### V1 采用全量构建，不做增量长期沉淀

全量构建更适合第一版：

- 状态干净。
- 易复现。
- 易生成构建报告。
- 易做 retrieval eval。
- 避免增量索引一致性、审核继承和局部更新复杂度。

### 外部检索先只做 temporary evidence

当本地证据不足时，外部检索可以补充当前会话，但 V1.5 不沉淀长期库。原因是长期库当前由全量构建维护，在线沉淀会引入增量更新问题。

## 推荐分层

遵守现有后端分层：

```text
graph/nodes
  -> services
  -> knowledge
  -> ai/prompts
  -> tools/mcp
  -> db/repositories
```

RAG 相关逻辑应主要放在：

```text
backend/app/knowledge/
backend/app/ai/prompts/
backend/app/services/
backend/scripts/ or CLI entry
backend/app/db/models/
backend/app/db/repositories/
```

LangGraph 节点只负责状态编排，不直接写 SQL、不直接调用外部 HTTP。

