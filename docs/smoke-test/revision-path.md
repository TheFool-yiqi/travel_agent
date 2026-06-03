# 冒烟测试 — 修订路径

在行程生成后走「请求修改 → 重新生成 → 确认」分支。

> 依赖主路径已完成至 `build_itinerary`（见 [main-path.md](./main-path.md) 第 6 步）。

## 自动化

```bash
uv run pytest backend/tests/test_smoke_flows.py -m smoke_revision -q
```

## 手动步骤

### 前置

- 同主路径，直至右侧出现行程卡片 + 底部「行程已生成，请确认或提出修改」横幅
- 进度条停在 **确认**

### 修订流程

| # | 操作 | 预期 |
|---|------|------|
| 1 | 点击「请求修改」或发送 `第三天改成逛胡同，少安排购物` | 助手：「收到修改意见…正在重新生成」 |
| 2 | 等待流式结束 | 进度回到 **行程**；新卡片覆盖旧行程 |
| 3 | 检查内容 | 与修改意见相关（或至少结构完整：每日 + 预算） |
| 4 | 点击「确认行程」或发送 `确认` | → **完成** |
| 5 | 检查订单 | 含 `ORDER-` 前缀订单号 |

### 关键词（对话式）

| 意图 | 示例输入 |
|------|----------|
| 确认 | `确认` / `确认行程` / `OK` |
| 修改 | `修改行程` / `第三天…` / `change hotel` |

## Checklist

```
□ 修订后 itinerary 重新生成（非空）
□ approval_status 从 pending 经 revising 回到可确认
□ 二次确认可生成订单
□ 不出现无限「仍在等待您的确认」循环（有明确修改内容时）
```

## 与 Graph 的对应关系

```
build_itinerary → approval_node (pending)
  → 用户修改 → revise_itinerary → build_itinerary → approval_node
  → 用户确认 → final_response
```
