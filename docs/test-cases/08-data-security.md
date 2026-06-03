# 数据持久化与安全测试用例

> **模块：** DATA / SEC · **用例数：** 30 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 PostgreSQL 模型、LangGraph Checkpoint、JWT 权限及数据隔离。

---

## TC-DATA 数据持久化（001–015）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-DATA-001 | User 模型 CRUD | P0 | 功能 | ✅ | DB 可用 | 1. repo create/get | — | 字段持久化正确 |
| TC-DATA-002 | LangGraph Checkpoint 恢复 | P0 | 功能 | ✅ | 会话中断前 | 1. 刷新/新请求 2. 查 state | — | current_step/槽位保留 |
| TC-DATA-003 | TravelSession thread_id 唯一 | P1 | 功能 | ⏳ | 创建会话 | 1. 查 DB | — | thread_id 非空且关联 graph |
| TC-DATA-004 | Message 按会话列表 | P0 | 功能 | ✅ | 多轮对话 | 1. MessageRepository.list | — | 顺序与 session 隔离 |
| TC-DATA-005 | 软删除会话 status | P0 | 功能 | ✅ | DELETE session | 1. 查 DB status | — | deleted；非物理删 |
| TC-DATA-006 | Itinerary JSON 存储 | P1 | 功能 | ✅ | build 完成 | 1. itinerary repo | — | JSON 可序列化/反读 |
| TC-DATA-007 | user_requirement 在 checkpoint | P0 | 功能 | ⏳ | collect 确认后 | 1. get_state | — | user_requirement 完整 |
| TC-DATA-008 | preferences 用户级持久化 | P2 | 功能 | ⏳ | 更新偏好 | 1. 写 users.preferences | — | 跨会话可读 |
| TC-DATA-009 | seed_initial_greeting 幂等 | P1 | 功能 | ✅ | 创建会话 | 1. 仅一条 greeting | — | 不重复 insert |
| TC-DATA-010 | 消息 metadata semantic_trace | P2 | 功能 | ✅ | pipeline 运行 | 1. 查 message extra | — | trace 可提取 |
| TC-DATA-011 | 数据库迁移 init_db | P1 | 功能 | ✅ | 空库 | 1. make init-db | — | 表齐全 |
| TC-DATA-012 | 会话列表 exclude_deleted | P0 | 功能 | ✅ | 有 deleted | 1. list_for_user | — | 不返回 deleted |
| TC-DATA-013 | checkpoint 与 session 生命周期 | P1 | 功能 | ⏳ | 删会话后 | 1. 尝试 resume | — | 404；不读旧 checkpoint |
| TC-DATA-014 | Redis 连接（若用于 checkpoint） | P2 | 功能 | ⏳ | docker-up | 1. 配置 REDIS_URL | — | graph 可持久化 |
| TC-DATA-015 | 并发写消息顺序 | P2 | 异常 | ❌ | — | 1. 快速连发 | — | created_at 单调 |

---

## TC-SEC 安全（001–015）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-SEC-001 | JWT 密钥非默认（生产） | P0 | 安全 | ❌ | 生产配置 | 1. 查 JWT_SECRET | — | 非 example 值 |
| TC-SEC-002 | 密码 bcrypt/scrypt 哈希 | P0 | 安全 | ✅ | 注册用户 | 1. 查 DB password_hash | — | 非明文 |
| TC-SEC-003 | 跨用户会话隔离 | P0 | 安全 | ⏳ | 用户 A/B | 1. A token 访问 B session | — | 404 |
| TC-SEC-004 | 跨用户 itinerary 隔离 | P0 | 安全 | ⏳ | 同上 | 1. GET itinerary | — | 404/403 |
| TC-SEC-005 | 未授权 stream 401 | P0 | 安全 | ⏳ | — | 1. 无 Token stream | — | 401 |
| TC-SEC-006 | SQL 注入 username | P1 | 安全 | ❌ | — | 1. login 特殊字符 | `' OR 1=1--` | 401；无 SQL 错误 |
| TC-SEC-007 | XSS 消息内容存储 | P1 | 安全 | ❌ | — | 1. 发送 `<script>` | — | 前端转义；不执行 |
| TC-SEC-008 | CORS 限制来源 | P2 | 安全 | ❌ | — | 1. 非法 Origin | — | 拒绝或 N/A |
| TC-SEC-009 | Token 不在 URL 日志（除 WS） | P2 | 安全 | ❌ | — | 1. 查 access log | — | 敏感信息脱敏 |
| TC-SEC-010 | 停用账号全 API 403 | P1 | 安全 | ❌ | is_active=false | 1. 各受保护端点 | — | 403 |
| TC-SEC-011 | auth_deps get_current_user | P0 | 安全 | ✅ | — | 1. test_auth_deps | — | 无效 token 拒绝 |
| TC-SEC-012 | WS 4401 无效 token | P0 | 安全 | ⏳ | — | 1. WS 错 token | — | 关闭连接 |
| TC-SEC-013 | 敏感字段不出 API | P0 | 安全 | ✅ | register/me | 1. 查响应 | — | 无 password_hash |
| TC-SEC-014 | 401 前端清 token 重登 | P0 | UI | ⏳ | 过期 token | 1. API 401 | — | localStorage 清；AuthOverlay |
| TC-SEC-015 | rate limit / 防 brute force | P3 | 安全 | ❌ | — | 1. 连续错误登录 | — | 锁定或 429（若实现） |

### TC-DATA-002 扩展说明（FLOW-06）

- **场景：** 需求收集中途刷新浏览器
- **预期：** 从 LangGraph checkpoint 恢复；已填槽位不丢；继续当前 guidance
- **自动化：** `backend/tests/test_checkpoint.py`

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_checkpoint.py` | TC-DATA-002, 007 |
| `test_db_models.py` | TC-DATA-001 |
| `test_sessions_api.py` | TC-DATA-005, 012 |
| `test_security.py` | TC-SEC-002, 011, 013 |
| `test_auth_deps.py` | TC-SEC-005, 011 |

## 流程关联

- FLOW-06：TC-DATA-002
- FLOW-12：TC-SEC-005, 014
- FLOW-13：TC-DATA-005, TC-SEC-003
