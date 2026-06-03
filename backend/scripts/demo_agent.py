"""长期记忆 + MiMo Agent 演示：写入记忆 → 创建 Agent → 个性化推荐"""
import asyncio
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from langchain_core.messages import HumanMessage

from app.ai.llm import create_memory_chat_agent
from app.dependencies import CheckpointerManager, get_user_memory_service
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()

DEMO_USER_ID = "demo_user_001"


async def seed_demo_memory(user_id: str) -> None:
    """为演示用户写入长期记忆（若已存在会合并更新）"""
    service = await get_user_memory_service()

    await service.update_travel_styles(user_id, ["文化探索", "美食之旅"])
    await service.update_dietary_restrictions(user_id, ["海鲜过敏"])
    await service.update_food_preferences(user_id, ["辣", "当地特色"])
    await service.add_completed_trip(
        user_id=user_id,
        destination="西安",
        start_date="2025-08-01",
        end_date="2025-08-05",
        visited_attractions=["兵马俑", "华清宫", "大雁塔", "西安城墙"],
    )
    await service.update_accommodation_preference(
        user_id=user_id,
        preferred_types=["星级酒店", "特色民宿"],
        avg_budget=350.0,
    )


async def run_demo() -> None:
    try:
        print(f"\n使用 LLM: {settings.mimo_model} ({settings.mimo_base_url})")
        print(f"演示用户: {DEMO_USER_ID}\n")

        print("==============================")
        print("Step 1: 写入长期记忆")
        print("==============================")
        await seed_demo_memory(DEMO_USER_ID)

        service = await get_user_memory_service()
        memory_text = await service.format_memory_for_prompt(DEMO_USER_ID)
        print(memory_text or "(暂无长期记忆)")

        print("\n==============================")
        print("Step 2: 创建记忆对话 Agent 并提问")
        print("==============================")

        agent = await create_memory_chat_agent(DEMO_USER_ID)
        response = await agent.ainvoke(
            {
                "messages": [
                    HumanMessage(
                        content="根据我的偏好，推荐一个适合的国内旅行目的地，并说明理由。"
                    )
                ]
            }
        )

        print("\nAgent 回复：")
        print(response["messages"][-1].content)
        print("\n演示完成")
    finally:
        manager = await CheckpointerManager.get_instance()
        await manager.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
