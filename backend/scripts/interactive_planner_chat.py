"""路线1 交互式规划：持续对话 + Checkpoint + Graph 流式输出"""
import asyncio
import sys
import uuid
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.ai.llm import create_travel_planner
from app.dependencies import CheckpointerManager
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()

DEFAULT_USER_ID = "interactive_user_001"


async def run_interactive_chat(user_id: str = DEFAULT_USER_ID) -> None:
    """
    持续对话测试循环（路线1 Graph，非 Handoffs Agent）。

    参考 Handoffs interactive_chat，改用 create_travel_planner()。
    """
    if not settings.mimo_api_key:
        raise ValueError("MIMO_API_KEY 未配置，请检查 .env")

    graph = await create_travel_planner()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    print(f"=== 旅行规划交互测试 (会话 ID: {thread_id}) ===")
    print(f"用户 ID: {user_id}")
    print("输入 q / quit / exit 退出")
    print("-" * 50)

    last_message_id = None
    last_step = None

    try:
        while True:
            try:
                user_input = input("\nUser (你): ").strip()
                if not user_input:
                    continue
                if user_input.lower() in {"q", "quit", "exit"}:
                    print("结束对话。")
                    break

                inputs = {
                    "user_id": user_id,
                    "session_id": thread_id,
                    "messages": [HumanMessage(content=user_input)],
                }

                print("\nAssistant: ", end="", flush=True)
                printed_reply = False

                async for event in graph.astream(
                    inputs,
                    config=config,
                    stream_mode="values",
                ):
                    step = event.get("current_step")
                    if step and step != last_step:
                        print(f"\n[步骤] {step}")
                        last_step = step

                    messages = event.get("messages") or []
                    if not messages:
                        continue

                    last_msg = messages[-1]
                    if last_msg.id == last_message_id:
                        continue
                    last_message_id = last_msg.id

                    if isinstance(last_msg, AIMessage) and last_msg.content:
                        if printed_reply:
                            print()
                        print(last_msg.content, end="", flush=True)
                        printed_reply = True
                    elif isinstance(last_msg, ToolMessage):
                        print(f"\n[系统] 工具执行: {last_msg.name}")

                if printed_reply:
                    print()

            except KeyboardInterrupt:
                print("\n结束对话。")
                break
            except EOFError:
                print("\n结束对话。")
                break
            except Exception as exc:
                print(f"\n发生错误: {exc}")
                import traceback

                traceback.print_exc()
    finally:
        manager = await CheckpointerManager.get_instance()
        await manager.close()


if __name__ == "__main__":
    asyncio.run(run_interactive_chat())
