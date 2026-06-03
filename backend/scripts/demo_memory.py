"""长期记忆全链路演示：写入画像/历史 → 读取 → 格式化 prompt"""
import asyncio
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.dependencies import CheckpointerManager, get_user_memory_service
from app.utils.logging import setup_logger

setup_logger()


async def run_demo() -> None:
    service = await get_user_memory_service()
    user_id = "449bfbbe-bdcb-473d-b7a9-67120f783df0"

    try:
        print("\n==============================")
        print("Step A: 保存用户画像（profile）")
        print("==============================")

        await service.update_travel_styles(user_id, ["culture", "food"])
        await service.update_dietary_restrictions(user_id, ["seafood-allergy"])
        await service.update_food_preferences(user_id, ["spicy", "local-cuisine"])

        profile = await service.get_user_profile(user_id)
        print("当前画像：", profile.model_dump())

        print("\n==============================")
        print("Step B: 保存出行历史（history）")
        print("==============================")

        await service.add_completed_trip(
            user_id=user_id,
            destination="西安",
            start_date="2025-08-01",
            end_date="2025-08-05",
            visited_attractions=["兵马俑", "华清宫", "大雁塔", "西安城墙"],
        )

        await service.update_accommodation_preference(
            user_id=user_id,
            preferred_types=["star_hotel", "hostel"],
            avg_budget=350.0,
        )

        history = await service.get_travel_history(user_id)
        print("当前出行历史：", history.model_dump())

        print("\n==============================")
        print("Step C: format_memory_for_prompt 结果")
        print("==============================")

        memory_text = await service.format_memory_for_prompt(user_id)
        print(memory_text if memory_text else "(暂无长期记忆)")

        print("\n演示完成：Store 写入 + 读取 + 格式化注入文本全链路正常")
    finally:
        manager = await CheckpointerManager.get_instance()
        await manager.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
