"""演示 TravelState 节点 partial update + Checkpoint 持久化"""
import asyncio
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from langchain_core.messages import HumanMessage

from app.dependencies import CheckpointerManager, get_user_memory_service
from app.graph import build_travel_graph
from app.utils.logging import setup_logger

setup_logger()

THREAD_ID = "demo-session-inject-001"
USER_ID = "demo_user_001"


async def seed_demo_memory(user_id: str) -> None:
    service = await get_user_memory_service()
    await service.update_travel_styles(user_id, ["文化探索", "美食之旅"])
    await service.update_dietary_restrictions(user_id, ["海鲜过敏"])
    await service.add_completed_trip(
        user_id=user_id,
        destination="西安",
        start_date="2025-08-01",
        end_date="2025-08-05",
        visited_attractions=["兵马俑", "华清宫"],
    )


async def run_demo() -> None:
    try:
        await seed_demo_memory(USER_ID)
        graph = await build_travel_graph()
        config = {"configurable": {"thread_id": THREAD_ID}}

        print("\n=== 第 1 轮：信息不完整，应追问（含长期记忆注入） ===")
        r1 = await graph.ainvoke(
            {
                "user_id": USER_ID,
                "session_id": THREAD_ID,
                "messages": [HumanMessage(content="我想去旅行")],
            },
            config=config,
        )
        print("current_step:", r1.get("current_step"))
        print("requirements_complete:", r1.get("requirements_complete"))
        print("messages count:", len(r1["messages"]))
        print("first message (memory):", r1["messages"][0].content[:80], "...")
        print("last message:", r1["messages"][-1].content)

        print("\n=== 第 2 轮：补充信息，Checkpoint 续跑 ===")
        r2 = await graph.ainvoke(
            {
                "destination": "成都",
                "start_date": "2025-10-01",
                "end_date": "2025-10-05",
                "messages": [HumanMessage(content="去成都，10月1日到10月5日")],
            },
            config=config,
        )
        print("current_step:", r2.get("current_step"))
        print("destination:", r2.get("destination"))
        print("messages count:", len(r2["messages"]))
        print("last message:", r2["messages"][-1].content)

        print("\n演示完成：state 通过节点 return dict 更新，Checkpoint 按 thread_id 持久化")
    finally:
        manager = await CheckpointerManager.get_instance()
        await manager.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
