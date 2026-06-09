# AGENTS.md — Travel Agent AI 开发约束

本文档约束所有 AI Agent（Cursor、Copilot 等）在本仓库中的开发行为。与 [docs/architecture.md](docs/architecture.md) 冲突时，以**用户最新明确指令**为准。

---

## 1. 项目概述

**Travel Agent** 是基于 LangGraph 的智能旅行规划系统：

- **后端**：FastAPI + LangGraph + PostgreSQL + Redis + ChromaDB
- **前端**：Vite + React + TypeScript + Tailwind（SPA）
- **能力**：多轮需求收集 → 分域规划 → 行程整合 → 人工审批 → 修订输出

当前阶段：**框架骨架已搭建，业务逻辑待实现**。不要假设已有实现。

---

## 2. 最高优先级规则

### 2.1 模糊时必须先向用户确认（NON-NEGOTIABLE）

遇到以下情况，**必须暂停实现并使用 AskQuestion 或文字向用户确认**，不得自行假设：

| 场景 | 示例 |
|------|------|
| 需求不明确 | 预算校验放在 `build_itinerary` 还是 `critic_agent` |
| 多种可行方案 | 向量库用 Chroma 还是 pgvector |
| 影响 API 契约 | 新增字段是否 breaking change |
| 第三方服务选型 | 天气已选 Open-Meteo；若改 QWeather 主源需确认 |
| 安全/权限策略 | JWT 存 cookie 还是 localStorage |
| 范围不清 | 用户说「优化一下」但未指明模块 |
| 与现有文档冲突 | AGENTS.md 与 architecture.md 不一致 |

**确认后再写代码。** 禁止「先实现一版再说」。

### 2.2 最小改动原则

- 只改与任务直接相关的文件
- 不重构无关模块
- 不添加用户未请求的功能、测试、文档
- 匹配现有代码风格与命名

### 2.3 不提交密钥

- 禁止将 `.env`、`frontend/.env` 中的真实 API Key 写入代码或文档
- 只更新 `.env.example` 中的占位符

### 2.4 范式升级执行门禁（NON-NEGOTIABLE）

进行新框架、PlanningRuntime 或其他范式升级时，必须遵守：

- **没有文档依据，不新增模块**：新增模块必须能对应到已确认的蓝图、路线图或当前 Slice 实施计划
- **没有测试，不声称完成**：未运行对应验收测试，或测试未通过时，只能报告当前进度和风险，不得声明任务已完成
- **没有用户确认，不改 API / DB / 顶层目录**：涉及 API 契约、数据库模型或迁移、仓库顶层目录的修改必须先暂停并确认
- **没有进入对应 Slice，不创建后续目录**：只创建当前 Slice 明确要求的目录和文件，不提前搭建后续模块空壳
- **不把旧 graph node 直接搬进 Runtime stage**：旧实现只能作为行为参考或复用来源，新业务逻辑必须遵守 Runtime 模块边界
- **不让 AI 自己扩大范围**：只执行当前用户确认的 Task / Slice；发现额外工作时先说明原因、影响和建议，等待确认后再执行

这些规则是实施门禁，不是建议。与普通实施顺序或便利性冲突时，以本节为准。

---

## 3. 目录结构（不得随意增删顶层）

```
travel_agent/
├── backend/app/     # FastAPI 应用
├── frontend/        # Vite React SPA
├── data/            # RAG 文档与样本
├── infra/           # Docker / nginx
├── evals/           # 评测
├── docs/            # 技术文档
├── .specify/        # Spec Kit 模板与 constitution
└── .cursor/         # Cursor skills / rules
```

新增顶层目录须先向用户确认。

---

## 4. 后端分层边界（严格遵守）

```
HTTP/WS → api/ | ws/
         → services/          # 业务编排、事务
         → graph/ | agents/ | knowledge/
         → tools/ → mcp/registry 或直连 HTTP
         → db/repositories/ → PostgreSQL
```

| 层级 | 职责 | 禁止 |
|------|------|------|
| `api/` `ws/` | 路由、参数校验、依赖注入 | 直接调用 LLM、写 SQL |
| `services/` | 业务逻辑、调用 graph、持久化 | 直接操作 HTTP 第三方 API |
| `graph/nodes/` | 状态编排、调用 agent、路由 | 直接 HTTP、直接 SQL |
| `agents/` | 单域 LLM 推理、structured output | 写 SQL、直接改 DB |
| `ai/` | LLM/Embedding/Prompt 加载 | 业务逻辑 |
| `tools/` | Agent 可调用的业务工具 | 被前端直接调用 |
| `mcp/` | MCP 客户端、registry、adapters | 被 Agent 绕过 registry 直调 |
| `knowledge/` | RAG 入库/检索/重排 | 替代 tools 做实时查询 |
| `db/repositories/` | 唯一数据库访问入口 | 被 api 层直接调用 |
| `schemas/` | Pydantic 请求/响应模型 | 含业务逻辑 |
| `middleware/` | 横切：CORS、日志、错误、限流 | 业务逻辑 |

### 4.1 tools 与 mcp 分工

```
Agent/Node → tools/xxx.py
              ├─ mcp/registry 查找已注册 MCP 工具
              └─ 否则直连 HTTP（可抽到 tools 内部私有 client）
```

- **禁止** 在 `agents/` 或 `graph/nodes/` 中直接调用 MCP 或第三方 HTTP
- **禁止** 为同一能力在 `tools/` 和 `mcp/adapters/` 各写一套而不经 registry

---

## 5. LangGraph 约定

### 5.1 节点流程

```
collect_requirements → plan_destination → plan_transport
  → plan_stay_and_food → plan_activities → build_itinerary
  → approval_node → final_response
         ↓ (拒绝/质检失败)
    revise_itinerary → 回到规划链
```

- 追问缺失信息：`collect_requirements` + `requirement_router` 路由回自身
- 预算校验：`build_itinerary` 或 `critic_agent`，不单独加节点（除非用户确认）
- Checkpoint：使用 `langgraph-checkpoint-postgres`，封装在 `graph/checkpoint.py`

### 5.2 状态管理

- 状态定义：`graph/state.py`
- Reducer：`graph/reducers.py`
- WS 事件格式：`graph/events.py`（`node_start`, `tool_call`, `token`, `approval_required`, `done`）

### 5.3 新增节点检查清单

新增 graph 节点前确认：

1. 对应 `agents/` 和 `ai/prompts/*.md` 是否已有
2. 是否需要新 `tools/`
3. 是否影响 `TravelState` 字段（需同步 `schemas/travel.py`）
4. 是否需 WS 新事件类型（需同步前端 `types/`）

---

## 6. 前端约定

- **框架**：Vite + React + TypeScript + Tailwind，React Router
- **状态**：Zustand（`stores/`）
- **API**：`lib/api.ts` 统一 REST
- **流式**：`lib/websocket.ts` + `hooks/useTravelStream.ts`
- **页面**：`pages/` 按路由组织，组件按 `layout/` `chat/` `travel/` `approval/` `ui/` 分组

禁止：

- 引入 Next.js 或 SSR 模式（除非用户确认）
- 在组件中硬编码 API URL（用 `lib/config.ts`）
- 前端直接调用第三方旅行 API

---

## 7. 命名与代码风格

### Python

- 文件：`snake_case.py`
- 类：`PascalCase`
- 函数/变量：`snake_case`
- 异步路由/服务：优先 `async def`
- 类型注解：公共函数必须标注
- 格式化：与项目现有风格一致（4 空格缩进）

### TypeScript

- 组件：`PascalCase.tsx`
- hooks：`useXxx.ts`
- stores：`xxxStore.ts`
- 类型：放 `types/`，禁止 `any`（除非有注释说明）

### Prompt 模板

- 存放于 `backend/app/ai/prompts/*.md`
- 通过 `ai/prompts/loader.py` 加载，使用 Jinja2 变量

---

## 8. 数据库约定

- ORM：SQLAlchemy 2.x
- 迁移：Alembic（`backend/alembic/`）
- 模型：`db/models/`
- 访问：仅通过 `db/repositories/`

新增表或字段时：

1. 更新 model
2. 新增 alembic migration
3. 更新 `docs/database.md`
4. 更新相关 `schemas/`

---

## 9. 环境变量

- 后端：根目录 `.env`（参考 `.env.example`）
- 前端：`frontend/.env`（参考 `frontend/.env.example`）
- 读取：后端统一通过 `app/settings.py`（pydantic-settings）

新增环境变量必须同步更新 `.env.example` 和 `docs/architecture.md`。

---

## 10. 测试

- 框架：`pytest` + `pytest-asyncio`
- 目录：`backend/tests/{unit,integration,e2e}/`
- 执行：统一使用 `uv run pytest ...`，禁止直接调用全局环境中的裸 `pytest`
- **仅在用户要求或修复 bug 时添加测试**，不主动为占位代码写无意义测试

---

## 11. Spec Kit 工作流

本项目已初始化 GitHub Spec Kit。功能开发推荐流程：

1. `/speckit-constitution` — 项目原则
2. `/speckit-specify` — 功能规格
3. `/speckit-clarify` — **有歧义时必用**
4. `/speckit-plan` — 技术方案
5. `/speckit-tasks` — 任务拆分
6. `/speckit-implement` — 执行实现

实现前阅读：

- `.specify/memory/constitution.md`
- `docs/architecture.md`
- 本文件 `AGENTS.md`

---

## 12. 实施顺序建议

按依赖顺序开发，避免跨层跳跃：

1. `settings` / `middleware` / `db/engine` / `db/session`
2. `security` + `auth` API
3. `sessions` / `messages` API
4. `graph` 核心 + `ws/travel_stream`
5. `ai/` + `tools/` + `mcp/`
6. `itinerary` / `approval`
7. `knowledge/` RAG
8. 前端页面对接

---

## 13. 禁止事项汇总

- 不提交 `.env` 或真实 API Key
- 不在 graph 节点中写 SQL 或 HTTP
- 不恢复已删除的重量级模块（`integrations/`、`jobs/`、`observability/` 目录）除非用户明确要求
- 不修改 `pyproject.toml` 依赖而不说明原因
- 不创建用户未请求的顶层目录
- 不在模糊需求下自行做架构决策
- 不执行 `git commit` / `git push`，除非用户明确要求

---

## 14. 参考文档

| 文档 | 用途 |
|------|------|
| [docs/architecture.md](docs/architecture.md) | 技术架构总览 |
| [docs/langgraph_flow.md](docs/langgraph_flow.md) | LangGraph 流程细节 |
| [docs/api.md](docs/api.md) | REST / WS API |
| [docs/database.md](docs/database.md) | 数据模型 |
| [docs/mcp.md](docs/mcp.md) | MCP 集成规范 |
| [docs/deployment.md](docs/deployment.md) | 部署说明 |
| [.specify/memory/constitution.md](.specify/memory/constitution.md) | Spec Kit 项目宪法 |

---

**Version**: 1.0.1 | **Last Updated**: 2026-06-06
