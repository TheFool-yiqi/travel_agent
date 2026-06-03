"""演示 plan_destination 节点通过 MiMo 推荐目的地（无预选城市）"""
import asyncio
import sys
import uuid
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from langchain_core.messages import HumanMessage

from app.ai.llm import create_travel_planner
from app.dependencies import CheckpointerManager
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()

THREAD_ID = f"demo-plan-destination-llm-{uuid.uuid4().hex[:8]}"
USER_ID = "demo_user_001"


async def run_demo() -> None:
    if not settings.mimo_api_key:
        raise ValueError("MIMO_API_KEY 未配置，请检查 .env")

    graph = await create_travel_planner()
    config = {"configurable": {"thread_id": THREAD_ID}}
    base = {"user_id": USER_ID, "session_id": THREAD_ID}

    print("=== 1. 提交需求（不预选目的地）===")
    state = await graph.ainvoke(
        {
            **base,
            "departure_city": "上海",
            "departure_date": "2025-10-01",
            "travel_days": 5,
            "budget_min": 3000,
            "budget_max": 6000,
            "travel_styles": ["culture", "food"],
            "messages": [HumanMessage(content="帮我推荐几个适合国庆出行的地方")],
        },
        config=config,
    )
    print("current_step:", state.get("current_step"))
    print("selected_destination:", state.get("selected_destination"))
    print("\n--- LLM 回复 ---\n")
    print(state["messages"][-1].content)

    print("\n=== 2. 用户确认目的地 ===")
    state = await graph.ainvoke(
        {
            "selected_destination": "西安",
            "messages": [HumanMessage(content="就选西安吧")],
        },
        config=config,
    )
    print("current_step:", state.get("current_step"))
    print("selected_destination:", state.get("selected_destination"))
    print("last:", state["messages"][-1].content)


async def main() -> None:
    try:
        await run_demo()
    finally:
        manager = await CheckpointerManager.get_instance()
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
