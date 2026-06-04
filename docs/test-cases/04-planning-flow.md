# LangGraph 规划流程测试用例

> **模块：** PLAN · **用例数：** 39 · **版本：** v2.0 · **更新：** 2026-06-03

覆盖 8 个 Graph 节点（含 `inject_user_memory`）、`step_router`、交通/食宿/活动枚举、MCP grounding、`build_itinerary` 预算警告。

**节点顺序：** inject_user_memory → collect_requirements → plan_destination → plan_transport → plan_stay_and_food → plan_activities → build_itinerary → approval_node → final_response

---

| 用例编号 | 用例名称 | 优先级 | 类型 | 自动化 | 前置条件 | 测试步骤 | 测试数据 | 预期结果 |
|----------|----------|--------|------|--------|----------|----------|----------|----------|
| TC-PLAN-002 | plan_destination 需 user_confirmed | P0 | 功能 | ✅ | collect 完成未确认 | 1. route_after_collect | — | 不进入 destination |
| TC-PLAN-003 | plan_destination 确认已选目的地 | P0 | 功能 | ✅ | req 含 destination | 1. 进入节点 | 北京 | 「目的地已确认：北京」→ transport |
| TC-PLAN-005 | plan_destination MCP/RAG 工具 | P1 | 功能 | ✅ | MCP 可用 | 1. 观察工具调用 | query_destination_info | 可出现检索提示 |
| TC-PLAN-006 | route_after_destination→transport | P0 | 功能 | ✅ | selected_destination 有值 | 1. 断言路由 | — | next=plan_transport |
| TC-PLAN-009 | 选择 train 高铁 | P0 | 功能 | ✅ | transport 步 | 1. `高铁` | train | selected_transport=train |
| TC-PLAN-010 | 选择 driving 自驾 | P1 | 功能 | ✅ | transport 步 | 1. `自驾` | driving | selected_transport=driving |
| TC-PLAN-011 | 无效交通方式拒绝 | P0 | 功能 | ✅ | transport 步 | 1. `坐船` | 非法 | 提示选 flight/train/driving；不推进 |
| TC-PLAN-012 | transport MCP grounding | P1 | 功能 | ✅ | MCP 配置 | 1. query_transport_options | 上海→北京 | 返回选项或降级文案 |
| TC-PLAN-013 | route_after_transport→stay_food | P0 | 功能 | ✅ | selected_transport 有值 | 1. 断言路由 | train | next=plan_stay_and_food |
| TC-PLAN-014 | 住宿四枚举 economy/star/hostel/youth | P0 | 功能 | ✅ | stay 步 | 1. 分别选择 | economy_hotel 等 | selected_accommodation_types 正确 |
| TC-PLAN-017 | 无效住宿类型 | P1 | 异常 | ✅ | stay 步 | 1. `胶囊太空舱` | — | 澄清或忽略；不写入非法 enum |
| TC-PLAN-018 | route_after_stay→activities | P0 | 功能 | ✅ | acc+food 均有 | 1. 断言路由 | — | next=plan_activities |
| TC-PLAN-020 | 多选活动类型 | P2 | 功能 | ✅ | activities 步 | 1. `文化+美食` | — | 多 enum 写入 |
| TC-PLAN-021 | 无效活动类型 | P1 | 异常 | ✅ | activities 步 | 1. `极限跳伞` | — | 不写入；提示重选 |
| TC-PLAN-022 | route_after_activities→build | P0 | 功能 | ✅ | activity 已选 | 1. 断言路由 | — | next=build_itinerary |
| TC-PLAN-023 | build_itinerary 生成逐日结构 | P0 | 功能 | ✅ | 前置选择齐全 | 1. 运行节点 | 3天 | itinerary 数组 day_number 1..N |
| TC-PLAN-024 | build_itinerary 预算拆分 | P0 | 功能 | ✅ | — | 1. 查 budget 对象 | — | transport/accommodation/food/attractions/misc |
| TC-PLAN-026 | route_after_itinerary→approval | P0 | 功能 | ✅ | itinerary 非空 | 1. 断言路由 | — | next=approval_node |
| TC-PLAN-027 | step_config requires 校验 | P1 | 功能 | ✅ | 缺 selected_transport | 1. assert_step_requirements | — | missing 含字段名 |
| TC-PLAN-028 | rollback_targets 配置完整 | P2 | 功能 | ✅ | — | 1. 读 step_config | 各 step | rollback 列表非空（collect 除外） |
| TC-PLAN-029 | STEP_LABELS 与前端一致 | P1 | UI | ✅ | — | 1. 对比 StepProgress STEPS | 8 步 | label 一致 |
| TC-PLAN-031 | nl_extract 交通映射 | P1 | 功能 | ✅ | — | 1. 测中英文映射 | 飞机→flight | 映射正确 |
| TC-PLAN-033 | flight_subagent 查询 | P2 | 功能 | ✅ | flight 选 | 1. 触发 subagent | — | 不抛错；有占位/真实数据 |
| TC-PLAN-034 | train_subagent 查询 | P2 | 功能 | ✅ | train 选 | 1. 同上 | — | 正常返回 |
| TC-PLAN-035 | driving_subagent 查询 | P2 | 功能 | ✅ | driving 选 | 1. 同上 | — | 正常返回 |
| TC-PLAN-036 | transport_coordinator 协调 | P2 | 功能 | ✅ | — | 1. 单元测试 | — | 路由至正确 subagent |
| TC-PLAN-037 | MCP hotel 工具 stay 步 | P1 | 功能 | ✅ | MCP 加载 | 1. refresh_step_mcp_tools | — | hotel tools 注入 stay 步 |
| TC-PLAN-038 | MCP 加载失败降级 | P1 | 异常 | ✅ | mock MCP fail | 1. refresh 失败 | — | 使用 inprocess 工具；graph 仍跑 |
| TC-PLAN-039 | checkpoint 跨步持久化 | P0 | 功能 | ✅ | 每步结束 | 1. 查 checkpoint | — | current_step/selections 保留 |
| TC-PLAN-040 | middleware 步骤守卫 | P2 | 功能 | ✅ | — | 1. test_graph_middleware | — | 非法跳步被拦 |
| TC-PLAN-041 | 主路径规划链 smoke | P0 | 回归 | ✅ | 需求已确认 | 1. smoke_main routing 测试 | — | 链式路由全绿 |
| TC-PLAN-042 | build 空 itinerary 不推进 | P1 | 异常 | ✅ | mock 失败 | 1. itinerary=[] | — | 停留 build 或报错 |
| TC-PLAN-043 | 天数与 itinerary 长度一致 | P1 | 功能 | ✅ | travel_days=3 | 1. 数 day 条目 | — | len=3 |
| TC-PLAN-044 | 人数影响 budget 乘数 | P1 | 功能 | ✅ | party=2 | 1. 对比 budget | — | 费用随人数缩放 |
| TC-PLAN-045 | stream_callback 步进事件 | P2 | 功能 | ✅ | SSE 流 | 1. 监听 step 事件 | — | 前端 StepProgress 更新 |
| TC-PLAN-046 | destination_router 分支 | P1 | 功能 | ✅ | — | 1. test_destination_router | — | 路由正确 |
| TC-PLAN-047 | step_router normalize 别名 | P2 | 功能 | ✅ | — | 1. STEP_ALIASES | transport_planning | →plan_transport |
| TC-PLAN-049 | plan 阶段 progress 8 步均可达 | P0 | UI | ✅ | 主路径 | 1. 手动/e2e 走全流程 | smoke 数据 | 8 阶段均 active/done |
| TC-PLAN-050 | itineraries API 读回 | P1 | 接口 | ✅ | build 完成 | 1. GET `/itineraries/{session_id}` | — | JSON 与 state 一致 |

### TC-PLAN-025 扩展说明（P0）

- **模块：** `backend/app/graph/nodes/build_itinerary.py`
- **条件：** `budget_max` 明显低于分项估算总和
- **预期：** 助手正文含超预算提示；可选 Plan B（降档住宿/减少活动）
- **自动化：** `test_build_itinerary.py`（部分）

---

## 枚举速查

| 类别 | 合法值 |
|------|--------|
| 交通 | `flight`, `train`, `driving` |
| 住宿 | `star_hotel`, `economy_hotel`, `hostel`, `youth_hostel` |
| 餐饮 | `specialty`, `chain`, `local` |
| 活动 | `culture`, `nature`, `food_tour`, `shopping`, `family_fun` |

---

## 自动化映射

| 测试文件 | 覆盖用例 |
|----------|----------|
| `test_smoke_flows.py` (smoke_main) | TC-PLAN-006, 013, 018, 022, 026, 041 |
| `test_build_itinerary.py` | TC-PLAN-023~025 |
| `test_plan_activities.py` | TC-PLAN-019 |
| `test_transport_grounding.py` | TC-PLAN-012 |
| `test_step_config.py` / `test_step_router.py` | TC-PLAN-027~028, 047 |
| `e2e/main-path.spec.ts` | TC-PLAN-049 |

## 流程关联

- FLOW-03：TC-PLAN-003~026, 049
