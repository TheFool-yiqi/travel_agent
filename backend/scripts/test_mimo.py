"""测试小米 MiMo LLM 连接（OpenAI 兼容模式）"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from langchain_core.messages import HumanMessage

from app.ai.llm import get_chat_model
from app.settings import settings


def test_mimo_connection() -> None:
    print(f"测试 MiMo 模型: {settings.mimo_model}")
    print(f"Base URL: {settings.mimo_base_url}")

    if not settings.mimo_api_key:
        raise ValueError("MIMO_API_KEY 未配置，请检查 .env")

    model = get_chat_model()
    response = model.invoke([
        HumanMessage(content="你好，请用一句话介绍你自己。")
    ])

    print(f"连接成功，模型回复:\n{response.content}")


if __name__ == "__main__":
    test_mimo_connection()
