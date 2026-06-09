# V1 EvidenceEngine Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Slice 4 from
> [10-v1-implementation-roadmap.md](10-v1-implementation-roadmap.md).

**Goal:** 让 PlanningRuntime 的 `retrieve_evidence` 阶段消费 **approved EvidenceCard**，
返回结构化 `EvidenceContext` 和 `sufficiency_result`，替代旧 chunk RAG 作为正式规划证据源。

**Architecture:** `RetrieveEvidenceStageHandler` 调用 `EvidenceEngine.retrieve()`。
Engine 负责 query 分析、metadata 过滤、Chroma + BM25 + RRF、PostgreSQL hydration、
充足度评估；Stage 只写 RuntimeState 结构化输出和 RuntimeEvent，不直接访问 Chroma/SQL。

**Tech Stack:** Python, Pydantic, pytest-asyncio, 复用现有
`backend/app/knowledge/hybrid_retriever.py` 的 RRF 思路，新增 EvidenceCard 专用边界。

**Prerequisites:** Slice 3 已完成（`PlanningNeed` / `BaseContext` / `ContextAssembler`、
collect waiting 语义、78 runtime 测试全绿）。

---

## 1. Scope

本文只冻结并实现 Slice 4。

```text
Slice 4: EvidenceEngine minimal retrieval + retrieve_evidence stage
```

### In Scope

```text
EvidenceCard / EvidenceContext / SufficiencyResult Pydantic schemas
ChineseTokenizer protocol + JiebaTokenizer adapter
EvidenceRepository boundary (fixture-backed for V1; PG-ready interface)
EvidenceEngine.retrieve() — approved cards only, vector + BM25 + RRF
QueryAnalyzer minimal implementation from PlanningNeed
SufficiencyEvaluator with suggested_action = mark_assumptions_and_continue
RuntimeState evidence_context / sufficiency_result fields
真实 RetrieveEvidenceStageHandler（替换 skeleton）
ContextAssembler 扩展 evidence_context 可见性
backend/tests/runtime/ evidence tests + fixture approved EvidenceCards
更新 runtime-framework-inventory.md
```

### Out Of Scope

```text
KnowledgeFactory 完整离线 rebuild CLI
DB migration 0003 knowledge evidence cards（可先用 fixture/in-memory repository）
external temporary EvidenceCard / external_search
retrieval eval metrics 工作台
DocumentChunk 线上 fallback 检索
ToolService / WeatherTool
DomainPlannerGroup
frontend RuntimeEvent switch
LangSmith dataset experiments
```

V1 允许先用 **small approved EvidenceCard fixture** 跑通 Runtime 检索闭环；完整
KnowledgeFactory 与 PG 表迁移可在 Slice 4 后期或 Slice 4.5 增量接入，但 online
EvidenceEngine 接口必须先稳定。

## 2. Directory Freeze For Slice 4

### Create Now

```text
backend/app/knowledge/
  evidence_schemas.py
  evidence_repository.py
  evidence_engine.py
  evidence_sufficiency.py
  tokenizers.py
  query_analyzer.py

backend/app/runtime/stages/retrieve_evidence.py   # replace skeleton
backend/tests/runtime/
  test_evidence_engine.py
  test_evidence_schemas.py
  test_retrieve_evidence_stage.py
  test_evidence_context_smoke.py

backend/tests/fixtures/evidence/
  approved_chengdu_cards.json
```

### Reuse, Do Not Break

```text
backend/app/knowledge/hybrid_retriever.py      -> RRF fusion reference
backend/app/knowledge/vector_store.py          -> Chroma access patterns
backend/app/knowledge/document_loader.py       -> offline path reference only
backend/app/knowledge/rag_service.py           -> old graph compatibility; do not route Runtime through it
backend/app/runtime/context/assembler.py       -> extend specs for evidence_context
backend/app/runtime/context/specs.py
```

### Do Not Create Yet

```text
backend/app/knowledge/evidence_factory.py      -> offline rebuild; separate slice/phase
backend/app/knowledge/evidence_report.py
backend/app/runtime/discovery/catalog.py       -> remains future
CLI rebuild commands beyond minimal inspect/query stub
```

## 3. Runtime And Evidence Contract

### RuntimeState Additions

```python
class RuntimeState(TypedDict, total=False):
    # ... existing fields ...
    evidence_context: dict[str, Any] | None
    sufficiency_result: dict[str, Any] | None
```

Rules:

```text
evidence_context 只在 retrieve_evidence 完成后写入
sufficiency_result 与 evidence_context 同阶段写入
retrieve_evidence 只读取 planning_need / base_context，不读取 collect_context
证据不足时仍 completed（不 blocking），但 sufficiency_result.is_sufficient = false
```

### EvidenceCard Minimal Shape (online)

```python
class EvidenceCard(BaseModel):
    id: str
    claim: str
    evidence_type: str
    city: str | None = None
    entities: list[str] = Field(default_factory=list)
    applies_to: list[str] = Field(default_factory=list)
    time_hint: str | None = None
    intensity: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    status: Literal["approved"]  # V1 online only approved
    embedding_text: str
    source_document_id: str | None = None
    source_chunk_id: str | None = None
```

### EvidenceContext Minimal Shape

```python
class EvidenceContext(BaseModel):
    cards: list[EvidenceCard]
    card_ids: list[str]
    query_summary: dict[str, Any]
    retrieval_trace: dict[str, Any]
```

### SufficiencyResult Minimal Shape

```python
class SufficiencyResult(BaseModel):
    is_sufficient: bool
    score: float
    missing_tags: list[str]
    missing_evidence_types: list[str]
    suggested_action: Literal["mark_assumptions_and_continue"]
```

V1 固定 `suggested_action = mark_assumptions_and_continue`；不调用外部搜索。

### ChineseTokenizer Protocol

```python
class ChineseTokenizer(Protocol):
    def tokenize(self, text: str) -> list[str]: ...
```

`JiebaTokenizer` 是唯一 V1 实现；`hybrid_retriever.py` 与 EvidenceEngine 不得直接
`import jieba`，只通过 tokenizer 边界调用。

## 4. Task Plan

### Task 1: Define Evidence Schemas

**Files:**

```text
Create: backend/app/knowledge/evidence_schemas.py
Create: backend/tests/runtime/test_evidence_schemas.py
```

**Required behavior:**

```text
EvidenceCard, EvidenceContext, SufficiencyResult, RetrievalTrace pydantic models
EvidenceCard.status validator rejects non-approved values for online retrieval results
serialize/deserialize round-trip helpers
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_evidence_schemas.py -q
```

### Task 2: Implement ChineseTokenizer Boundary

**Files:**

```text
Create: backend/app/knowledge/tokenizers.py
Modify: backend/tests/runtime/test_evidence_engine.py
```

**Required behavior:**

```text
ChineseTokenizer protocol
JiebaTokenizer adapter wrapping jieba.cut
unit test proves tokenizer isolates jieba from engine/repository code paths
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_evidence_engine.py -k tokenizer -q
```

### Task 3: Implement EvidenceRepository Boundary

**Files:**

```text
Create: backend/app/knowledge/evidence_repository.py
Create: backend/tests/fixtures/evidence/approved_chengdu_cards.json
Modify: backend/tests/runtime/test_evidence_engine.py
```

**Required behavior:**

```text
EvidenceRepository protocol:
  list_approved_cards(*, city: str | None = None) -> list[EvidenceCard]
  get_cards_by_ids(card_ids: list[str]) -> list[EvidenceCard]
FixtureEvidenceRepository loads approved_chengdu_cards.json
PostgresEvidenceRepository stub or NotImplemented boundary reserved for later migration
only returns status=approved cards
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_evidence_engine.py -k repository -q
```

### Task 4: Implement QueryAnalyzer

**Files:**

```text
Create: backend/app/knowledge/query_analyzer.py
Modify: backend/tests/runtime/test_evidence_engine.py
```

**Required behavior:**

```text
build_retrieval_query(planning_need, base_context) -> RetrievalQuery
extract city, duration, must_visit/preferences tags, required_evidence_types
does not read CollectContext
uses PlanningNeed confirmed/derived facts and BaseContext planning_need_summary
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_evidence_engine.py -k query_analyzer -q
```

### Task 5: Implement EvidenceEngine Core Retrieval

**Files:**

```text
Create: backend/app/knowledge/evidence_engine.py
Modify: backend/tests/runtime/test_evidence_engine.py
```

**Required behavior:**

```text
EvidenceEngine.retrieve(planning_need, base_context) -> tuple[EvidenceContext, SufficiencyResult]
filter approved cards by city/metadata before ranking
vector rank uses embedding_text similarity (V1 may use deterministic text overlap stub if vector index not ready)
BM25 rank uses ChineseTokenizer over embedding_text
RRF fusion keyed by evidence_card_id
hydrate final cards through repository.get_cards_by_ids
no HTTP / external search / old rag_service calls
```

V1 acceptable shortcut:

```text
If EvidenceCard vector index is not yet rebuilt, use in-memory cosine-over-token-set or
repository-provided rank scores for fixture cards, but keep vector/BM25/RRF interfaces stable.
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_evidence_engine.py -q
```

### Task 6: Implement SufficiencyEvaluator

**Files:**

```text
Create: backend/app/knowledge/evidence_sufficiency.py
Modify: backend/tests/runtime/test_evidence_engine.py
```

**Required behavior:**

```text
evaluate(query, cards) -> SufficiencyResult
computes evidence_type_coverage and need_tag_coverage
returns is_sufficient=false with missing_tags when coverage below threshold
always suggested_action=mark_assumptions_and_continue in V1
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_evidence_engine.py -k sufficiency -q
```

### Task 7: Extend RuntimeState And Helpers

**Files:**

```text
Modify: backend/app/runtime/state.py
Modify: backend/tests/runtime/test_runtime_state.py
```

**Required behavior:**

```text
set_evidence_context / set_sufficiency_result helpers
create_initial_runtime_state initializes both to None
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_runtime_state.py -q
```

### Task 8: Replace RetrieveEvidence Stage Skeleton

**Files:**

```text
Modify: backend/app/runtime/stages/retrieve_evidence.py
Create: backend/tests/runtime/test_retrieve_evidence_stage.py
```

**Required behavior:**

```text
RetrieveEvidenceStageHandler calls EvidenceEngine.retrieve
requires planning_need; uses base_context if present
writes evidence_context and sufficiency_result to RuntimeState
returns completed even when insufficient (with sufficiency_result flagged)
does not read collect_context
injects EvidenceEngine/repository in __init__ for tests
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_retrieve_evidence_stage.py -q
```

### Task 9: Extend ContextAssembler For EvidenceContext

**Files:**

```text
Modify: backend/app/runtime/context/specs.py
Modify: backend/app/runtime/context/assembler.py
Modify: backend/tests/runtime/test_context_assembler.py
```

**Required behavior:**

```text
formal planning specs may read evidence_context.cards summaries, not raw retrieval traces
still reject collect_context
destination_planner may read evidence_context card ids + claims subset
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime/test_context_assembler.py -q
```

### Task 10: Slice 4 Integration Smoke Test

**Files:**

```text
Create: backend/tests/runtime/test_evidence_context_smoke.py
Modify: backend/tests/runtime/test_collect_context_smoke.py (optional cross-check)
```

**Required behavior:**

```text
after Slice 3 collect-ready state, retrieve_evidence produces EvidenceContext + sufficiency_result
insufficient fixture still completes stage with mark_assumptions_and_continue
full path: collect ready -> prepare_base_context -> retrieve_evidence -> skeleton stages continue
```

**Verification:**

```powershell
uv run pytest backend/tests/runtime -q
uv run pytest backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py -q
```

### Task 11: Update Runtime Framework Inventory

**Files:**

```text
Modify: docs/rag-agent-refactor/runtime-framework-inventory.md
Modify: docs/rag-agent-refactor/README.md
```

**Required updates:**

```text
Add knowledge/evidence_*.py and tokenizers.py
Mark retrieve_evidence.py as active
Record old rag_service/hybrid_retriever as compatibility reference
Update last_verified_date
```

## 5. Integration Rules

### Existing Graph RAG

Do not route Runtime through:

```text
backend/app/knowledge/rag_service.py
backend/app/knowledge/rag_pipeline.py
backend/app/graph/nodes that embed old chunk retrieval
```

Old graph keeps working until Phase 9 retirement.

### Existing Hybrid Retriever

`hybrid_retriever.py` remains chunk-oriented compatibility code. Slice 4 may extract
RRF utility from it into a shared helper, but must not change old graph behavior tests.

### PlanningRuntime

`retrieve_evidence` returns `completed` for both sufficient and insufficient cases.
Downstream stages must read `sufficiency_result` rather than blocking here.

### jieba Warning

Isolate jieba behind `ChineseTokenizer`. Do not globally suppress setuptools/pkg_resources
warnings in Slice 4; add focused tokenizer regression tests instead.

## 6. Verification Commands

Run after each task:

```powershell
uv run pytest backend/tests/runtime/test_evidence_schemas.py -q
uv run pytest backend/tests/runtime/test_evidence_engine.py -q
uv run pytest backend/tests/runtime/test_retrieve_evidence_stage.py -q
uv run pytest backend/tests/runtime/test_context_assembler.py -q
```

Final Slice 4 verification:

```powershell
uv run pytest backend/tests/runtime backend/tests/test_chat_stream.py backend/tests/test_checkpoint.py backend/tests/test_approval_router.py -q
```

Expected:

```text
retrieves approved cards only
returns sufficiency_result
marks assumptions path available when insufficient
ContextAssembler exposes evidence to formal planners without collect_context
Slice 1-3 runtime tests still pass
```

## 7. Completion Criteria

Slice 4 is complete when:

```text
EvidenceCard / EvidenceContext / SufficiencyResult schemas exist
ChineseTokenizer isolates jieba usage for EvidenceEngine BM25 path
EvidenceRepository returns approved cards only
EvidenceEngine performs metadata filter + vector + BM25 + RRF + hydration
SufficiencyEvaluator returns mark_assumptions_and_continue when insufficient
RetrieveEvidenceStageHandler replaces skeleton behavior
RuntimeState stores evidence_context and sufficiency_result
ContextAssembler updated for evidence visibility
Slice 4 tests and smoke test pass without breaking Slice 1-3 tests
runtime-framework-inventory.md updated
```

After this, the next implementation plan should be:

```text
14-v1-tool-service-implementation-plan.md
```

It should cover:

```text
ToolService allowlist
WeatherTool adapter
tool_enrich stage real implementation
ToolContext.weather
```
