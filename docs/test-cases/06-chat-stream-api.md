# 对话流与 API 测试用例

> **模块：** CHAT / API · **用例数：** 49 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 SSE（`POST /api/v1/chat/stream/{id}`）、WebSocket（`/api/v1/chat/ws/{id}`）、REST 错误码及 `chat_stream` 服务。

---

## TC-CHAT 对话流（001–025）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-CHAT-001 | SSE stream 基本流式 | P0 | 接口 | ✅ | 已登录+会话 | 1. POST stream 2. 读 SSE | `你好` | Content-Type: text/event-stream；有 token 事件 |
| TC-CHAT-002 | SSE 最终 message 事件 | P0 | 接口 | ✅ | 同上 | 1. 消费至结束 | — | 含完整 assistant 消息 |
| TC-CHAT-003 | SSE step 进度事件 | P1 | 接口 | ✅ | 规划阶段 | 1. 监听 step 类型 | — | current_step 与 graph 一致 |
| TC-CHAT-004 | SSE 消息持久化 | P0 | 功能 | ✅ | stream 完成 | 1. GET history | — | user+assistant 均入库 |
| TC-CHAT-005 | GET chat history | P0 | 接口 | ✅ | 会话有消息 | 1. GET `/chat/history/{id}` | — | conversation + messages 数组 |
| TC-CHAT-006 | history 404 已删会话 | P0 | 接口 | ✅ | 会话已删 | 1. GET history | deleted id | 404 |
| TC-CHAT-007 | stream 404 他人会话 | P0 | 安全 | ✅ | 跨用户 | 1. POST stream | — | 404 或 403 |
| TC-CHAT-008 | stream 空 content | P1 | 异常 | ✅ | 已登录 | 1. POST content=`""` | 空 | 422 或友好错误 |
| TC-CHAT-009 | stream 超长 content | P2 | 异常 | ✅ | — | 1. 10k 字符 | 超长 | 截断或 422；服务不崩 |
| TC-CHAT-010 | WebSocket 连接 query token | P0 | 接口 | ✅ | 有效 JWT | 1. WS `?token=` 连接 | — | 连接成功 |
| TC-CHAT-011 | WebSocket 首帧 auth | P0 | 接口 | ✅ | — | 1. 连接后发 `{type:auth,token}` | — | 认证成功 |
| TC-CHAT-012 | WebSocket 无效 token 4401 | P0 | 安全 | ✅ | 无效 token | 1. 连接 | — | close code 4401 |
| TC-CHAT-013 | WebSocket 发消息收事件 | P0 | 接口 | ✅ | 已认证 WS | 1. 发 user message 2. 收 JSON 事件 | — | 与 SSE 事件结构一致 |
| TC-CHAT-018 | generate_sse_stream 错误降级 | P1 | 异常 | ✅ | mock graph 异常 | 1. stream | — | SSE error 事件；HTTP 仍 200 或 500 明确 |
| TC-CHAT-019 | iter_chat_events 共享逻辑 | P1 | 功能 | ✅ | — | 1. 单元测 chat_stream | — | WS/SSE 同源 |
| TC-CHAT-021 | history 消息顺序 | P1 | 功能 | ✅ | 多轮 | 1. GET history | — | 按 created_at 升序 |
| TC-CHAT-023 | 前端 ChatInput 发送触发 SSE | P0 | UI | ✅ | e2e 环境 | 1. 输入发送 | main-path | 消息出现在 MessageList |
| TC-CHAT-024 | TypingIndicator 流式显示 | P2 | UI | ✅ | stream 中 | 1. 观察 UI | — | 打字指示器显示/隐藏 |
| TC-CHAT-025 | MessageBubble 角色样式 | P2 | UI | ✅ | 有历史 | 1. 查看气泡 | user/assistant | 样式区分 |

---

## TC-API REST 接口（001–030）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-API-001 | health 健康检查 | P0 | 接口 | ✅ | 服务启动 | 1. GET `/health` | — | 200 ok |
| TC-API-002 | users register 201 | P0 | 接口 | ✅ | — | 1. POST register | 合法 body | 201 |
| TC-API-003 | users login 200 | P0 | 接口 | ✅ | 已注册 | 1. POST login | — | 200 + token |
| TC-API-004 | users me 401 无 Token | P0 | 接口 | ✅ | — | 1. GET /me | 无头 | 401 |
| TC-API-005 | sessions POST 401 | P0 | 接口 | ✅ | — | 1. 无 Token 创建 | — | 401 |
| TC-API-006 | sessions GET list 200 | P0 | 接口 | ✅ | 已登录 | 1. GET list | — | 200 数组 |
| TC-API-007 | sessions GET 404 不存在 | P0 | 接口 | ✅ | — | 1. 随机 UUID | — | 404 |
| TC-API-008 | sessions DELETE 204 | P0 | 接口 | ✅ | 自有会话 | 1. DELETE | — | 204 |
| TC-API-009 | chat history 401 | P0 | 接口 | ✅ | — | 1. 无 Token | — | 401 |
| TC-API-010 | chat stream 401 | P0 | 接口 | ✅ | — | 1. 无 Token stream | — | 401 |
| TC-API-011 | 无效 UUID 400 | P1 | 接口 | ✅ | 已登录 | 1. id=`abc` | — | 400 无效会话 ID |
| TC-API-012 | itineraries GET 200 | P1 | 接口 | ✅ | 有行程 | 1. GET itinerary | session_id | 200 JSON |
| TC-API-013 | itineraries GET 404 | P1 | 接口 | ✅ | 无行程 | 1. GET | — | 404 |
| TC-API-014 | itineraries PATCH 200 | P2 | 接口 | ✅ | 有行程 | 1. PATCH 局部 | — | 200 |
| TC-API-015 | semantic-metrics GET 200 | P1 | 接口 | ✅ | 有对话 | 1. GET metrics | — | SemanticMetricsResponse |
| TC-API-016 | 422 请求体校验失败 | P1 | 接口 | ✅ | — | 1. register 缺字段 | — | 422 Unprocessable |
| TC-API-017 | CORS 预检 OPTIONS | P2 | 接口 | ✅ | 浏览器跨域 | 1. OPTIONS | — | 允许前端 origin |
| TC-API-018 | API v1 前缀统一 | P2 | 接口 | ✅ | — | 1. 确认路径 | — | 均 `/api/v1/*` |
| TC-API-019 | conversations 别名路径 | P2 | 接口 | ✅ | — | 1. 用 /conversations CRUD | — | 同 sessions |
| TC-API-020 | OpenAPI docs 可访问 | P3 | 接口 | ✅ | — | 1. GET `/docs` | — | Swagger UI |
| TC-API-021 | 403 停用账号 | P1 | 接口 | ✅ | is_active=false | 1. 任意受保护 API | — | 403 |
| TC-API-022 | Bearer 格式错误 401 | P0 | 安全 | ✅ | — | 1. Authorization: Basic xxx | — | 401 |
| TC-API-023 | 重复 register 400 | P0 | 接口 | ✅ | 重复用户名 | 1. POST | — | 400 |
| TC-API-024 | login 错误密码 401 | P0 | 接口 | ✅ | — | 1. 错密码 | — | 401 |
| TC-API-025 | MessageCreate schema | P2 | 接口 | ✅ | — | 1. test_message_schemas | — | content 必填 |
| TC-API-026 | ConversationResponse schema | P2 | 接口 | ✅ | — | 1. test_conversation_schemas | — | 字段齐全 |
| TC-API-027 | rate limit（若启用） | P3 | 安全 | ✅ | — | 1.  burst 请求 | — | 429 或 N/A |
| TC-API-028 | lifespan MCP 启动 | P1 | 功能 | ✅ | 应用启动 | 1. test_lifespan | — | MCP 工具加载 |
| TC-API-029 | 404 未知路由 | P2 | 接口 | ✅ | — | 1. GET `/api/v1/nope` | — | 404 |
| TC-API-030 | JSON 非法 body 422 | P2 | 接口 | ✅ | — | 1. POST 非 JSON | — | 422 |

### TC-CHAT-010~013 扩展说明（WebSocket · 冒烟缺口）

- **路径：** `backend/app/ws/chat_stream.py` → `/api/v1/chat/ws/{conversation_id}`
- **认证：** Query `?token=` 或首帧 `{"type":"auth","token":"..."}`
- **现状：** 自动化 ⏳；smoke README 标注 WebSocket 为覆盖缺口
- **预期：** 与 `generate_sse_stream` / `iter_chat_events` 输出一致

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_chat_stream.py` | TC-CHAT-001~004, 019 |
| `test_chat_api.py` | TC-CHAT-005~006, TC-API-009~011 |
| `test_users_api.py` | TC-API-002~004, 023~024 |
| `test_sessions_api.py` | TC-API-005~008, 015 |
| `test_itineraries_api.py` | TC-API-012~014 |
| `e2e/main-path.spec.ts` | TC-CHAT-023 |

## 流程关联

- 全部 FLOW 均依赖 TC-CHAT-001 SSE 通路
- FLOW-12：TC-API-004, 010 + TC-CHAT-007
