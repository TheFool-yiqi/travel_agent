"""FastAPI 依赖注入与全局共享资源"""

import asyncio
from typing import Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.checkpoint.redis.aio import AsyncRedisSaver
from langgraph.store.postgres.aio import AsyncPostgresStore
from loguru import logger
from psycopg_pool import AsyncConnectionPool

from app.graph.checkpoint import (
    checkpointer_label,
    close_redis_checkpointer,
    create_postgres_checkpointer,
    create_redis_checkpointer,
    resolve_checkpoint_backend,
)
from app.schemas.memory import (
    TravelHistory,
    TravelRecord,
    UserMemory,
    UserProfile,
    empty_user_memory,
    utc_now_iso,
)
from app.db.session import get_db
from app.settings import Settings, get_settings, settings

# 认证依赖（Handoffs 兼容 re-export）
from app.api.deps import get_current_user, get_current_user_optional  # noqa: E402

__all__ = [
    "CheckpointerManager",
    "UserMemoryService",
    "get_checkpointer",
    "get_current_user",
    "get_current_user_optional",
    "get_db",
    "get_settings_dep",
    "get_user_memory",
    "get_user_memory_service",
    "format_user_memory_for_prompt",
    "save_user_memory",
]


def get_settings_dep() -> Settings:
    """在路由中通过 Depends(get_settings_dep) 注入配置"""
    return get_settings()


class CheckpointerManager:
    """LangGraph 资源单例（Checkpointer + Postgres Store 连接池）"""

    _instance: Optional["CheckpointerManager"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self.pool: Optional[AsyncConnectionPool] = None
        self.checkpointer: Optional[BaseCheckpointSaver] = None
        self._redis_saver: Optional[AsyncRedisSaver] = None
        self.backend: str = resolve_checkpoint_backend()

    @classmethod
    async def get_instance(cls) -> "CheckpointerManager":
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    await cls._instance.initialize()
        return cls._instance

    async def initialize(self) -> None:
        if self.checkpointer is not None:
            logger.warning("LangGraph 资源已初始化，跳过")
            return

        try:
            logger.info(
                "初始化 LangGraph 资源 backend={} store=postgres",
                self.backend,
            )

            self.pool = AsyncConnectionPool(
                conninfo=settings.psycopg_url,
                min_size=settings.db_pool_min_size,
                max_size=settings.db_pool_max_size,
                timeout=settings.db_pool_timeout,
            )
            await self.pool.open()

            if self.backend == "redis":
                self._redis_saver = await create_redis_checkpointer()
                self.checkpointer = self._redis_saver
            else:
                self.checkpointer = create_postgres_checkpointer(self.pool)

            logger.info(
                "Checkpointer={} Store 连接池初始化完成",
                checkpointer_label(self.checkpointer),
            )

        except Exception as e:
            logger.error("LangGraph 资源初始化失败: {}", e)
            raise

    async def close(self) -> None:
        if self._redis_saver is not None:
            await close_redis_checkpointer(self._redis_saver)
            self._redis_saver = None

        if self.pool:
            await self.pool.close()
            self.pool = None

        self.checkpointer = None
        logger.info("LangGraph 资源已关闭")

    def get_checkpointer(self) -> BaseCheckpointSaver:
        if self.checkpointer is None:
            raise RuntimeError("Checkpointer 未初始化，请先启动应用")
        return self.checkpointer

    async def with_store(self, operation):
        """在 Store 上执行操作（复用连接池）"""
        if self.pool is None:
            raise RuntimeError("Store 未初始化，请先启动应用")
        async with self.pool.connection() as conn:
            store = AsyncPostgresStore(conn)
            return await operation(store)


async def get_checkpointer() -> BaseCheckpointSaver:
    """获取全局 Checkpointer，供 LangGraph compile 使用"""
    manager = await CheckpointerManager.get_instance()
    return manager.get_checkpointer()


class UserMemoryService:
    """
    用户长期记忆服务
    画像与出行历史分 namespace 存储，支持细粒度更新
    """

    def __init__(self, manager: CheckpointerManager) -> None:
        self._manager = manager

    @staticmethod
    def _profile_namespace(user_id: str) -> tuple[str, str]:
        return ("user_profiles", user_id)

    @staticmethod
    def _history_namespace(user_id: str) -> tuple[str, str]:
        return ("travel_history", user_id)

    async def get_user_profile(self, user_id: str) -> UserProfile:
        async def _load(store: AsyncPostgresStore) -> UserProfile:
            try:
                result = await store.aget(self._profile_namespace(user_id), "profile")
                if result and result.value:
                    return UserProfile.model_validate(result.value)
            except Exception as e:
                logger.error("获取用户画像失败 user_id={}: {}", user_id, e)
            return UserProfile()

        return await self._manager.with_store(_load)

    async def save_user_profile(self, user_id: str, profile: UserProfile) -> None:
        profile.updated_at = utc_now_iso()

        async def _save(store: AsyncPostgresStore) -> None:
            await store.aput(
                self._profile_namespace(user_id),
                "profile",
                profile.model_dump(),
            )

        await self._manager.with_store(_save)
        logger.info("保存用户画像 user_id={}", user_id)

    async def update_travel_styles(self, user_id: str, styles: list[str]) -> None:
        profile = await self.get_user_profile(user_id)
        profile.travel_styles = list(set(profile.travel_styles) | set(styles))
        await self.save_user_profile(user_id, profile)

    async def update_dietary_restrictions(
        self, user_id: str, restrictions: list[str]
    ) -> None:
        profile = await self.get_user_profile(user_id)
        profile.dietary_restrictions = list(
            set(profile.dietary_restrictions) | set(restrictions)
        )
        await self.save_user_profile(user_id, profile)

    async def update_food_preferences(
        self, user_id: str, preferences: list[str]
    ) -> None:
        profile = await self.get_user_profile(user_id)
        profile.food_preferences = list(set(profile.food_preferences) | set(preferences))
        await self.save_user_profile(user_id, profile)

    async def get_travel_history(self, user_id: str) -> TravelHistory:
        async def _load(store: AsyncPostgresStore) -> TravelHistory:
            try:
                result = await store.aget(self._history_namespace(user_id), "history")
                if result and result.value:
                    return TravelHistory.model_validate(result.value)
            except Exception as e:
                logger.error("获取出行历史失败 user_id={}: {}", user_id, e)
            return TravelHistory()

        return await self._manager.with_store(_load)

    async def save_travel_history(self, user_id: str, history: TravelHistory) -> None:
        history.updated_at = utc_now_iso()

        async def _save(store: AsyncPostgresStore) -> None:
            await store.aput(
                self._history_namespace(user_id),
                "history",
                history.model_dump(),
            )

        await self._manager.with_store(_save)
        logger.info("保存出行历史 user_id={}", user_id)

    async def add_completed_trip(
        self,
        user_id: str,
        destination: str,
        start_date: str,
        end_date: str,
        visited_attractions: list[str],
    ) -> None:
        history = await self.get_travel_history(user_id)
        history.completed_trips.append(
            TravelRecord(
                destination=destination,
                start_date=start_date,
                end_date=end_date,
                visited_attractions=visited_attractions,
            )
        )
        history.visited_attractions = list(
            set(history.visited_attractions) | set(visited_attractions)
        )
        await self.save_travel_history(user_id, history)
        logger.info("添加旅行记录 user_id={} destination={}", user_id, destination)

    async def update_accommodation_preference(
        self,
        user_id: str,
        preferred_types: list[str] | None = None,
        avg_budget: float | None = None,
    ) -> None:
        history = await self.get_travel_history(user_id)
        pref = history.accommodation_preference

        if preferred_types:
            pref.preferred_types = list(set(pref.preferred_types) | set(preferred_types))

        if avg_budget is not None:
            old_budget = pref.avg_budget_per_night
            pref.avg_budget_per_night = (
                (old_budget + avg_budget) / 2 if old_budget else avg_budget
            )

        await self.save_travel_history(user_id, history)
        logger.info("更新住宿偏好 user_id={}", user_id)

    async def get_visited_destinations(self, user_id: str) -> list[str]:
        history = await self.get_travel_history(user_id)
        return list({trip.destination for trip in history.completed_trips})

    async def get_visited_attractions(self, user_id: str) -> list[str]:
        history = await self.get_travel_history(user_id)
        return history.visited_attractions

    async def get_user_memory(self, user_id: str) -> UserMemory:
        profile, history = await asyncio.gather(
            self.get_user_profile(user_id),
            self.get_travel_history(user_id),
        )
        return UserMemory(user_id=user_id, profile=profile, history=history)

    async def format_memory_for_prompt(self, user_id: str) -> str:
        memory = await self.get_user_memory(user_id)
        parts = ["**用户历史偏好**："]

        if memory.profile.travel_styles:
            parts.append(f"- 旅行风格：{', '.join(memory.profile.travel_styles)}")
        if memory.profile.dietary_restrictions:
            parts.append(
                f"- 饮食禁忌：{', '.join(memory.profile.dietary_restrictions)}"
            )
        if memory.profile.food_preferences:
            parts.append(f"- 饮食偏好：{', '.join(memory.profile.food_preferences)}")

        if memory.history.completed_trips:
            destinations = list(
                {trip.destination for trip in memory.history.completed_trips}
            )
            parts.append(f"- 去过的目的地：{', '.join(destinations[-5:])}")

        if memory.history.visited_attractions:
            recent = memory.history.visited_attractions[-10:]
            parts.append(f"- 去过的景点：{', '.join(recent)}（最近10个）")

        acc_pref = memory.history.accommodation_preference
        if acc_pref.preferred_types:
            parts.append(f"- 住宿偏好：{', '.join(acc_pref.preferred_types)}")
        if acc_pref.avg_budget_per_night is not None:
            parts.append(f"- 住宿预算：约 {acc_pref.avg_budget_per_night:.0f} 元/晚")

        return "" if len(parts) == 1 else "\n".join(parts)


async def get_user_memory_service() -> UserMemoryService:
    """获取用户长期记忆服务"""
    manager = await CheckpointerManager.get_instance()
    return UserMemoryService(manager)


async def get_user_memory(user_id: str) -> UserMemory:
    """加载完整用户长期记忆"""
    service = await get_user_memory_service()
    memory = await service.get_user_memory(user_id)
    if (
        not memory.profile.travel_styles
        and not memory.profile.dietary_restrictions
        and not memory.profile.food_preferences
        and not memory.history.completed_trips
    ):
        return empty_user_memory(user_id)
    return memory


async def save_user_memory(memory: UserMemory) -> UserMemory:
    """保存完整用户长期记忆"""
    service = await get_user_memory_service()
    await service.save_user_profile(memory.user_id, memory.profile)
    await service.save_travel_history(memory.user_id, memory.history)
    logger.info("用户长期记忆已保存 user_id={}", memory.user_id)
    return memory


async def format_user_memory_for_prompt(user_id: str) -> str:
    """将用户长期记忆格式化为 Agent 提示词"""
    service = await get_user_memory_service()
    return await service.format_memory_for_prompt(user_id)
