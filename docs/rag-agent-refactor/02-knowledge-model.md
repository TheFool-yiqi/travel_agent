# Knowledge Model

本方案采用三层知识结构：

```text
SourceDocument
  -> DocumentChunk
  -> EvidenceCard
```

三层不是重复存储，而是分别承担来源审计、文档定位和 Agent 决策。

## SourceDocument

SourceDocument 是来源层，负责记录一份资料从哪里来、何时获得、如何追溯。

典型来源：

- 本地 markdown 文档。
- 外部搜索结果落地页快照。
- 后续可能接入的第三方文档服务。

推荐字段：

```text
id
title
source_type
source_url
local_path
city
domain
checksum
retrieved_at
created_at
updated_at
```

说明：

- 原始或清洗后的文档内容可以存放在 `data/documents/`。
- PostgreSQL 的 `documents` 表存元数据和可追溯信息。
- EvidenceCard 不需要关心来源是否外部，只通过 `source_document_id` 回溯。

## DocumentChunk

DocumentChunk 是文档 RAG 层，负责定位、抽取和溯源。

V1 保留 parent/child chunk：

```text
parent chunk:
  较长上下文，用于 EvidenceCard 抽取和来源解释。

child chunk:
  较短片段，用于精确定位、向量索引和后续 fallback 预留。
```

推荐统一表：

```text
document_chunks
  id
  document_id
  parent_chunk_id
  chunk_type: parent | child
  content
  section_title
  city
  domain
  start_char
  end_char
  token_count
  content_hash
  metadata_json
  created_at
```

父子关系：

```text
parent chunk:
  parent_chunk_id = null

child chunk:
  parent_chunk_id = parent chunk id
```

## EvidenceCard

EvidenceCard 是 Agent 决策证据层，是线上规划的主检索对象。

它不是原始文本，而是从文档中抽取出的结构化、可追溯、可审核的旅行规划证据。

推荐字段：

```text
id
claim
evidence_type
city
entities_json
applies_to_json
time_hint
intensity
budget_level
season
confidence
status
raw_quote
supporting_summary
embedding_text
source_document_id
source_chunk_id
valid_until
embedding_version
indexed_at
index_status
created_at
updated_at
```

状态：

```text
temporary
pending_review
approved
rejected
```

V1 长期知识库只索引 `approved` EvidenceCard。V1.5 外部检索生成的 temporary EvidenceCard 只用于当前会话。

## Evidence Type

第一版建议保留以下类型：

| 类型 | 含义 |
|------|------|
| `route_relation` | 景点/区域之间是否适合同游、顺路、适合放同一天 |
| `time_intensity` | 游玩耗时、强度、是否适合低强度/亲子/父母 |
| `attraction_fit` | 景点适合的兴趣、人群、旅行风格 |
| `area_strategy` | 城市区域安排策略，如商圈、住宿区、路线分布 |
| `risk_or_constraint` | 风险、限制、闭馆、季节、拥挤等 |
| `food_option` | 美食区域、餐饮选择、适合偏好 |

## Embedding Text

EvidenceCard 不应只 embedding 很短的 `claim`，否则向量检索能力会下降。应构造专门的 `embedding_text`：

```text
城市：成都
证据类型：路线组合、景点关系、半日游安排
结论：武侯祠和锦里距离较近，适合组合为半日文化游路线
适用场景：第一次到访、喜欢历史文化、低强度、不想太累
相关地点：武侯祠、锦里
时间建议：半日
强度：低
原文依据：武侯祠和锦里距离较近，适合一起游玩
```

这样 Chroma 负责模糊意图匹配，BM25 负责实体和关键词命中。

