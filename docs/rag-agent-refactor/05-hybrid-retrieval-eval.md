# Hybrid Retrieval And Eval

## 检索对象优先级

第一版线上主检索对象：

```text
EvidenceCard
```

优先级：

```text
1. EvidenceCard retrieval
2. DocumentChunk retrieval reserved as future fallback
3. SourceDocument only for traceability
```

原因：

- EvidenceCard 是结构化决策证据。
- DocumentChunk 是来源和补充上下文。
- SourceDocument 是原始来源，不直接参与线上规划检索。

## Hybrid Retrieval

第一版采用：

```text
Chroma vector retrieval
  + BM25 keyword retrieval
  + metadata filter
  + RRF fusion
```

流程：

```text
PlanningNeed
  -> QueryAnalyzer
  -> metadata filter
  -> vector retrieve EvidenceCards
  -> BM25 retrieve EvidenceCards
  -> RRF fusion by evidence_card_id
  -> PostgreSQL hydrate EvidenceCards
  -> ContextAssembler
```

## Vector Retriever

负责语义匹配：

```text
不想太累
适合父母
第一次到访
喜欢文化街区
低强度三日游
```

检索文本使用 EvidenceCard 的 `embedding_text`。

## BM25 Retriever

负责关键词和实体命中：

```text
武侯祠
锦里
熊猫基地
春熙路
2 号线
半日
```

中文 BM25 第一版可用：

```text
jieba + rank_bm25
```

## Metadata Filter

必须保留：

```text
city
evidence_type
status = approved
valid_until
```

否则容易出现跨城市、过期或未审核证据污染。

## RRF 融合

第一版使用 Reciprocal Rank Fusion：

```text
score = sum(1 / (k + rank_i))
```

优点：

- 不要求 vector score 和 BM25 score 同分布。
- 简单稳定。
- 适合融合多个 rank list。

融合时必须按 `evidence_card_id` 去重：

```text
vector hits: [A, B, C]
bm25 hits: [C, D, A]
RRF result: [A, C, B, D]
```

## Evidence Sufficiency Check

V1 需要基础充足度判断，用于决定是否证据足够支撑规划。

不要只看 EvidenceCard 标签总数。应根据 PlanningNeed 覆盖率判断。

输入：

```json
{
  "city": "成都",
  "duration": 3,
  "must_visit": ["熊猫基地", "武侯祠", "锦里"],
  "preferences": ["美食", "低强度"],
  "required_evidence_types": [
    "route_relation",
    "time_intensity",
    "food_option",
    "area_strategy"
  ]
}
```

指标：

```text
card_count
evidence_type_coverage
need_tag_coverage
confidence_floor
```

输出：

```json
{
  "is_sufficient": false,
  "score": 0.58,
  "missing_tags": ["熊猫基地", "time_intensity"],
  "missing_evidence_types": ["time_intensity"],
  "suggested_action": "mark_assumptions_and_continue"
}
```

V1 证据不足时不触发外部检索。系统继续规划，但必须显式标记假设并交给 Judge 检查。
`external_search` 是 V1.5 的动作。

## Retrieval Eval

Retrieval Eval 不进入 V1 Runtime 闭环，放到 V1.5。V1 只要求线上
`EvidenceEngine` 返回可解释的 `EvidenceContext` 和 `sufficiency_result`。

V1.5 只做 retrieval 指标，不做 answer 指标，不做场景诊断指标。

评估对象：

```text
EvidenceCard retrieval
```

对比 retriever：

```text
vector
bm25
rrf
```

核心指标：

```text
Hit@K
Recall@K
MRR@K
nDCG@K
```

K：

```text
5
10
```

## Eval Case

测试集可由 LLM 生成 query，但 ground truth 必须 evidence-grounded。

推荐结构：

```json
{
  "id": "case_chengdu_food_low_intensity_001",
  "query": "成都三天，不想太累，主要想吃和逛",
  "relevant_evidence_card_ids": [
    "ev_chengdu_food_001",
    "ev_chengdu_area_003",
    "ev_chengdu_intensity_002"
  ],
  "source_evidence_card_ids": [
    "ev_chengdu_food_001",
    "ev_chengdu_area_003",
    "ev_chengdu_intensity_002"
  ],
  "generation_method": "llm_from_evidence_cards",
  "review_status": "auto_approved"
}
```

V1.5 不标：

```text
expected_retrieval_mode
query_type
场景诊断标签
answer quality
```

## Eval 报告

推荐位置：

```text
data/exports/rag_eval_reports/
```

报告输出：

```text
| Retriever | Hit@5 | Recall@5 | MRR@5 | nDCG@5 | Hit@10 | Recall@10 | MRR@10 | nDCG@10 |
|-----------|------:|---------:|------:|-------:|-------:|----------:|-------:|--------:|
| Vector    | ...   | ...      | ...   | ...    | ...    | ...       | ...    | ...     |
| BM25      | ...   | ...      | ...   | ...    | ...    | ...       | ...    | ...     |
| RRF       | ...   | ...      | ...   | ...    | ...    | ...       | ...    | ...     |
```

Eval 报告回答：

```text
混合检索是否比单路检索更稳定。
EvidenceCard 检索是否能命中目标证据。
```
