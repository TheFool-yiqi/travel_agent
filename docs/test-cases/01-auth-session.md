# 认证与会话测试用例

> **模块：** AUTH / SESS · **用例数：** 45 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 `backend/app/api/v1/users.py`、`sessions.py`、JWT 鉴权及前端 `AuthOverlay` 相关会话生命周期。

---

## TC-AUTH 用户认证（001–020）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-AUTH-001 | 新用户注册成功 | P0 | 接口 | ✅ | 后端已启动；用户名/邮箱未占用 | 1. POST `/api/v1/users/register` | username=`testuser01`, email=`u01@test.com`, password=`Pass123!` | 201；返回 `access_token` + `user` 对象 |
| TC-AUTH-002 | 注册后自动获得 Token | P0 | 接口 | ✅ | 同 TC-AUTH-001 | 1. 注册 2. 检查响应字段 | 同上 | `access_token` 非空；`token_type=bearer` |
| TC-AUTH-003 | 重复用户名注册拒绝 | P0 | 接口 | ✅ | 用户名已存在 | 1. 用相同 username 再次注册 | 已存在用户名 | 400；detail=`用户名已存在` |
| TC-AUTH-004 | 重复邮箱注册拒绝 | P1 | 接口 | ✅ | 邮箱已注册 | 1. 新 username + 已存在 email 注册 | email 重复 | 400；detail=`邮箱已被注册` |
| TC-AUTH-005 | 登录成功返回 Token | P0 | 接口 | ✅ | 用户已注册 | 1. POST `/api/v1/users/login` | 正确 username/password | 200；返回有效 JWT |
| TC-AUTH-006 | 错误密码登录失败 | P0 | 接口 | ✅ | 用户已注册 | 1. 登录时提交错误密码 | password 错误 | 401；detail=`用户名或密码错误` |
| TC-AUTH-007 | 不存在用户登录失败 | P1 | 接口 | ✅ | — | 1. 用未注册用户名登录 | username=`nouser` | 401 |
| TC-AUTH-008 | 停用账号登录拒绝 | P1 | 接口 | ✅ | 用户 `is_active=false` | 1. 尝试登录 | 停用账号 | 403；detail=`账号已停用` |
| TC-AUTH-009 | GET /me 需 Bearer Token | P0 | 接口 | ✅ | — | 1. 无 Authorization 调用 `/api/v1/users/me` | 无 Token | 401 Unauthorized |
| TC-AUTH-010 | GET /me 有效 Token 返回用户信息 | P0 | 接口 | ✅ | 已登录获 Token | 1. 带 Bearer 调用 `/me` | 有效 JWT | 200；username/email 与注册一致 |
| TC-AUTH-011 | 过期 Token 访问受保护接口 | P0 | 安全 | ✅ | 构造过期 JWT | 1. 用过期 Token 调 `/me` 或 `/sessions` | exp 已过期 | 401 |
| TC-AUTH-012 | 篡改 Token 签名拒绝 | P0 | 安全 | ✅ | 有效 Token | 1. 修改 payload 后请求 | 篡改 JWT | 401 |
| TC-AUTH-013 | 密码哈希不入响应 | P0 | 安全 | ✅ | 注册成功 | 1. 检查 register/login/me 响应 | — | 响应体不含 `password_hash` |
| TC-AUTH-014 | 注册密码强度校验 | P2 | 接口 | ✅ | — | 1. 提交过短/纯数字密码 | password=`123` | 422 校验失败（若 schema 启用） |
| TC-AUTH-015 | 注册邮箱格式校验 | P2 | 接口 | ✅ | — | 1. 提交非法 email | email=`not-an-email` | 422 |
| TC-AUTH-016 | 前端未登录显示 AuthOverlay | P0 | UI | ✅ | 前端 `:5173` 已启动 | 1. 打开首页 2. 观察浮层 | — | 显示登录/注册 Tab；不可进入主界面 |
| TC-AUTH-017 | 前端注册后进入主界面 | P0 | UI | ✅ | backend 可达 | 1. 在 AuthOverlay 注册 2. 提交 | e2e/helpers 随机用户 | 浮层关闭；Sidebar「我的行程」可见 |
| TC-AUTH-018 | 前端登录 Tab 切换 | P2 | UI | ✅ | 打开首页 | 1. 点击「注册」Tab 2. 切回「登录」 | — | 表单字段切换正确 |
| TC-AUTH-019 | Token 持久化 localStorage | P1 | UI | ✅ | 登录成功 | 1. 刷新页面 | — | 仍保持登录态；不重复弹出 AuthOverlay |
| TC-AUTH-020 | 401 全局 Toast 并弹出登录 | P0 | UI | ✅ | 已登录；Token 失效 | 1. 触发 API 401 | 过期 Token | Toast 提示；AuthOverlay 重新显示 |

### TC-AUTH-001 扩展说明（P0）

- **关联自动化：** `backend/tests/test_users_api.py::test_register_success`
- **关联 E2E：** `e2e/auth.spec.ts`「注册后进入主界面」
- **API 路径：** `POST /api/v1/users/register`

---

## TC-SESS 会话管理（001–025）

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-SESS-001 | 创建新会话 | P0 | 接口 | ✅ | 已登录 | 1. POST `/api/v1/sessions` 或 `/conversations` | title 可选 | 201；返回 session id、thread_id |
| TC-SESS-002 | 创建会话自动 seed 问候 | P0 | 功能 | ✅ | 新建会话 | 1. 创建 2. GET history | — | 首条 assistant 消息为 bootstrap 问候 |
| TC-SESS-003 | 列出用户会话列表 | P0 | 接口 | ✅ | 用户有 ≥1 会话 | 1. GET `/api/v1/sessions` | — | 200；仅当前用户会话；不含已删除 |
| TC-SESS-004 | 获取会话详情 | P1 | 接口 | ✅ | 会话属于当前用户 | 1. GET `/api/v1/sessions/{id}` | 有效 UUID | 200；字段完整 |
| TC-SESS-005 | 软删除会话 | P0 | 接口 | ✅ | 会话存在 | 1. DELETE `/api/v1/sessions/{id}` | 有效 id | 204；status=deleted |
| TC-SESS-006 | 删除后不可再访问 | P0 | 接口 | ✅ | 会话已删除 | 1. GET 详情 2. POST stream | 已删 id | 404 `会话不存在` |
| TC-SESS-007 | 访问他人会话拒绝 | P0 | 安全 | ✅ | 用户 A/B 各一会话 | 1. A 的 Token 访问 B 的 session | 跨用户 id | 404（不泄露存在性） |
| TC-SESS-008 | 无效 UUID 会话 ID | P1 | 接口 | ✅ | 已登录 | 1. GET `/sessions/not-a-uuid` | 非法 id | 400 `无效的会话 ID` |
| TC-SESS-009 | 继续旧会话非重复 bootstrap | P1 | 功能 | ✅ | 已有历史消息的会话 | 1. 打开旧会话 2. 发送消息 | 旧 session | 不重复插入问候；从 checkpoint 继续 |
| TC-SESS-010 | 更新会话标题 | P2 | 接口 | ✅ | 会话存在 | 1. PATCH `/sessions/{id}` | title=`成都三日游` | 200；title 更新 |
| TC-SESS-011 | 前端「规划新行程」创建会话 | P0 | UI | ✅ | 已登录 | 1. 点击「规划新行程」 | — | 新会话选中；ChatMain 显示问候 |
| TC-SESS-012 | Sidebar 会话列表展示 | P1 | UI | ✅ | 多会话 | 1. 查看 ConversationList | — | 按时间排序；标题可读 |
| TC-SESS-013 | 切换会话加载历史 | P0 | UI | ✅ | ≥2 会话 | 1. 点击另一会话 | — | MessageList 切换；StepProgress 同步 |
| TC-SESS-014 | 删除会话 UI 确认 | P1 | UI | ✅ | 会话存在 | 1. 点击删除 2. 确认 | — | 列表移除；不可再选 |
| TC-SESS-015 | 移动端 MobileSessionDrawer | P2 | UI | ✅ | 窄屏 viewport | 1. 打开 drawer 2. 选会话 | width<768 | drawer 可用；与 Sidebar 行为一致 |
| TC-SESS-016 | semantic-metrics 接口 | P1 | 接口 | ✅ | 会话有对话 | 1. GET `/sessions/{id}/semantic-metrics` | — | 200；含槽位命中率等聚合 |
| TC-SESS-017 | semantic-metrics 无权限 | P1 | 安全 | ✅ | 他人会话 id | 1. 带 Token 请求 metrics | 跨用户 | 404 |
| TC-SESS-018 | thread_id 与 LangGraph 绑定 | P1 | 功能 | ✅ | 新建会话 | 1. 创建 2. 发消息 3. 查 checkpoint | — | thread_id 贯穿 graph 状态 |
| TC-SESS-019 | 会话 extra_info 持久化 | P3 | 接口 | ✅ | — | 1. 创建时传 extra_info | JSON 元数据 | 创建成功；GET 可回读 |
| TC-SESS-020 | 并发创建多会话 | P2 | 异常 | ✅ | 已登录 | 1. 快速连续 POST 5 次 | — | 均 201；列表含 5 条 |
| TC-SESS-021 | 空 title 默认「新对话」 | P2 | 接口 | ✅ | 已登录 | 1. POST 不传 title | — | title=`新对话` |
| TC-SESS-022 | 会话列表排除 deleted | P0 | 接口 | ✅ | 1 正常 + 1 已删 | 1. GET list | — | 仅返回未删除 |
| TC-SESS-023 | Handoffs 别名 /conversations | P2 | 接口 | ✅ | 已登录 | 1. 用 `/conversations` 路径 CRUD | — | 与 `/sessions` 行为一致 |
| TC-SESS-024 | 未登录创建会话 401 | P0 | 安全 | ✅ | 无 Token | 1. POST `/sessions` | — | 401 |
| TC-SESS-025 | 会话与 itinerary 关联 | P1 | 功能 | ✅ | 走完 build_itinerary | 1. GET `/api/v1/itineraries/{session_id}` | — | 返回行程 JSON |

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `backend/tests/test_users_api.py` | TC-AUTH-001~007, 009~010, 013 |
| `backend/tests/test_sessions_api.py` | TC-SESS-001~006, 021~022, 024 |
| `backend/tests/test_auth_deps.py` | TC-AUTH-009~011 |
| `e2e/auth.spec.ts` | TC-AUTH-016~017 |
| `e2e/main-path.spec.ts` | TC-SESS-011 |

## 流程关联

- FLOW-01：TC-AUTH-002, TC-SESS-002
- FLOW-12：TC-AUTH-020, TC-SESS-024
- FLOW-13：TC-SESS-005~006
