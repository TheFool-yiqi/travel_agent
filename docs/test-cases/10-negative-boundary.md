# 异常与边界测试用例

> **模块：** NEG · **用例数：** 19 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖非法输入、服务降级、并发、LLM 失败兜底及边界条件。

---

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-NEG-001 | 空消息 stream | P1 | 异常 | ✅ | 已登录 | 1. POST content 空 | `""` | 422 或拒绝发送 |
| TC-NEG-002 | 仅空白字符消息 | P2 | 异常 | ✅ | — | 1. `"   "` | — | 同 TC-NEG-001 |
| TC-NEG-003 | 非法 UUID 会话 | P1 | 异常 | ✅ | 已登录 | 1. stream/history | `not-uuid` | 400 |
| TC-NEG-004 | 不存在会话 UUID | P1 | 异常 | ✅ | 已登录 | 1. 随机 UUID | — | 404 |
| TC-NEG-005 | 交通 enum 外输入 | P0 | 异常 | ✅ | plan_transport | 1. `坐船` | 非法 | 提示 flight/train/driving |
| TC-NEG-006 | 住宿 enum 外输入 | P1 | 异常 | ✅ | plan_stay_and_food | 1. 胡乱住宿 | — | 不写入；澄清 |
| TC-NEG-007 | 活动 enum 外输入 | P1 | 异常 | ✅ | plan_activities | 1. 无效活动 | — | 不推进 |
| TC-NEG-008 | 负数 travel_days | P1 | 异常 | ✅ | 问天数 | 1. `-1天` | — | 拒绝或澄清 |
| TC-NEG-009 | 超大 travel_days | P2 | 异常 | ✅ | — | 1. `999天` | — | 澄清合理上限 |
| TC-NEG-010 | 过去日期 departure_date | P1 | 异常 | ✅ | 问日期 | 1. `2020-01-01` | — | 警告或澄清 |
| TC-NEG-013 | MCP 全失败降级 | P1 | 异常 | ✅ | mock MCP | 1. refresh_step_mcp_tools fail | — | inprocess 工具；流程继续 |
| TC-NEG-016 | 并发双用户同 username 注册 | P2 | 异常 | ✅ | — | 1. 同时 register 同 username | — | 一个 201 一个 400 |
| TC-NEG-018 | 极长用户名注册 | P2 | 异常 | ✅ | — | 1. username 256 字符 | — | 422 |
| TC-NEG-019 | emoji 仅消息 | P3 | 异常 | ✅ | 收集中 | 1. `😀😀` | — | 友好回复；不脏槽 |
| TC-NEG-020 | SQL/XSS  payload 输入 | P1 | 安全 | ✅ | — | 1. 各槽注入串 | — | 存储安全；展示转义 |
| TC-NEG-022 | 修订中空修改意见 | P2 | 异常 | ✅ | approval | 1. `修改` 无具体内容 | — | 追问细节 |
| TC-NEG-023 | graph 缺 requires 字段 | P1 | 异常 | ✅ | 缺 transport | 1. assert_step_requirements | — | missing 列表非空 |
| TC-NEG-024 | sanitize 清除全部幻觉槽 | P0 | 异常 | ✅ | LLM 多填 | 1. sanitize_* | 无用户词 | 字段清空 |
| TC-NEG-025 | 无限 clarify 循环防护 | P1 | 异常 | ✅ | 连续模糊地名 | 1. 10 轮模糊 | — | 降级人工式追问或放弃 |

### TC-NEG-013 扩展说明（MCP 降级）

- **代码：** `step_config.refresh_step_mcp_tools` except → 空 hotel + 默认 search/date
- **自动化：** `test_smoke` 间接覆盖；`test_mcp_manager.py` 单元
- **预期：** Graph 仍可完成主路径（可能无实时票价）

---

## 与冒烟异常路径对照

| 冒烟场景 | 对应用例 |
|----------|----------|
| E1 程度→成都 | TC-NEG-005 同类 + TC-FLOW-040 |
| E2 整个假期 | TC-NEG-008~009 边界 + TC-FLOW-050 |
| E3 预算防幻觉 | TC-NEG-024 |
| E6 天数兜底 | TC-NEG-025 |
| E7 预算歧义 | TC-NEG-001 同类 clarify |
| MCP/LLM 失败 | TC-NEG-011~013 |

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_smoke_flows.py` (smoke_exception) | TC-NEG-024 |
| `test_step_config.py` | TC-NEG-013, 023 |
| `test_sessions_api.py` | TC-NEG-004 |
| `test_anti_hallucination.py` | TC-NEG-024 |

## 执行建议

- **P0 异常：** TC-NEG-005, 013, 014, 024 — 纳入冒烟扩展
- **手动探索：** TC-NEG-017, 025 — 季度全量
