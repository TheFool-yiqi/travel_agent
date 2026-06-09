# V1 Scope

> 本文是 V1 / V1.5 / V2 范围边界说明。PlanningRuntime 主流程以
> [09-planning-runtime-blueprint.md](09-planning-runtime-blueprint.md) 为准。
> 若本文中的早期节点名或旧 graph 叙事与 09 冲突，以 09 为准。

## V1 必做

### Knowledge Model

```text
SourceDocument
DocumentChunk parent/child
EvidenceCard
```

EvidenceCard 是线上主检索对象。

### Offline Full Rebuild

```text
knowledge rebuild
  -> documents
  -> chunks
  -> EvidenceCards
  -> normalize
  -> hard rule verification
  -> dedupe
  -> LLM verification
  -> Chroma
  -> BM25
  -> build report
```

V1 不做增量更新。

### EvidenceCard Extraction

```text
prompt file
structured output
Pydantic schema
raw_quote required
supporting_summary generated offline
```

### Hybrid Retrieval

```text
EvidenceCard vector retrieval
EvidenceCard BM25 retrieval
metadata filter
RRF fusion
PostgreSQL hydration
```

### Agent Flow

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

旧 `retrieve_planning_evidence` 节点语义升级为 `retrieve_evidence` stage。
旧 `build_itinerary` 职责拆到 `domain_plan`、`integrate` 和 `finalize`。

## V1 预留但不实现

```text
DocumentChunk fallback
目的地发现 RAG
行程验证 RAG
外部检索补充
长期知识库增量更新
人工审核页面
多级 relevance 标注
answer quality eval
MCP/tools CLI
Retrieval Eval
```

## V1.5 可做

### External Temporary Evidence

```text
sufficiency check failed
  -> targeted external search
  -> temporary EvidenceCard
  -> current session only
```

不沉淀长期库。

### Query Generation

```text
query_templates.yaml
external_search_query_generation.md
```

规则模板为主，LLM prompt 为辅。

### Retrieval Eval

只做 retrieval 指标：

```text
Hit@5 / Hit@10
Recall@5 / Recall@10
MRR@5 / MRR@10
nDCG@5 / nDCG@10
```

对比：

```text
vector
bm25
rrf
```

不做 answer 指标，不做场景诊断指标。

## V2 可做

```text
增量知识库沉淀
temporary -> approved 长期知识流转
DocumentChunk fallback
目的地发现 RAG
行程验证 RAG
human review dashboard
MCP/tools CLI
Agent trace replay
answer quality eval
```

## 暂不做的原因

### 不做长期在线沉淀

当前长期知识库采用全量 rebuild。在线沉淀会带来：

```text
增量切 chunk
局部索引同步
审核状态继承
失败恢复
下次全量 rebuild 覆盖策略
```

这些属于 V2。

### 不做 answer eval

行程质量主观性强，第一版先验证检索层质量，避免评估范围失控。

### 不做复杂 destination discovery RAG

用户意图挖掘先由 TripSpec extraction + completeness check 完成。目的地发现 RAG 后续作为增强能力。

## 推荐面试叙事

可以这样概括：

```text
我的项目没有把 RAG 简化成文档切块问答，而是构建了 SourceDocument、DocumentChunk、EvidenceCard 三层知识结构。

长期知识库通过 CLI 离线全量构建，包含抽取、归一化、硬规则校验、去重、LLM 审核、索引和构建报告。

线上 Agent 在需求成熟后由 PlanningRuntime 进入 `retrieve_evidence` 阶段，使用 EvidenceCard 作为主检索对象，通过 Chroma + BM25 + RRF 做 hybrid retrieval。

V1.5 可用标准 retrieval metrics 对比 vector、BM25 和 RRF，验证混合检索的价值。

当本地证据不足时，后续版本通过 external search 生成 temporary EvidenceCard 参与当前会话，但不污染长期库。
```
