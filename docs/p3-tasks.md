# P3 任务拆分 — 行程持久化 / WebSocket / 生产 Docker / E2E

> P0–P2 已完成：LangGraph 规划链、SSE 流式、审批/修订、React Router 前端。
> 本文档为 P3 实施清单与验收说明。

---

## P3.1 行程持久化 + API

### 目标

将 SSE 流中生成的行程从 message `extra_info` 元数据提升为一等公民 DB 实体，并提供 REST 读写。

### 后端

| 项 | 路径 / 说明 |
|----|-------------|
| ORM 模型 | `backend/app/db/models/itinerary.py` — 表 `itineraries` |
| 迁移 | `backend/alembic/versions/20260602_0002_add_itineraries.py` |
| Repository | `backend/app/db/repositories/itinerary_repository.py` |
| Schemas | `backend/app/schemas/itinerary.py` |
| Service | `backend/app/services/itinerary_service.py` — upsert + session extra_info 同步 |
| API | `backend/app/api/v1/itineraries.py` |

**字段**：`id`, `session_id` FK, `user_id` FK, `days` JSON, `budget` JSON, `summary` text, `status` (`draft`/`approved`), `version` int, timestamps

**路由**（前缀 `/api/v1/itineraries`，需 JWT）：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/sessions/{session_id}` | 会话最新行程 |
| GET | `/{itinerary_id}` | 按 ID 查询 |
| PATCH | `/{itinerary_id}` | 手动编辑 days/budget/summary |

**流式完成钩子**：`chat_stream.py` 在 assistant 消息含 itinerary 时调用 service upsert，并同步 `travel_sessions.extra_info.itinerary`。

### 前端

| 项 | 说明 |
|----|------|
| `lib/api.ts` | `getItinerary(token, sessionId)` |
| `stores/chatStore.ts` | `loadHistory` 时并行拉取行程 |
| `types/itinerary.ts` | 已有 normalize；可选 `ItineraryResponse` 类型 |

---

## P3.2 WebSocket 流式（补充 SSE，不替换）

### 目标

与 SSE 发送相同事件 dict，供未来客户端或双通道场景使用；**ChatMain 仍用 SSE**。

### 后端

| 项 | 说明 |
|----|------|
| 共享生成器 | `iter_chat_events(...)` → `AsyncIterator[dict]` in `services/chat_stream.py` |
| SSE 包装 | `generate_sse_stream` 调用 `iter_chat_events` + `sse()` |
| WS 端点 | `GET /api/v1/chat/ws/{conversation_id}` — `backend/app/ws/chat_stream.py` |
| 认证 | Query `?token=` **或** 首帧 JSON `{"type":"auth","token":"..."}` |

**事件类型**（与 SSE 一致）：`token`, `tool_call`, `step`, `itinerary`, `approval_required`, `done`, `error`

### 前端

| 项 | 说明 |
|----|------|
| `lib/websocket.ts` | WS 连接、认证、帧解析 |
| `hooks/useTravelStream.ts` | 与 `useChatStream` 类似的事件回调 hook（**导出备用，ChatMain 未切换**） |

---

## P3.3 生产 Docker

| 文件 | 说明 |
|------|------|
| `infra/docker/backend.Dockerfile` | 多阶段 Python 镜像，uvicorn `:8200` |
| `infra/docker/frontend.Dockerfile` | Node 构建 + nginx 静态服务 |
| `infra/nginx/nginx.conf` | `/api` 反代 backend，SPA fallback |
| `docker-compose.prod.yml` | postgres + redis + backend + frontend/nginx |

**启动**：

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

访问：`http://localhost`（nginx 80）→ 前端；`/api/v1/*` → backend:8200

---

## P3.4 E2E 冒烟

| 项 | 说明 |
|----|------|
| 框架 | Playwright（根目录 `e2e/`） |
| 用例 | 加载 `/`，断言 auth overlay 品牌 `diao-travelagent` 或 Tab「登录」 |
| 配置 | `playwright.config.ts` — baseURL `http://localhost:5173` |

**运行**（需先 `pnpm dev` 或使用 preview）：

```bash
cd frontend && pnpm exec playwright install chromium
pnpm exec playwright test --config ../playwright.config.ts
```

不调用真实 LLM；仅 UI 冒烟。

---

## P3 延期（仅文档）

- ChromaDB / RAG 知识库入库
- 完整 CI pipeline（lint + test + build + deploy）
- ChatMain 从 SSE 迁移到 WebSocket

---

## 验收清单

- [ ] `pytest backend/tests/ -q --ignore=tests/integration` 通过
- [ ] `pnpm run build`（frontend）通过
- [ ] Playwright smoke 可运行（环境允许时）
- [ ] 手动：规划完成后 GET `/api/v1/itineraries/sessions/{id}` 返回行程
- [ ] 手动：`docker compose -f docker-compose.prod.yml config` 无语法错误
