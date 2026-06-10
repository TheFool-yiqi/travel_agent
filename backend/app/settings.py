"""
配置管理模块

使用 pydantic-settings 从项目根目录 .env 加载环境变量，
供 FastAPI、数据库、LLM、第三方 API 等模块统一读取。
"""
import os
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/settings.py → 向上两级到 backend/，再向上一级到项目根目录
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(BACKEND_DIR)


class Settings(BaseSettings):
    """应用配置（字段名 snake_case，通过 alias 映射 .env 中的大写变量）"""

    # ============== 应用基础 ==============
    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="APP_HOST")
    app_port: int = Field(default=8200, alias="APP_PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ============== 数据库 ==============
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_user: str = Field(default="travel", alias="DB_USER")
    db_password: str = Field(default="", alias="DB_PASSWORD")
    db_name: str = Field(default="travel_agent", alias="DB_NAME")
    db_pool_min_size: int = Field(default=2, alias="DB_POOL_MIN_SIZE")
    db_pool_max_size: int = Field(default=20, alias="DB_POOL_MAX_SIZE")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    checkpoint_retention_days: int = Field(default=7, alias="CHECKPOINT_RETENTION_DAYS")
    checkpoint_cleanup_daily_rate: int = Field(
        default=100,
        alias="CHECKPOINT_CLEANUP_DAILY_RATE",
        description="估算每日 checkpoint 写入量，用于无 created_at 时的清理 cutoff",
    )

    # ============== Redis ==============
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    # ============== LangGraph Checkpoint ==============
    checkpoint_backend: str = Field(
        default="postgres",
        alias="CHECKPOINT_BACKEND",
        description="LangGraph 会话状态存储：postgres（推荐）| redis（需兼容版本）",
    )

    # ============== LLM: 千问 (DashScope) ==============
    dashscope_api_key: str = Field(default="", alias="DASHSCOPE_API_KEY")
    qwen_model: str = Field(default="qwen3-vl-flash", alias="QWEN_MODEL")
    qwen_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        alias="QWEN_BASE_URL",
    )
    qwen_embedding_model: str = Field(
        default="text-embedding-v4", alias="QWEN_EMBEDDING_MODEL"
    )
    qwen_embedding_dimensions: int = Field(default=1024, alias="QWEN_EMBEDDING_DIMENSIONS")
    qwen_temperature: float = Field(default=0.7, alias="QWEN_TEMPERATURE")
    qwen_max_tokens: int = Field(default=8000, alias="QWEN_MAX_TOKENS")
    qwen_max_tokens_fast: int = Field(
        default=1024,
        alias="QWEN_MAX_TOKENS_FAST",
        description="简单对话 fast 模型上限（寒暄、需求收集回复）",
    )

    # ============== LLM: DeepSeek ==============
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com", alias="DEEPSEEK_BASE_URL"
    )
    deepseek_model: str = Field(default="deepseek-v4-pro", alias="DEEPSEEK_MODEL")

    # ============== LLM: 小米 MiMo ==============
    mimo_api_key: str = Field(default="", alias="MIMO_API_KEY")
    mimo_base_url: str = Field(
        default="https://token-plan-cn.xiaomimimo.com/v1", alias="MIMO_BASE_URL"
    )
    mimo_model: str = Field(default="mimo-v2.5-pro", alias="MIMO_MODEL")
    mimo_model_fast: str = Field(
        default="mimo-v2.5",
        alias="MIMO_MODEL_FAST",
        description="简单对话用较快模型（如需求收集、寒暄）",
    )
    mimo_http_trust_env: bool = Field(
        default=False,
        alias="MIMO_HTTP_TRUST_ENV",
        description="MiMo 请求是否读取系统 HTTP 代理；经代理 SSL 失败时请保持 false",
    )

    # ============== LangSmith ==============
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="travel_agent", alias="LANGSMITH_PROJECT")
    langsmith_tracing: bool = Field(default=True, alias="LANGSMITH_TRACING")
    langsmith_endpoint: str = Field(
        default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT"
    )

    # ============== 第三方 API ==============
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    tavily_search_depth: str = Field(default="advanced", alias="TAVILY_SEARCH_DEPTH")
    tavily_max_results: int = Field(default=5, alias="TAVILY_MAX_RESULTS")

    amap_api_key: str = Field(default="", alias="AMAP_API_KEY")
    amap_base_url: str = Field(
        default="https://restapi.amap.com/v3", alias="AMAP_BASE_URL"
    )

    aviationstack_api_key: str = Field(default="", alias="AVIATIONSTACK_API_KEY")
    aviationstack_base_url: str = Field(
        default="https://api.aviationstack.com/v1", alias="AVIATIONSTACK_BASE_URL"
    )

    aigohotel_api_key: str = Field(default="", alias="AIGOHOTEL_API_KEY")
    aigohotel_base_url: str = Field(
        default="https://mcp.aigohotel.com/mcp", alias="AIGOHOTEL_BASE_URL"
    )

    qweather_api_key: str = Field(default="", alias="QWEATHER_API_KEY")
    qweather_api_host: str = Field(default="", alias="QWEATHER_API_HOST")
    qweather_lang: str = Field(default="zh", alias="QWEATHER_LANG")
    qweather_unit: str = Field(default="m", alias="QWEATHER_UNIT")

    # ============== MCP ==============
    mcp_weather_transport: str = Field(
        default="inprocess",
        alias="MCP_WEATHER_TRANSPORT",
        description="天气 MCP：inprocess（直连 QWeather）| stdio（本地 FastMCP Server）",
    )
    mcp_python_command: str = Field(
        default="",
        alias="MCP_PYTHON_COMMAND",
        description="stdio 模式启动 MCP Server 的可执行文件，默认当前 Python",
    )
    mcp_search_transport: str = Field(
        default="inprocess",
        alias="MCP_SEARCH_TRANSPORT",
        description="搜索 MCP：inprocess（直连 Tavily）| stdio（本地 FastMCP Server）",
    )
    mcp_train_url: str = Field(
        default="https://mcp.api-inference.modelscope.net/215d3cfb299e47/mcp",
        alias="MCP_TRAIN_URL",
        description="12306 高铁 MCP（ModelScope streamable_http）",
    )
    mcp_http_bypass_proxy: bool = Field(
        default=True,
        alias="MCP_HTTP_BYPASS_PROXY",
        description="MCP / provider HTTP 直连时忽略 HTTP_PROXY、HTTPS_PROXY（trust_env=False）",
    )
    mcp_include_date_tools: bool = Field(
        default=False,
        alias="MCP_INCLUDE_DATE_TOOLS",
        description="为 True 时 get_date_tools 额外加载 12306/飞常准 MCP 日期工具；默认仅用本地 get-current-date",
    )
    transport_subagent_timeout_seconds: int = Field(
        default=120,
        alias="TRANSPORT_SUBAGENT_TIMEOUT_SECONDS",
        description="协调器调用 Subagent 的超时秒数，超时后回退 mock",
    )
    transport_coordinator_timeout_seconds: int = Field(
        default=180,
        alias="TRANSPORT_COORDINATOR_TIMEOUT_SECONDS",
        description="集成测试 / 同步入口调用协调器的超时秒数",
    )
    chat_planner_backend: str = Field(
        default="runtime",
        alias="CHAT_PLANNER_BACKEND",
        description="Chat 主路径：runtime（PlanningRuntime）| graph（旧 LangGraph）",
    )
    variflight_api_key: str = Field(default="", alias="VARIFLIGHT_API_KEY")

    # ============== JWT ==============
    jwt_secret_key: str = Field(default="change_me", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_value(cls, value: object) -> object:
        """Accept common environment labels accidentally placed in DEBUG."""
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"dev", "development"}:
                return True
        return value

    @field_validator("chat_planner_backend", mode="before")
    @classmethod
    def normalize_chat_planner_backend(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"runtime", "graph"}:
                return normalized
        return value

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.app_env == "production" and self.jwt_secret_key.strip().lower() in {
            "change_me",
            "changeme",
            "",
        }:
            raise ValueError("JWT_SECRET_KEY must be set to a secure value in production")
        return self

    @property
    def database_url(self) -> str:
        """SQLAlchemy 连接串（psycopg 驱动）"""
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def psycopg_url(self) -> str:
        """psycopg / LangGraph 连接串（非 SQLAlchemy 格式）"""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        """Redis 连接串"""
        if self.redis_password:
            return (
                f"redis://:{self.redis_password}@{self.redis_host}:"
                f"{self.redis_port}/{self.redis_db}"
            )
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def qweather_base_url(self) -> str:
        """和风天气 API 完整 Base URL（自动补 https）"""
        host = self.qweather_api_host.strip().rstrip("/")
        if not host:
            return ""
        if host.startswith("http://") or host.startswith("https://"):
            return host
        return f"https://{host}"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例（进程内缓存，避免重复读 .env）"""
    return Settings()


settings = get_settings()
