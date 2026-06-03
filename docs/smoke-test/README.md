# 冒烟测试总览

Travel Agent 冒烟测试拆分为三条路径，对应 LangGraph 全链路的不同切面。

| 文档 | 路径 | 覆盖范围 | 预估耗时 |
|------|------|----------|----------|
| [**执行报告**](./REPORT.md) | 最近一次冒烟结果 | pytest + Playwright 输出、质量分析、已知问题 | — |
| [主路径](./main-path.md) | 登录 → 需求收集 → 规划 → 审批 → 订单 | 端到端 happy path | UI 手动 15–25 min；自动化 ~2 min |
| [修订路径](./revision-path.md) | 行程生成 → 请求修改 → 重新生成 → 确认 | 审批分支 | UI 手动 +5 min |
| [异常路径](./exception-path.md) | 错别字、假期口语、预算/风格防幻觉等 | 语义与兜底 | 自动化 ~1 min |

## 前置条件

```bash
make docker-up          # PostgreSQL + Redis
cp .env.example .env    # 配置 MIMO_API_KEY / JWT / DB
make init-db            # 首次
make backend            # :8200
make frontend           # :5173（UI 测试）
```

## 一键执行（推荐）

```bash
# 后端冒烟（路由 + 语义，无需 LLM）
make test-smoke

# 含 Playwright UI 壳层（需 backend + frontend 已启动）
make test-smoke-ui
```

### 命令明细

| 命令 | 说明 |
|------|------|
| `uv run pytest backend/tests/ -m smoke -q` | 三条路径的后端自动化断言 |
| `pnpm exec playwright test --config ../playwright.config.ts` | UI 鉴权 + 主路径前几步 |
| `PLAYWRIGHT_SKIP_WEBSERVER=1 ...` | 使用已运行的 dev server |

## 进度条阶段对照

```
需求 → 目的地 → 交通 → 食宿 → 活动 → 行程 → 确认 → 完成
```

对应 Graph 节点见 [langgraph_flow.md](../langgraph_flow.md)。

## 通过标准

- 后端 `pytest -m smoke` 全绿
- Playwright `e2e/` 全绿（环境允许时）
- 手动主路径 Checklist 全部勾选（发布前建议做一次完整 UI 走查）

## 最近执行报告

见 [REPORT.md](./REPORT.md)（日期、命令、问题表、响应质量分析、复跑方式）。

## 完整测试用例库

功能点标准测试用例（~111 条）：[test-cases/README.md](../test-cases/README.md)
