"""RAG 知识层：LLM 重排序 + 长上下文重排。"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger
from pydantic import BaseModel, Field

from app.ai.llm import get_chat_model
from app.settings import settings

_DEFAULT_EXCERPT_CHARS = 600
_DEFAULT_PREVIEW_CHARS = 200
_MAX_RERANK_CANDIDATES = 20

_SYSTEM_PROMPT = """你是文档相关性评估专家。请评估各文档与用户查询的相关性。

评分标准（0-10 分）：
- 10：完美回答查询，信息准确完整
- 7-9：大部分相关，有用信息较多
- 4-6：部分相关，有一定参考价值
- 1-3：相关性很低，几乎没有帮助
- 0：完全不相关

只依据文档摘要内容打分，不要编造文档中没有的信息。"""


class RelevanceScore(BaseModel):
    """相关性评分（结构化输出）。"""

    document_index: int = Field(ge=0, description="文档索引，从 0 开始")
    relevance_score: int = Field(ge=0, le=10, description="相关性得分 0-10")
    reason: str = Field(default="", max_length=120, description="简短打分理由")


class RerankingResult(BaseModel):
    """重排序结果。"""

    scores: list[RelevanceScore] = Field(description="所有文档的评分列表")


class LLMReranker:
    """使用 MiMo 对检索候选文档重排。"""

    def __init__(
        self,
        top_k: int = 3,
        excerpt_chars: int = _DEFAULT_EXCERPT_CHARS,
    ) -> None:
        self.top_k = top_k
        self.excerpt_chars = excerpt_chars
        self._structured_llm = get_chat_model().bind(temperature=0).with_structured_output(
            RerankingResult
        )

    def rerank(
        self,
        query: str,
        documents: list[Document],
        top_k: int | None = None,
        *,
        long_context_reorder: bool = False,
    ) -> list[Document]:
        """
        对混合检索候选文档重排，返回 top_k。

        Args:
            long_context_reorder: 是否应用 Lost-in-the-Middle 长上下文重排
        """
        if not documents:
            return []

        limit = top_k if top_k is not None else self.top_k

        if len(documents) <= limit and not long_context_reorder:
            return documents[:limit]

        candidates = documents[:_MAX_RERANK_CANDIDATES]
        if len(documents) > _MAX_RERANK_CANDIDATES:
            logger.warning(
                "重排候选超过 {} 篇，仅对前 {} 篇打分",
                _MAX_RERANK_CANDIDATES,
                _MAX_RERANK_CANDIDATES,
            )

        logger.info("开始重排序 {} 个文档（query={!r}）", len(candidates), query)

        if not settings.mimo_api_key:
            logger.warning("MIMO_API_KEY 未配置，跳过重排，按原顺序截取 top_k")
            ranked = candidates[:limit]
        else:
            try:
                ranked = self._rerank_scored(query, candidates, limit)
            except Exception as exc:
                logger.error("重排序失败: {}，返回原始顺序", exc)
                ranked = candidates[:limit]

        if long_context_reorder:
            ranked = LongContextReorder.reorder(ranked)

        return ranked

    def _rerank_scored(
        self,
        query: str,
        documents: list[Document],
        top_k: int,
    ) -> list[Document]:
        prompt = self._build_user_prompt(query, documents)
        result: RerankingResult = self._structured_llm.invoke(
            [
                SystemMessage(content=_SYSTEM_PROMPT),
                HumanMessage(content=prompt),
            ]
        )

        sorted_scores = sorted(
            result.scores,
            key=lambda item: item.relevance_score,
            reverse=True,
        )

        reranked: list[Document] = []
        for item in sorted_scores:
            index = item.document_index
            if 0 <= index < len(documents):
                reranked.append(documents[index])
                logger.debug(
                    "  [{}] 得分: {}/10 - {}",
                    index,
                    item.relevance_score,
                    item.reason,
                )
            if len(reranked) >= top_k:
                break

        if len(reranked) < top_k:
            seen = {id(doc) for doc in reranked}
            for doc in documents:
                if id(doc) not in seen:
                    reranked.append(doc)
                if len(reranked) >= top_k:
                    break

        logger.info("重排序完成，返回 {} 个文档", len(reranked[:top_k]))
        return reranked[:top_k]

    def _build_user_prompt(self, query: str, documents: list[Document]) -> str:
        blocks: list[str] = [
            f"用户查询：{query}",
            "",
            "文档列表：",
        ]
        for index, doc in enumerate(documents):
            content = doc.page_content.strip().replace("\n", " ")
            if len(content) > self.excerpt_chars:
                preview = content[: self.excerpt_chars] + "…"
            else:
                preview = content
            meta_parts = [
                str(doc.metadata.get(key))
                for key in ("city", "category", "slug", "chunk_level")
                if doc.metadata.get(key)
            ]
            meta = " | ".join(meta_parts) if meta_parts else "未知来源"
            blocks.append(f"[文档 {index}]\n元数据：{meta}\n{preview}\n")
        blocks.append("请返回 JSON，包含每个 document_index 的 relevance_score 与 reason。")
        return "\n".join(blocks)


class LongContextReorder:
    """
    长上下文重排序（Lost in the Middle）

    最相关放开头，次相关放结尾，其余放中间，减轻 LLM 对中段内容的忽略。
    """

    @staticmethod
    def reorder(documents: list[Document]) -> list[Document]:
        if len(documents) <= 2:
            return documents

        logger.info("长上下文重排序: {} 个文档", len(documents))

        odd_rank: list[Document] = []
        even_rank: list[Document] = []

        for index, doc in enumerate(documents):
            if index % 2 == 0:
                odd_rank.append(doc)
            else:
                even_rank.append(doc)

        reordered = odd_rank + even_rank[::-1]
        logger.debug("长上下文重排完成，文档数={}", len(reordered))
        return reordered
