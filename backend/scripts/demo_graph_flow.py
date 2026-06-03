"""路线1 演示：完整流程 + 回退 + 继续规划"""
import asyncio
import sys
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from langchain_core.messages import HumanMessage

from app.dependencies import CheckpointerManager
from app.graph import build_travel_graph, format_planning_progress, rollback_to_destination
from app.utils.logging import setup_logger

setup_logger()

THREAD_ID = "demo-flow-rollback-001"
USER_ID = "demo_user_001"


async def invoke_step(graph, config, label, payload):
    print(f"\n=== {label} ===")
    state = await graph.ainvoke(payload, config=config)
    print("current_step:", state.get("current_step"))
    print("last:", state["messages"][-1].content)
    return state


async def run_demo() -> None:
    try:
        graph = await build_travel_graph()
        config = {"configurable": {"thread_id": THREAD_ID}}
        base = {"user_id": USER_ID, "session_id": THREAD_ID}

        await invoke_step(
            graph,
            config,
            "1. 提交需求",
            {
                **base,
                "departure_city": "上海",
                "departure_date": "2025-10-01",
                "travel_days": 5,
                "budget_min": 3000,
                "budget_max": 6000,
                "travel_styles": ["culture", "food"],
                "destination": "成都",
                "selected_destination": "成都",
                "messages": [HumanMessage(content="我想去成都")],
            },
        )

        state = await invoke_step(
            graph,
            config,
            "2. 选择交通",
            {
                "selected_transport": "flight",
                "messages": [HumanMessage(content="坐飞机")],
            },
        )

        print("\n=== 进度（回退前） ===")
        print(format_planning_progress(state))

        print("\n=== 3. 回退到目的地选择 ===")
        snapshot = await graph.aget_state(config)
        rollback_update = rollback_to_destination(
            dict(snapshot.values),
            reason="用户希望改去西安",
        )
        await graph.aupdate_state(config, rollback_update)

        state = await invoke_step(
            graph,
            config,
            "4. 重新选择目的地并继续",
            {
                "selected_destination": "西安",
                "destination": "西安",
                "selected_transport": "train",
                "selected_accommodation_types": ["hostel"],
                "selected_food_types": ["specialty", "local"],
                "messages": [HumanMessage(content="改去西安，高铁，民宿，特色美食")],
            },
        )

        print("\n=== 最终结果 ===")
        print("destination:", state.get("selected_destination"))
        print("transport:", state.get("selected_transport"))
        print("order_id:", state.get("order_id"))
        print("\n=== 进度（完成后） ===")
        print(format_planning_progress(state))
    finally:
        manager = await CheckpointerManager.get_instance()
        await manager.close()


if __name__ == "__main__":
    asyncio.run(run_demo())
