# Travel Agent

基于 LangGraph 的智能旅行规划系统。用户通过 Web 界面对话式提交旅行需求，系统以多 Agent 协作完成分域规划、行程整合与人工审批。

## 技术栈

- **后端**：FastAPI + LangGraph + PostgreSQL + Redis + ChromaDB
- **前端**：Vite + React + TypeScript + Tailwind
- **AI**：通义千问 (DashScope) + DeepSeek + MiMo

## 项目结构

```
travel_agent/
├── backend/          # FastAPI + LangGraph 后端
├── frontend/         # Vite React 前端
├── data/             # RAG 文档与样本数据
├── infra/            # Docker / nginx
├── evals/            # 规划质量评测
├── docs/             # 技术文档
├── AGENTS.md         # AI 开发约束
└── .specify/         # Spec Kit 配置
```

## 快速开始

```bash
# 启动 PostgreSQL + Redis
make docker-up

# 配置环境变量
cp .env.example .env

# 安装依赖并启动后端
uv sync
make backend

# 启动前端
cd frontend && pnpm install && pnpm dev
```

## 文档

| 文档 | 说明 |
|------|------|
| [AGENTS.md](AGENTS.md) | AI Agent 开发约束 |
| [docs/architecture.md](docs/architecture.md) | 技术架构总览 |
| [docs/langgraph_flow.md](docs/langgraph_flow.md) | LangGraph 流程 |
| [docs/api.md](docs/api.md) | API 参考 |
| [docs/database.md](docs/database.md) | 数据模型 |
| [docs/mcp.md](docs/mcp.md) | MCP 集成 |
| [docs/deployment.md](docs/deployment.md) | 部署指南 |
| [docs/smoke-test/README.md](docs/smoke-test/README.md) | 冒烟测试（主路径 / 修订 / 异常） |
| [docs/test-cases/README.md](docs/test-cases/README.md) | 功能测试用例库（标准用例） |

## Spec Kit

本项目使用 GitHub Spec Kit 进行规格驱动开发。在 Cursor 中使用 `/speckit-specify`、`/speckit-plan`、`/speckit-tasks`、`/speckit-implement` 等命令。

## 开发约束

所有 AI Agent 开发须遵循 [AGENTS.md](AGENTS.md)，**遇到模糊需求必须先向用户确认**。
