# Test Case Execution Log

> Last verified: 2026-06-03 (batch-4)  
> Executor: agent � changes uncommitted

## Current Automated Baseline

| Command | Result | Notes |
|---------|--------|-------|
| `uv run pytest backend/tests/ -m "not integration" -q` | **598 passed**, 22 deselected | +11 vs batch-3 (`test_automated_skip_cases.py`) |
| `PLAYWRIGHT_SKIP_WEBSERVER=1 cd frontend && npx playwright test --config ../playwright.config.ts --workers=1 --retries=0` | **29/29 passed** (13.1m) | unchanged from batch-3 |
| `uv run python scripts/sync_test_case_docs.py` | 351 cases kept, **59 removed** | non-automatable ?/? rows deleted |

## Batch-4: SKIP audit

| Action | Count |
|--------|-------|
| Cases kept (all ?) | **351** |
| Cases removed (cannot automate) | **59** |
| New pytest file | `test_automated_skip_cases.py` (11 tests) |

**Removed categories:** manual checklists (E2E-010~014), infra fault injection (NEG-014/015, DATA-014/015), LLM integration-only, visual/a11y-only, rate-limit unimplemented, meta traceability (FLOW-023), dual-browser isolation.

**New automation:** TC-NEG-006/007, TC-PLAN-017/020/021, TC-APR-011/021, TC-SEM-030, TC-API-016/022.

## Residual Risks

| Area | Status |
|------|--------|
| Live LLM / real MCP integration | Covered only by Playwright e2e with running backend |
| Rate limiting | Not implemented; cases removed from catalog |
| Dependency deprecations | LangGraph `create_react_agent` migration pending |
