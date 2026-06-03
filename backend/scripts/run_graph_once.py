"""Run one LangGraph turn from the command line."""

from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from langchain_core.messages import AIMessage, HumanMessage

from app.ai.llm import create_travel_planner
from app.dependencies import CheckpointerManager
from app.utils.logging import setup_logger

setup_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Invoke the travel graph once.")
    parser.add_argument("message", help="User message to send into the graph.")
    parser.add_argument("--user-id", default="cli_user", help="State user_id value.")
    parser.add_argument(
        "--session-id",
        default=None,
        help="State session_id/thread_id value. Defaults to a random UUID.",
    )
    return parser.parse_args()


async def run_once(args: argparse.Namespace) -> None:
    session_id = args.session_id or str(uuid.uuid4())
    graph = await create_travel_planner()
    config = {"configurable": {"thread_id": session_id}}
    try:
        state = await graph.ainvoke(
            {
                "user_id": args.user_id,
                "session_id": session_id,
                "messages": [HumanMessage(content=args.message)],
            },
            config=config,
        )
        print("session_id:", session_id)
        print("current_step:", state.get("current_step"))
        for message in reversed(state.get("messages") or []):
            if isinstance(message, AIMessage) and message.content:
                print("assistant:", message.content)
                break
    finally:
        manager = await CheckpointerManager.get_instance()
        await manager.close()


def main() -> None:
    asyncio.run(run_once(parse_args()))


if __name__ == "__main__":
    main()
