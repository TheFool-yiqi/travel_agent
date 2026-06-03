"""千问 DashScope 文本嵌入（langchain_core Embeddings 适配）。"""

from __future__ import annotations

import dashscope
import requests
from dashscope import TextEmbedding
from langchain_core.embeddings import Embeddings
from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.settings import settings

_EMBED_BATCH_SIZE = 10
_RETRYABLE = (
    RuntimeError,
    requests.exceptions.RequestException,
)


class QwenEmbeddings(Embeddings):
    """使用 DashScope TextEmbedding API（默认 text-embedding-v4，1024 维）。"""

    def __init__(
        self,
        model: str | None = None,
        dimensions: int | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or settings.qwen_embedding_model
        self.dimensions = dimensions or settings.qwen_embedding_dimensions
        self.api_key = api_key or settings.dashscope_api_key
        if not self.api_key:
            logger.warning("DASHSCOPE_API_KEY 未配置，嵌入调用将失败")
        else:
            dashscope.api_key = self.api_key

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors: list[list[float]] = []
        for start in range(0, len(texts), _EMBED_BATCH_SIZE):
            batch = texts[start : start + _EMBED_BATCH_SIZE]
            vectors.extend(self._call_embedding(batch))
        return vectors

    def embed_query(self, text: str) -> list[float]:
        return self._call_embedding([text])[0]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(_RETRYABLE),
        reraise=True,
    )
    def _call_embedding(self, texts: list[str]) -> list[list[float]]:
        response = TextEmbedding.call(
            model=self.model,
            input=texts,
            dimension=self.dimensions,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"DashScope 嵌入失败: status={response.status_code} "
                f"message={getattr(response, 'message', response)}"
            )
        items = sorted(response.output["embeddings"], key=lambda item: item["text_index"])
        return [item["embedding"] for item in items]


def get_embedding_model() -> QwenEmbeddings:
    """获取默认千问嵌入模型实例。"""
    return QwenEmbeddings()
