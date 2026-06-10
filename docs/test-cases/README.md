# Travel Agent 功能测试用例库（PlanningRuntime v3）

> **版本：** v3.0 · **更新：** 2026-06-09  
> **架构基线：** PlanningRuntime 九阶段（chat 唯一主路径）  
> **AI 执行入口：** [00-ai-manifest.json](./00-ai-manifest.json) + [13-ai-execution-guide.md](./13-ai-execution-guide.md)

---

## 1. 文档体系

| 文件 | 模块 | 说明 |
|------|------|------|
| **[00-ai-manifest.json](./00-ai-manifest.json)** | **AI/CI** | 机器可读用例清单（**58+ 可执行条目**） |
| [13-ai-execution-guide.md](./13-ai-execution-guide.md) | AI 指南 | 成功指标、套件 SLA、执行流程 |
| [11-runtime-stages.md](./11-runtime-stages.md) | TC-RT-* | 九阶段单元/集成（**~45 条**） |
| [12-runtime-chat-resume.md](./12-runtime-chat-resume.md) | TC-RT-STREAM/SESS | SSE、持久化、resume（**~20 条**） |
| [14-flow-matrix-v3.md](./14-flow-matrix-v3.md) | FLOW-RT-* | 业务流程矩阵（**~20 条**） |
| [01-auth-session.md](./01-auth-session.md) | TC-AUTH / TC-SESS | 认证与会话（45） |
| [02-requirements-collection.md](./02-requirements-collection.md) | TC-REQ | 需求收集（39） |
| [03-semantic-understanding.md](./03-semantic-understanding.md) | TC-SEM | 语义理解（50） |
| [04-planning-flow.md](./04-planning-flow.md) | TC-PLAN | ⚠️ **Legacy** LangGraph 节点（已由 TC-RT-* 替代） |
| [05-approval-order.md](./05-approval-order.md) | TC-APR | 审批与订单（22） |
| [06-chat-stream-api.md](./06-chat-stream-api.md) | TC-CHAT / TC-API | SSE、REST（49） |
| [07-frontend-ui.md](./07-frontend-ui.md) | TC-UI | 前端 UI（23） |
| [08-data-security.md](./08-data-security.md) | TC-DATA / TC-SEC | 数据与安全（24） |
| [09-e2e-flows.md](./09-e2e-flows.md) | TC-E2E / TC-FLOW | 端到端（41） |
| [10-negative-boundary.md](./10-negative-boundary.md) | TC-NEG | 异常边界（19） |

**v3 可执行用例合计：** manifest **58** 条（直接 subprocess）+ legacy 模块 **~280** 条（pytest 全库覆盖）→ 全库 **724+** tests。

---

## 2. 功能架构 ↔ 用例映射（v3）

```
┌─────────────────────────────────────────────────────────────────┐
│  AUTH / SESS          认证、会话、历史                              │
├─────────────────────────────────────────────────────────────────┤
│  REQ + SEM            collect 阶段 ←→ 语义层                        │
├─────────────────────────────────────────────────────────────────┤
│  RUNTIME (TC-RT-*)    collect → prep → evidence → tool_enrich     │
│                       → domain_plan → integrate → verify          │
│                       → approve_or_revise → finalize              │
├─────────────────────────────────────────────────────────────────┤
│  STREAM / SESS        SSE 适配、extra_info 持久化、resume           │
├─────────────────────────────────────────────────────────────────┤
│  CHAT / API / UI      REST / Playwright                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 测试套件（AI 可执行）

| 套件 ID | 范围 | 命令 |
|---------|------|------|
| `SUITE-SMOKE` | P0 冒烟 10 条 | `uv run python scripts/run_test_case.py --suite SUITE-SMOKE` |
| `SUITE-RUNTIME` | 九阶段 + stream + resume | `uv run python scripts/run_test_case.py --suite SUITE-RUNTIME` |
| `SUITE-SEM-REQ` | 语义 + 需求 | `--suite SUITE-SEM-REQ` |
| `SUITE-API` | 认证/会话/chat API | `--suite SUITE-API` |
| `SUITE-E2E-P0` | Playwright P0 | `--suite SUITE-E2E-P0` |
| `SUITE-FULL-BACKEND` | 全量 pytest | `--suite SUITE-FULL-BACKEND` |

```bash
# 单条
uv run python scripts/run_test_case.py TC-RT-COLLECT-001

# 列出
uv run python scripts/run_test_case.py --list --suite SUITE-RUNTIME

# 写日志
uv run python scripts/run_test_case.py --suite SUITE-SMOKE --log
```

---

## 4. 成功验证指标（摘要）

| 层级 | PASS 条件 |
|------|-----------|
| **pytest 单条** | exit 0；无 FAILED/ERROR |
| **SUITE-RUNTIME** | manifest 内全部 case `passed: true` |
| **SUITE-FULL-BACKEND** | ≥700 passed |
| **SUITE-E2E-P0** | Playwright exit 0；ORDER 正则匹配 |
| **发版门禁** | SMOKE + RUNTIME + E2E-P0 全 PASS |

详见 [13-ai-execution-guide.md](./13-ai-execution-guide.md) §3。

---

## 5. 标准用例模板（人文档）

```
用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 | 成功指标
```

---

## 6. 执行策略

| 轮次 | 范围 | 时机 |
|------|------|------|
| **冒烟** | SUITE-SMOKE | 每次提测 / AI 首轮 |
| **Runtime 回归** | SUITE-RUNTIME + SUITE-SEM-REQ | 每次 runtime 变更 |
| **发版** | + SUITE-E2E-P0 + SUITE-FULL-BACKEND | 发版前 |
| **全量 E2E** | `make test-e2e` | 大版本 |

```bash
make test-backend          # 724+ tests
make test-smoke            # smoke marker
uv run python scripts/run_test_case.py --suite SUITE-SMOKE
```

---

## 7. 修订记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-06-03 | 初版 ~111 条 |
| v2.0 | 2026-06-03 | 扩充至 351 条 LangGraph 时代 |
| v3.0 | 2026-06-09 | PlanningRuntime manifest + AI runner + TC-RT-* / FLOW-RT-* |
