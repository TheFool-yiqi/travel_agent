# V1 QualityVerifier Implementation Plan

> **For agentic workers:** implement this plan task-by-task. Do not commit unless the
> user explicitly asks. This plan covers Slice 7 from
> [10-v1-implementation-roadmap.md](10-v1-implementation-roadmap.md).

**Goal:** 让 `verify` 阶段对 `ItineraryDraft + EvidenceContext` 产出结构化
`QualityReport`；blocking issue 触发一次自动修订，二次仍失败则标记 `surface_to_user`。

**Architecture:** `VerifyStageHandler` 调用 `QualityVerifier.verify()`，必要时调用
`RevisionAgent.revise()`（`max_auto_revision = 1`）。V1 使用 deterministic rule-based
Judge，不调用 LLM。

**Prerequisites:** Slice 6 已完成（`itinerary_draft` 真实产出、133 runtime 测试全绿）。

---

## 1. Scope

```text
Slice 7: QualityVerifier + RevisionAgent + verify stage
```

### In Scope

```text
QualityIssue / QualityReport schemas
QualityVerifier deterministic checks
RevisionAgent single auto-revision pass
RuntimeState quality_report / revision_count
真实 VerifyStageHandler
ContextAssembler itinerary_summary / sufficiency_summary for quality_verifier
Slice 7 integration smoke test
更新 runtime-framework-inventory.md
```

### Out Of Scope

```text
LLM Judge profile
approve_or_revise interrupt / finalize persistence
frontend approval UI
LangSmith tracing
```

## 2. Completion Criteria

```text
blocking day-count mismatch triggers revision once
insufficient evidence without assumptions flagged then fixed by revision
unsupported claims detected
verify completes with quality_report even when issues remain
Slice 1-6 tests still pass
```

Next plan: `17-v1-approval-finalize-implementation-plan.md`
