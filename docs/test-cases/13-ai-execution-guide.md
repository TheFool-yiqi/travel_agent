# AI 可执行测试指南（PlanningRuntime v3）

> **版本：** v3.0 · **更新：** 2026-06-09  
> **架构基线：** PlanningRuntime 九阶段（chat 唯一主路径）

---

## 1. 文档结构

| 文件 | 用途 |
|------|------|
| [00-ai-manifest.json](./00-ai-manifest.json) | **机器可读**用例清单（AI/CI 直接解析） |
| [11-runtime-stages.md](./11-runtime-stages.md) | 九阶段单元/集成用例（TC-RT-*） |
| [12-runtime-chat-resume.md](./12-runtime-chat-resume.md) | SSE、会话持久化、resume（TC-RT-STREAM / TC-RT-SESS） |
| [14-flow-matrix-v3.md](./14-flow-matrix-v3.md) | 端到端业务流程矩阵（FLOW-*） |
| [01–10 模块](./README.md) | 认证/语义/审批等横切能力（仍有效，PLAN 模块见 legacy 说明） |

---

## 2. 用例编号规范

| 前缀 | 含义 | 示例 |
|------|------|------|
| `TC-RT-{STAGE}-{NNN}` | Runtime 阶段 | `TC-RT-DOMAIN-001` |
| `TC-RT-STREAM-{NNN}` | SSE / 前端适配 | `TC-RT-STREAM-003` |
| `TC-RT-SESS-{NNN}` | 会话状态 / resume | `TC-RT-SESS-002` |
| `TC-RT-ORCH-{NNN}` | 编排器（PlanningRuntime） | `TC-RT-ORCH-001` |
| `TC-{MODULE}-{NNN}` | 横切模块（AUTH/SEM/…） | `TC-AUTH-001` |
| `TC-E2E-{NNN}` / `TC-FLOW-{NNN}` | Playwright 全流程 | `TC-E2E-002` |

**STAGE 缩写：** COLLECT · PREP · EVID · TOOL · DOMAIN · INTEG · VERIFY · APPROVE · FINAL

---

## 3. 成功验证指标（统一）

每条 manifest 用例含 `success_criteria`，AI 执行后按下列规则判定 **PASS / FAIL**：

| 指标 | 判定条件 |
|------|----------|
| **exit_code** | 子进程退出码等于 manifest 指定值（默认 `0`） |
| **pytest** | 输出含 `N passed`，且无 `FAILED` / `ERROR` |
| **playwright** | 输出含 `N passed`，且无 `failed` |
| **assertions** | 文档/用例描述中的逻辑断言（由测试代码保证；失败时 pytest 非 0） |
| **evidence**（E2E） | 页面或 SSE 流中出现指定正则/元素（由 Playwright expect 保证） |
| **coverage_gate**（套件级） | `SUITE-FULL-BACKEND` 全部 PASS 且 `passed >= 700` |

### 3.1 套件级 SLA（发版门禁）

| 套件 ID | 命令 | PASS 条件 |
|---------|------|-----------|
| `SUITE-SMOKE` | `make test-smoke` | exit 0，≥20 passed |
| `SUITE-RUNTIME` | `uv run pytest backend/tests/runtime/ -q` | exit 0，≥150 passed |
| `SUITE-BACKEND` | `make test-backend` | exit 0，≥700 passed |
| `SUITE-E2E-P0` | Playwright P0 用例 | exit 0，12/12 passed |
| `SUITE-FULL` | BACKEND + E2E-P0 | 两者均 PASS |

---

## 4. AI 执行方式

### 4.1 单条用例

```bash
uv run python scripts/run_test_case.py TC-RT-COLLECT-001
```

### 4.2 按套件

```bash
uv run python scripts/run_test_case.py --suite SUITE-SMOKE
uv run python scripts/run_test_case.py --suite SUITE-RUNTIME
uv run python scripts/run_test_case.py --suite SUITE-E2E-P0
```

### 4.3 按优先级 / 层

```bash
uv run python scripts/run_test_case.py --priority P0 --layer pytest
uv run python scripts/run_test_case.py --layer playwright
```

### 4.4 列出可执行用例

```bash
uv run python scripts/run_test_case.py --list
uv run python scripts/run_test_case.py --list --suite SUITE-RUNTIME
```

### 4.5 写回执行日志

```bash
uv run python scripts/run_test_case.py --suite SUITE-SMOKE --log
```

---

## 5. 前置环境

| 层 | 要求 |
|----|------|
| **pytest** | 仓库根目录；`uv sync` 已完成；无需外部 LLM（默认 `-m "not integration"`） |
| **playwright** | `backend` 在 `:8200`；`make test-e2e` 可自动起 Vite `:5173` |
| **integration** | 显式 `-m integration` 用例需配置 `.env` 中 LLM/MCP 密钥 |

---

## 6. AI Agent 执行流程（推荐）

```text
1. 读取 00-ai-manifest.json
2. 确认 preconditions（health、docker、.env）
3. 按 priority P0 → P1 顺序执行 --suite SUITE-SMOKE → SUITE-RUNTIME → SUITE-E2E-P0
4. 收集 run_test_case.py 的 JSON 摘要（stdout 最后一行）
5. FAIL 时：读取失败用例的 command，单独 -v 重跑，贴出 traceback
6. 全部 PASS 后：--log 更新 EXECUTION_LOG.md
```

---

## 7. 与旧版用例的关系

- **TC-PLAN-***（LangGraph 八节点）已 **废弃**；等价能力映射到 **TC-RT-DOMAIN / INTEG / VERIFY / APPROVE / FINAL**。
- **TC-REQ / TC-SEM / TC-APR / TC-CHAT / TC-E2E** 仍有效；manifest 中通过 `legacy_ids` 字段追溯。
- 旧 [04-planning-flow.md](./04-planning-flow.md) 仅作历史参考，勿按 graph 节点执行。

---

## 8. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v3.0 | 2026-06-09 | PlanningRuntime 专用 manifest + AI runner + 九阶段用例 |
