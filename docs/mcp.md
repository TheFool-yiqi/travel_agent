# MCP 集成规范

> 详细架构见 [architecture.md](architecture.md)。

## 设计原则

```
Agent/Node → tools/xxx.py → mcp/registry.py → mcp/adapters/ → mcp/client.py
```

- Agent 和 Graph 节点**不直接**调用 MCP
- `tools/` 是业务入口，`mcp/` 是协议层
- 同一能力不得在 `tools/` 和 `mcp/adapters/` 重复实现

## 目录结构

```
backend/app/mcp/
├── client.py          # MCP 客户端
├── registry.py        # 工具注册与查找
├── adapters/          # 协议适配
│   ├── weather_adapter.py
│   ├── search_adapter.py
│   ├── maps_adapter.py
│   └── travel_provider_adapter.py
└── servers/           # 本地 MCP Server（后期独立部署）
```

## 已规划集成

| 能力 | 适配器 | 外部服务 |
|------|--------|----------|
| 搜索 | `search_adapter` | Tavily |
| 地图 | `maps_adapter` | 高德 AMAP |
| 天气 | `weather_adapter` | **和风天气 QWeather** |
| 旅行供给 | `travel_provider_adapter` | AviationStack + AigoHotel MCP |

## 天气服务选型（已确认：和风天气 QWeather）

| 项 | 说明 |
|----|------|
| 服务商 | [和风天气开发服务](https://dev.qweather.com/) |
| 费用 | 每月前 **5 万次免费**，超出约 ¥0.0007/次 |
| 环境变量 | `QWEATHER_API_KEY`、`QWEATHER_API_HOST` |
| 能力 | 实时天气、7/15 天预报、分钟降水、预警、天气指数、空气质量 |
| MCP 参考 | [pangerl/mcp-server-weather](https://github.com/pangerl/mcp-server-weather)（可选自建 adapter） |

### 配置步骤

1. 登录 [控制台](https://console.qweather.com/) → 创建项目
2. 添加凭据（API KEY），勾选 **GeoAPI**、**天气预报**、**天气指数** 等
3. 在 **设置** 中复制你的 **API Host**（独立域名，非公共 `api.qweather.com`）
4. 填入 `.env`：

```bash
QWEATHER_API_KEY=你的API_KEY
QWEATHER_API_HOST=https://xxxx.def.qweatherapi.com
QWEATHER_LANG=zh
QWEATHER_UNIT=m
```

### 集成方式

```
tools/weather.py → mcp/adapters/weather_adapter.py → QWeather HTTP API
```

请求认证：Header `X-QW-Api-Key: {QWEATHER_API_KEY}`，Base URL 使用 `QWEATHER_API_HOST`。

## 部署

- 前期：MCP 与 backend 同进程
- 后期：`infra/docker/mcp.Dockerfile` 独立容器
