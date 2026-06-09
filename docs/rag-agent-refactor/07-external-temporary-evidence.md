# External Search And Temporary Evidence

## 背景

本地长期知识库不可能覆盖所有目的地、景点和临时信息。因此当本地 EvidenceCard 不足时，系统可以通过外部检索补充证据。

但 V1/V1.5 不将外部检索结果在线沉淀进长期库，因为长期库采用全量 rebuild 策略，在线增量沉淀会引入复杂索引一致性问题。

## V1.5 策略

```text
local EvidenceCard retrieval
  -> sufficiency check failed
  -> targeted external search
  -> extract temporary EvidenceCards
  -> verify
  -> use in current session only
```

不进入：

```text
长期 evidence_cards
documents
document_chunks
Chroma
BM25
retrieval eval
```

可以保存到：

```text
LangGraph state
session trace
temporary evidence JSON
```

## 为什么不沉淀长期库

当前长期知识库是全量构建：

```text
knowledge rebuild
  -> clear old index
  -> rebuild documents/chunks/cards/indexes
```

在线沉淀会引入：

```text
稳定 ID
局部切 chunk
局部抽卡
局部审核
局部更新 Chroma
局部更新 BM25
下次全量 rebuild 是否覆盖
审核状态继承
失败恢复
```

这些属于 V2 增量知识库能力。

## Targeted Search Query

外部检索不应直接使用用户原话作为主 query，而应根据 missing evidence 生成 targeted query。

输入：

```json
{
  "city": "成都",
  "missing_entities": ["熊猫基地"],
  "missing_evidence_types": ["route_relation", "time_intensity"],
  "preferences": ["低强度"],
  "must_visit": ["熊猫基地", "武侯祠", "锦里"]
}
```

输出：

```json
{
  "queries": [
    {
      "query": "成都 熊猫基地 武侯祠 锦里 三日游 路线 不累",
      "purpose": "route_relation"
    },
    {
      "query": "成都 熊猫基地 游玩时间 半天 强度",
      "purpose": "time_intensity"
    }
  ]
}
```

用户原话可作为 fallback query，但不是主策略。

## Query 模板

V1.5 推荐规则模板为主，LLM prompt 为辅。

规则模板可放：

```text
backend/app/knowledge/query_templates.yaml
```

示例：

```yaml
route_relation:
  - "{city} {entity_a} {entity_b} 路线 安排 交通 时间"
  - "{city} {entity_a} {entity_b} 顺路 半天 一天"

time_intensity:
  - "{city} {entity} 游玩时间 强度 不累"
  - "{city} {entity} 半天 游玩 建议"

food_option:
  - "{city} {area} 美食 小吃 推荐"
```

LLM query generation prompt 可放：

```text
backend/app/ai/prompts/external_search_query_generation.md
```

职责：

```text
根据 missing_tags / missing_evidence_types 生成 3-5 条检索 query
不能引入用户未提到的新具体实体
输出 JSON
```

## Temporary EvidenceCard

即使是临时证据，也必须保留质量门禁。

字段：

```text
claim
evidence_type
entities
raw_quote
source_url
source_title
retrieved_at
confidence
verifier_result
supporting_summary
status = temporary
```

审核：

```text
hard rules
  -> LLM verifier
  -> use or discard
```

不合格的临时证据不能进入 planner。

## Planner 使用方式

Planner 统一消费 EvidenceCard：

```text
approved local EvidenceCards
temporary external EvidenceCards
```

只是上下文中应区分：

```json
{
  "approved_evidence_cards": [],
  "temporary_evidence_cards": []
}
```

Prompt 可要求：

```text
本地 approved evidence 优先级更高
temporary evidence 可用于补充缺口
涉及临时证据的结论应更谨慎
```

