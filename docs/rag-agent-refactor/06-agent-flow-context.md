# Agent Flow And Context

> Status: 本文是 PlanningRuntime 蓝图形成前的线上 RAG 流程设计说明。它仍用于说明
> TripSpec、需求成熟度判断、EvidenceContext 和 RAG 节点边界。V1 线上主流程以
> [09-planning-runtime-blueprint.md](09-planning-runtime-blueprint.md) 为准。
> 若本文中的 `retrieve_planning_evidence -> build_itinerary` 流程与 09 冲突，以 09
> 的 PlanningRuntime 8 阶段流程为准。

## 核心原则

线上 Agent 不应该用户一说旅行就直接生成完整行程。应先抽取用户意图，判断需求成熟度，再进入 RAG 编排。

早期简化流程如下。该流程不再作为 V1 线上主流程，只保留为 TripSpec 与
EvidenceContext 进入规划前的设计背景：

```text
user message
  -> TripSpec extraction
  -> completeness check
  -> if insufficient: ask follow-up
  -> if sufficient: retrieve_planning_evidence
  -> build_itinerary
  -> approval
```

## TripSpec

TripSpec 是用户需求的结构化表示。

推荐字段：

```text
destination
duration
start_date
budget
travelers
interests
must_visit
avoid
travel_style
intensity_preference
departure_city
constraints
```

抽取方式：

```text
LLM structured output
  + rules fallback
  + schema validation
```

这一步不使用 RAG。

## 需求成熟度判断

最低进入行程编排条件可设计为：

```text
destination 明确
duration 明确
interest 或 must_visit 至少一个明确
travelers 或 travel_style 或 intensity_preference 至少一个明确
```

不足时不进入 `retrieve_planning_evidence`，而是追问用户。

示例：

```text
用户：我想出去玩几天
系统：不直接生成行程，先询问目的地偏好、天数、预算或旅行风格。
```

## retrieve_planning_evidence 节点边界

早期设计中，RAG 作为独立 LangGraph 节点，而不是藏在 `build_itinerary` 内部。
在 09 的 PlanningRuntime 蓝图中，该职责升级为 `retrieve_evidence` 阶段，由
`EvidenceEngine` 承载检索、证据充足度和 EvidenceContext 输出。

推荐流程：

```text
plan_activities
  -> retrieve_planning_evidence
  -> build_itinerary
```

节点职责：

```text
读取 TravelState 中的 TripSpec / PlanningNeed
调用 KnowledgeRetrievalService
写入 state.planning_evidence
写入 sufficiency result
```

节点不直接：

```text
写 SQL
调用 Chroma 细节
调用外部 HTTP
组装复杂 prompt
```

具体逻辑放在：

```text
backend/app/knowledge/
backend/app/services/
```

## PlanningEvidenceContext

线上规划时给 LLM 的上下文采用：

```text
EvidenceCard + supporting chunk summary
```

不直接给完整 parent chunk。

推荐结构：

```json
{
  "query": "成都三天，不想太累，喜欢吃东西",
  "retrieval_mode": "rrf",
  "evidence_cards": [
    {
      "id": "ev_chengdu_route_001",
      "claim": "武侯祠和锦里距离较近，适合组合为半日文化游路线。",
      "evidence_type": "route_relation",
      "entities": ["武侯祠", "锦里"],
      "time_hint": "half_day",
      "intensity": "low",
      "confidence": 0.86,
      "supporting_summary": "来源指出武侯祠和锦里相邻，常被安排一起游览。",
      "source": {
        "document_title": "成都旅行指南",
        "chunk_id": "chunk_chengdu_001_003"
      }
    }
  ],
  "temporary_evidence_cards": [],
  "missing_evidence": [],
  "fallback_used": false
}
```

## Supporting Summary

`supporting_summary` 建议在离线抽取 EvidenceCard 时生成并审核。

原因：

- 线上更快。
- 输出更稳定。
- 可在审核时检查是否被 raw quote 支撑。

EvidenceCard 仍保留：

```text
raw_quote
source_chunk_id
source_document_id
```

用于 inspect-card 和来源追溯。

## Context 控制

V1 建议限制：

```text
Top 6 EvidenceCards
每张 1 条 supporting_summary
最多附少量 raw_quote
总 evidence context 控制在 1200-1800 中文字以内
```

Prompt 要明确：

```text
优先使用 EvidenceCard 中的证据
不要编造未被证据支持的路线关系
证据不足时标记 assumptions
```

## DocumentChunk Fallback

V1 只在架构上预留，不实现复杂线上 fallback。

预留字段：

```json
{
  "supporting_chunks": [],
  "fallback_used": false,
  "missing_evidence": []
}
```

后续可扩展：

```text
EvidenceCard 不足
  -> DocumentChunk retrieval
  -> parent context
  -> temporary evidence
```
