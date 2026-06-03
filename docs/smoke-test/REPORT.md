# 冒烟测试执行报告

**执行日期：** 2026-06-03  
**执行环境：** Windows · Python 3.13 · pnpm 9.15.0

## 当前结果

| 范围 | 命令 | 结果 |
|------|------|------|
| 后端 smoke | `uv run pytest backend/tests/ -m smoke -q` | 23 passed, 586 deselected |
| 后端默认非集成 | `uv run pytest backend/tests/ -m "not integration" -q` | 587 passed, 22 deselected |
| 前端构建 | `cd frontend && npx pnpm@9.15.0 run build` | passed |

## 覆盖行为

| 路径 | 自动化覆盖 |
|------|------------|
| 主路径 | 需求引导顺序、用户确认门禁、规划链路路由、行程进入审批 |
| 修订路径 | 确认/修订关键词识别，审批后分支到 `final_response` 或 `revise_itinerary` |
| 异常路径 | 节假日天数理解、预算/风格防幻觉、错别字澄清与目的地碰撞防护 |
| API / 数据安全 | 默认非集成测试覆盖鉴权、会话、行程、RAG、MCP fallback、边界输入等回归 |

## 仍需手动执行

| 路径 | 文档 | 手动内容 |
|------|------|----------|
| 主路径完整 UI | [main-path.md](./main-path.md) | 需求收集 → 目的地 → 交通 → 食宿 → 活动 → 行程卡片 → 确认 → `ORDER-` 订单号 |
| 修订路径 UI | [revision-path.md](./revision-path.md) | 行程生成后请求修改 → 重新生成 → 二次确认 → 订单 |
| 异常路径穿插 | [exception-path.md](./exception-path.md) | 错别字、口语天数、预算歧义、用户纠错等对话场景 |

## 重新执行

```bash
make docker-up
make init-db
make backend
make frontend

uv run pytest backend/tests/ -m smoke -q
uv run pytest backend/tests/ -m "not integration" -q
cd frontend && npx pnpm@9.15.0 run build
```

发布前建议至少完成一次主路径手动 Checklist；涉及 `approval_node` 或 `revise_itinerary` 变更时补测修订路径。
