# Offline Pipeline And CLI

## CLI 定位

第一版 CLI 优先做本地任务批处理，而不是外部工具调用。

定位：

```text
RAG 知识生产与检索评测工作台
```

它服务于开发者和面试展示：

- 重建知识库。
- 查看构建统计。
- 调试一次 query 的 hybrid retrieval。
- 查看 EvidenceCard 来源。
- V1.5 运行 retrieval eval。

## 推荐命令

```bash
travel-agent knowledge rebuild
travel-agent knowledge query "成都三天不想太累，喜欢美食"
travel-agent knowledge inspect-card ev_chengdu_route_001
# V1.5
travel-agent knowledge eval
```

如果第一版不引入正式 CLI 框架，也可以用脚本承载同等能力：

```bash
python backend/scripts/rebuild_knowledge.py
python backend/scripts/query_knowledge.py
python backend/scripts/inspect_evidence_card.py
python backend/scripts/eval_rag_retrieval.py
```

## knowledge rebuild

V1 默认全量重建。

流程：

```text
scan data/documents
  -> load SourceDocument
  -> write documents
  -> split parent chunks
  -> split child chunks
  -> write document_chunks
  -> extract candidate EvidenceCards from parent chunks
  -> normalize
  -> hard rule verification
  -> dedupe
  -> LLM verifier
  -> write approved/pending/rejected evidence_cards
  -> rebuild Chroma evidence_cards collection
  -> rebuild BM25 index
  -> generate build report
```

## EvidenceCard 抽取

V1 使用：

```text
prompt file + structured output + Pydantic schema
```

推荐位置：

```text
backend/app/ai/prompts/evidence_card_extraction.md
backend/app/knowledge/evidence_extractor.py
backend/app/knowledge/schemas.py
```

不建议 V1 做成 skill。理由：

- 抽取是稳定后端任务，不是开放式 Agent 行为。
- 需要 schema 约束。
- 需要可复现、可批处理、可评估。

抽取要求：

```text
只允许基于输入 parent chunk 抽取
每张卡必须有 raw_quote
每张卡必须有 evidence_type
不能生成没有来源支持的常识
每个 parent chunk 可抽取 0 到 N 张卡
```

## 去重

顺序：

```text
extract
  -> normalize
  -> hard rule verification
  -> rule dedupe
  -> embedding near-duplicate detection
  -> LLM verification
```

### Claim 归一化

处理：

```text
去标点和多余空格
统一同义表达
统一景点别名
entities 排序
规范 evidence_type、time_hint、intensity
```

生成 dedupe key：

```text
city + evidence_type + canonical_entities + time_hint/intensity
```

如果 key 接近，再计算 claim 相似度：

```text
token overlap
rapidfuzz token_set_ratio
char n-gram Jaccard
```

建议：

```text
同 city
同 evidence_type
entities 高度重合
claim similarity > 0.88
  -> duplicate
```

### Embedding 去重

流程：

```text
new EvidenceCard embedding
  -> search topK within same city/evidence_type
  -> cosine similarity
  -> combine with entities/rules
```

建议阈值：

```text
>= 0.92: highly duplicate
0.85 - 0.92: near duplicate
< 0.85: not duplicate
```

Embedding 去重只作为近重复信号，不能单独决定合并。

## 自动审核

顺序：

```text
hard rules
  -> dedupe
  -> LLM verifier
  -> final status rules
```

### 硬规则

适合判断：

```text
schema 是否合法
claim 是否为空
raw_quote 是否为空
source_chunk_id 是否存在
evidence_type 是否合法
city 是否存在
entities 是否为空
confidence 是否低于阈值
valid_until 是否明显过期
```

### LLM verifier

适合判断：

```text
claim 是否被 raw_quote 支撑
claim 是否过度推断
evidence_type 是否语义合理
是否适合进入旅行规划知识库
```

LLM verifier 不直接拍板，而是输出结构化判断和分数。

### 状态

```text
明显失败 -> rejected
规则通过 + verifier 高分 -> approved
规则通过 + verifier 不确定 -> pending_review
```

## 构建报告

`knowledge rebuild` 默认生成 Markdown + JSON 报告。

推荐位置：

```text
data/exports/knowledge_build_reports/
```

报告内容：

```text
Build Summary
Source Documents
Chunking
Evidence Extraction
Deduplication
Verification
Indexing
Quality Signals
Samples
Warnings
Errors
```

示例指标：

```text
documents_scanned
parent_chunks
child_chunks
candidate_cards
deduped_cards
approved_cards
rejected_cards
pending_review_cards
chroma_indexed
bm25_indexed
cards_with_raw_quote_rate
average_confidence
```

构建报告回答：

```text
知识库是如何被构建出来的，质量如何，哪些地方失败或不确定。
```
