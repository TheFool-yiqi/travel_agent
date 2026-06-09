# Storage Design

## 总体原则

```text
PostgreSQL = 权威业务数据
Chroma = 向量索引
BM25 = 关键词索引
data/ = 原始资料和开发期产物
```

不要在 PostgreSQL 和 Chroma 中各存一份完整 EvidenceCard。Chroma 和 BM25 都是派生索引，只返回 id，完整对象从 PostgreSQL 获取。

## data 目录

推荐保留：

```text
data/
  documents/
    destinations/
    transport/
    food/
    accommodation/
    policies/

  vectorstore/
    chroma.sqlite3
    ...

  exports/
    knowledge_build_reports/
    rag_eval_reports/
```

说明：

- `data/documents/` 存本地文档或外部资料快照。
- `data/vectorstore/` 由 Chroma 持久化生成，不手动维护。
- `data/exports/` 存构建报告和 eval 报告。

## PostgreSQL

PostgreSQL 是 system of record。

推荐表：

```text
documents
document_chunks
evidence_cards
```

后续如需更精细来源关系，可增加：

```text
evidence_card_sources
```

但 V1 一张 EvidenceCard 绑定一个 `source_document_id` 和一个 `source_chunk_id` 即可。

## Chroma

Chroma 只保存向量索引必要信息。

推荐 collections：

```text
evidence_cards
document_child_chunks
```

V1 线上主流程只使用 `evidence_cards` collection。

EvidenceCard 在 Chroma 中的结构：

```json
{
  "id": "ev_chengdu_route_001",
  "document": "embedding_text",
  "metadata": {
    "city": "成都",
    "evidence_type": "route_relation",
    "status": "approved",
    "confidence": 0.86,
    "source_chunk_id": "chunk_chengdu_001_003"
  }
}
```

检索后：

```text
Chroma returns evidence_card_id
  -> PostgreSQL batch fetch
  -> hydrated EvidenceCard
```

## BM25

BM25 检索 EvidenceCard 的派生搜索文本：

```text
search_text =
  claim
  + entities
  + raw_quote
  + evidence_type 中文解释
  + applies_to
  + city
```

BM25 只返回：

```text
evidence_card_id
rank
score
```

最终仍回 PostgreSQL 获取完整 EvidenceCard。

第一版可选实现：

```text
jieba + rank_bm25
```

后续可替换为：

```text
PostgreSQL full-text search
Elasticsearch/OpenSearch
```

## 索引一致性

V1 采用全量重建，因此索引同步简单：

```text
clear old Chroma collection
clear old BM25 index
load approved EvidenceCards from PostgreSQL
upsert Chroma
rebuild BM25
```

推荐保留字段，为未来增量做准备：

```text
embedding_version
indexed_at
index_status: pending | indexed | failed
content_hash
checksum
```

V1 不实现复杂增量更新。

