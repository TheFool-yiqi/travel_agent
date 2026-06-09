"""Online EvidenceCard retrieval for PlanningRuntime."""

from __future__ import annotations

from typing import Any

from rank_bm25 import BM25Okapi

from app.knowledge.evidence_repository import EvidenceRepository, FixtureEvidenceRepository
from app.knowledge.evidence_schemas import EvidenceCard, EvidenceContext, RetrievalTrace, SufficiencyResult
from app.knowledge.evidence_sufficiency import evaluate_sufficiency
from app.knowledge.query_analyzer import RetrievalQuery, build_retrieval_query
from app.knowledge.tokenizers import ChineseTokenizer, JiebaTokenizer
from app.runtime.collect.schemas import PlanningNeed
from app.runtime.context.schemas import BaseContext


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]],
    *,
    rrf_k: int = 60,
    top_k: int = 5,
) -> list[str]:
    """Fuse ranked evidence_card_id lists with RRF."""
    scores: dict[str, float] = {}
    for ranked_ids in ranked_lists:
        for rank, card_id in enumerate(ranked_ids, start=1):
            scores[card_id] = scores.get(card_id, 0.0) + 1.0 / (rrf_k + rank)
    return [
        card_id
        for card_id, _score in sorted(scores.items(), key=lambda item: item[1], reverse=True)
    ][:top_k]


class EvidenceEngine:
    """Retrieve approved EvidenceCards for formal planning stages."""

    def __init__(
        self,
        repository: EvidenceRepository | None = None,
        *,
        tokenizer: ChineseTokenizer | None = None,
        top_k: int = 5,
        rrf_k: int = 60,
    ) -> None:
        self._repository = repository or FixtureEvidenceRepository.from_default_fixture()
        self._tokenizer = tokenizer or JiebaTokenizer()
        self._top_k = top_k
        self._rrf_k = rrf_k

    def retrieve(
        self,
        planning_need: dict[str, Any],
        base_context: dict[str, Any] | None = None,
    ) -> tuple[EvidenceContext, SufficiencyResult]:
        need = PlanningNeed.from_runtime_dict(planning_need)
        base = BaseContext.from_runtime_dict(base_context) if base_context else None
        query = build_retrieval_query(need, base)

        candidates = self._repository.list_approved_cards(city=query.city)
        if not candidates:
            candidates = self._repository.list_approved_cards()

        vector_ranked_ids = self._vector_rank_ids(candidates, query.search_text)
        bm25_ranked_ids = self._bm25_rank_ids(candidates, query.search_text)
        fused_ids = reciprocal_rank_fusion(
            [vector_ranked_ids, bm25_ranked_ids],
            rrf_k=self._rrf_k,
            top_k=self._top_k,
        )
        cards = self._repository.get_cards_by_ids(fused_ids)

        trace = RetrievalTrace(
            vector_ranked_ids=vector_ranked_ids,
            bm25_ranked_ids=bm25_ranked_ids,
            fused_ids=fused_ids,
            filters={
                "city": query.city,
                "status": "approved",
                "required_evidence_types": query.required_evidence_types,
            },
        )
        context = EvidenceContext(
            cards=cards,
            card_ids=[card.id for card in cards],
            query_summary=query.model_dump(mode="json"),
            retrieval_trace=trace,
        )
        sufficiency = evaluate_sufficiency(query, cards)
        return context, sufficiency

    def _vector_rank_ids(self, cards: list[EvidenceCard], search_text: str) -> list[str]:
        if not search_text:
            return [card.id for card in cards]
        query_tokens = set(self._tokenizer.tokenize(search_text))
        scored: list[tuple[str, float]] = []
        for card in cards:
            doc_tokens = set(self._tokenizer.tokenize(card.embedding_text))
            if not query_tokens:
                overlap = 0.0
            else:
                overlap = len(query_tokens & doc_tokens) / len(query_tokens)
            scored.append((card.id, overlap))
        scored.sort(key=lambda item: item[1], reverse=True)
        return [card_id for card_id, _score in scored]

    def _bm25_rank_ids(self, cards: list[EvidenceCard], search_text: str) -> list[str]:
        if not cards:
            return []
        tokenized_docs = [self._tokenizer.tokenize(card.embedding_text) for card in cards]
        bm25 = BM25Okapi(tokenized_docs)
        query_tokens = self._tokenizer.tokenize(search_text)
        scores = bm25.get_scores(query_tokens)
        ranked_indices = sorted(
            range(len(scores)),
            key=lambda index: scores[index],
            reverse=True,
        )
        return [cards[index].id for index in ranked_indices]
