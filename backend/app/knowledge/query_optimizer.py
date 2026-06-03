"""
查询优化模块

包含 Multi-Query、HyDE、查询改写及综合优化策略。
"""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from app.ai.llm import get_chat_model
from app.settings import settings

OptimizationStrategy = Literal[
    "multi_query",
    "hyde",
    "rewrite",
    "hybrid",
    "rewrite_hyde",
    "full",
]
QueryStrategyInput = OptimizationStrategy | Literal["auto"]

# 口语 / 推荐类关键词（规则选策略）
_COLLOQUIAL_MARKERS = (
    "有啥",
    "啥",
    "咋",
    "地儿",
    "玩儿",
    "玩啥",
    "弄啥",
    "去哪",
    "怎么样",
    "呗",
    "啦",
    "吗",
)
_RECOMMEND_MARKERS = ("推荐", "攻略", "旅游", "怎么玩", "有什么", "哪些", "介绍")

_MULTI_QUERY_SYSTEM = """你是一个查询优化专家。
给定用户查询，生成语义相似但表述不同的查询变体。

要求：
1. 保持原查询的核心意图
2. 使用不同的词汇和表述方式
3. 考虑同义词、相关概念
4. 每行一个变体，不要编号、不要额外说明"""

_HYDE_SYSTEM = """你是旅行攻略写作助手。
请根据用户问题，生成一段假设性的回答文档，用于检索匹配（HyDE）。

要求：
1. 200-300 字
2. 包含具体的景点名称、特点、推荐理由（与问题主题相关）
3. 使用旅游攻略的语言风格
4. 只输出文档正文，不要标题、不要前言"""

_REWRITE_SYSTEM = """你是一个查询改写专家。请将用户的口语化查询改写为更规范的书面表达。

要求：
1. 修正错别字
2. 将口语转为书面语
3. 保持查询意图不变
4. 只返回改写后的查询，不要解释"""


def _merge_queries(*parts: str) -> list[str]:
    """去重合并，保持顺序。"""
    merged: list[str] = []
    for part in parts:
        text = part.strip()
        if text and text not in merged:
            merged.append(text)
    return merged


def select_query_strategy(query: str) -> OptimizationStrategy:
    """
    根据 query 特征自动选择优化策略。

    | 场景 | 策略 | 说明 |
    | 口语 + 短句 | rewrite_hyde | 先书面化，再生成假设文档，兼顾 BM25 与向量 |
    | 口语 + 较长 | hybrid | 改写 + Multi-Query 扩召回 |
    | 推荐/攻略类 | full | 改写 + 变体 + HyDE，召回最大化 |
    | 短而规范 | hyde | 短问句与长文档语义鸿沟大 |
    | 长句 | multi_query | 已较完整，只需变体 |
    | 默认 | hybrid | 改写 + 变体，成本与效果平衡 |
    """
    text = query.strip()
    if not text:
        return "multi_query"

    length = len(text)
    colloquial = any(marker in text for marker in _COLLOQUIAL_MARKERS)
    recommend = any(marker in text for marker in _RECOMMEND_MARKERS)
    is_short = length < 18
    is_long = length > 45

    if colloquial and is_short:
        return "rewrite_hyde"
    if colloquial:
        return "hybrid"
    if recommend:
        return "full"
    if is_short:
        return "hyde"
    if is_long:
        return "multi_query"
    return "hybrid"


def resolve_query_strategy(query: str, strategy: QueryStrategyInput) -> OptimizationStrategy:
    """解析 auto 为具体策略。"""
    if strategy != "auto":
        return strategy
    resolved = select_query_strategy(query)
    logger.info("自动选择查询优化策略: {} ← {}", resolved, query[:80])
    return resolved


class MultiQueryOptimizer:
    """
    Multi-Query 优化器

    生成查询的多个变体以提高 RAG 召回率。
    """

    def __init__(self, num_variants: int = 3) -> None:
        self.num_variants = num_variants
        self._llm = get_chat_model().bind(temperature=0)

    def optimize(self, query: str) -> list[str]:
        """
        生成查询变体。

        Returns:
            包含原始查询与变体的列表（去重，原始查询在前）。
        """
        query = query.strip()
        if not query:
            return []

        logger.info("生成 Multi-Query 变体: {}", query)

        if not settings.mimo_api_key:
            logger.warning("MIMO_API_KEY 未配置，跳过多查询扩展")
            return [query]

        try:
            response = self._llm.invoke(
                [
                    SystemMessage(content=_MULTI_QUERY_SYSTEM),
                    HumanMessage(
                        content=(
                            f"原始查询：{query}\n\n"
                            f"请生成 {self.num_variants} 个变体，每行一个："
                        )
                    ),
                ]
            )
            content = response.content
            text = content if isinstance(content, str) else str(content)
            variants = [
                line.strip()
                for line in text.strip().splitlines()
                if line.strip() and line.strip() != query
            ]
        except Exception as exc:
            logger.warning("Multi-Query 生成失败，仅使用原始查询: {}", exc)
            return [query]

        all_queries: list[str] = [query]
        for variant in variants[: self.num_variants]:
            if variant not in all_queries:
                all_queries.append(variant)

        logger.debug("Multi-Query 共 {} 条", len(all_queries))
        for index, item in enumerate(all_queries, start=1):
            logger.debug("  {}. {}", index, item)

        return all_queries


def expand_query(query: str, *, num_variants: int = 3) -> list[str]:
    """便捷函数：Multi-Query 扩展。"""
    return MultiQueryOptimizer(num_variants=num_variants).optimize(query)


class HyDEOptimizer:
    """
    HyDE (Hypothetical Document Embeddings) 优化器

    生成假设性文档，用其 embedding 替代原始 query 做向量检索，提高语义匹配。
    """

    def __init__(self) -> None:
        self._llm = get_chat_model().bind(temperature=0)

    def generate_hypothetical_doc(self, query: str) -> str:
        """
        生成假设性文档。

        Args:
            query: 原始查询

        Returns:
            假设性文档；无 LLM 或失败时回退为原始 query。
        """
        query = query.strip()
        if not query:
            return ""

        logger.info("生成 HyDE 假设性文档: {}", query)

        if not settings.mimo_api_key:
            logger.warning("MIMO_API_KEY 未配置，HyDE 回退为原始 query")
            return query

        try:
            response = self._llm.invoke(
                [
                    SystemMessage(content=_HYDE_SYSTEM),
                    HumanMessage(content=f"问题：{query}"),
                ]
            )
            content = response.content
            hypothetical_doc = (
                content.strip() if isinstance(content, str) else str(content).strip()
            )
            if not hypothetical_doc:
                return query
            logger.debug("假设性文档: {}...", hypothetical_doc[:100])
            return hypothetical_doc
        except Exception as exc:
            logger.warning("HyDE 生成失败，回退为原始 query: {}", exc)
            return query


def generate_hyde_doc(query: str) -> str:
    """便捷函数：HyDE 假设性文档生成。"""
    return HyDEOptimizer().generate_hypothetical_doc(query)


class QueryRewriter:
    """
    查询改写器

    修正错别字、口语化表达，输出规范书面查询。
    """

    def __init__(self) -> None:
        self._llm = get_chat_model().bind(temperature=0)

    def rewrite(self, query: str) -> str:
        """
        改写查询。

        Returns:
            改写后的查询；无 LLM 或失败时回退为原始 query。
        """
        query = query.strip()
        if not query:
            return ""

        logger.info("改写查询: {}", query)

        if not settings.mimo_api_key:
            logger.warning("MIMO_API_KEY 未配置，跳查询改写")
            return query

        try:
            response = self._llm.invoke(
                [
                    SystemMessage(content=_REWRITE_SYSTEM),
                    HumanMessage(content=f"原始查询：{query}"),
                ]
            )
            content = response.content
            rewritten = (
                content.strip() if isinstance(content, str) else str(content).strip()
            )
            if not rewritten:
                return query
            logger.debug("改写结果: {}", rewritten)
            return rewritten
        except Exception as exc:
            logger.warning("查询改写失败，回退为原始 query: {}", exc)
            return query


def rewrite_query(query: str) -> str:
    """便捷函数：查询改写。"""
    return QueryRewriter().rewrite(query)


class AdvancedQueryOptimizer:
    """
    综合查询优化器

    整合 Multi-Query、HyDE、查询改写；支持 auto 自动选策略。
    """

    def __init__(self, strategy: QueryStrategyInput = "multi_query") -> None:
        self.strategy = strategy
        self.multi_query = MultiQueryOptimizer()
        self.hyde = HyDEOptimizer()
        self.rewriter = QueryRewriter()

    def optimize(self, query: str) -> list[str]:
        """根据策略优化查询，返回下游检索可用的 query 列表。"""
        query = query.strip()
        if not query:
            return []

        resolved = resolve_query_strategy(query, self.strategy)
        return self._optimize_resolved(query, resolved)

    def _optimize_resolved(self, query: str, strategy: OptimizationStrategy) -> list[str]:
        if strategy == "multi_query":
            return self.multi_query.optimize(query)

        if strategy == "hyde":
            hypothetical_doc = self.hyde.generate_hypothetical_doc(query)
            return _merge_queries(query, hypothetical_doc)

        if strategy == "rewrite":
            return [self.rewriter.rewrite(query)]

        if strategy == "hybrid":
            rewritten = self.rewriter.rewrite(query)
            return self.multi_query.optimize(rewritten)

        if strategy == "rewrite_hyde":
            rewritten = self.rewriter.rewrite(query)
            hyde_doc = self.hyde.generate_hypothetical_doc(rewritten)
            return _merge_queries(query, rewritten, hyde_doc)

        if strategy == "full":
            rewritten = self.rewriter.rewrite(query)
            variants = self.multi_query.optimize(rewritten)
            hyde_doc = self.hyde.generate_hypothetical_doc(rewritten)
            return _merge_queries(*variants, hyde_doc)

        logger.warning("未知策略: {}，使用原始查询", strategy)
        return [query]


def optimize_queries(
    query: str,
    *,
    strategy: QueryStrategyInput = "auto",
) -> list[str]:
    """便捷函数：按策略（或 auto）优化查询。"""
    return AdvancedQueryOptimizer(strategy=strategy).optimize(query)


def optimize_queries_with_strategy(query: str) -> tuple[list[str], OptimizationStrategy]:
    """优化查询并返回实际使用的策略（按 auto 规则解析）。"""
    resolved = select_query_strategy(query)
    logger.info("自动选择查询优化策略: {} ← {}", resolved, query[:80])
    queries = AdvancedQueryOptimizer(strategy=resolved)._optimize_resolved(query, resolved)
    return queries, resolved
