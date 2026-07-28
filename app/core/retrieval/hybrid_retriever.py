# Hybrid Retriever — menggabungkan BM25 + Dense Retrieval dengan weighted fusion

from typing import Optional
from app.core.retrieval.base import BaseRetriever
from app.core.retrieval.bm25_retriever import BM25Retriever
from app.core.retrieval.embedding_retriever import DenseRetriever
from app.models.document import DocumentChunk
from app.config import settings


class HybridRetriever(BaseRetriever):
    def __init__(
        self,
        bm25_retriever: BM25Retriever,
        dense_retriever: DenseRetriever,
        alpha: float = None,
    ):
        self._bm25 = bm25_retriever
        self._dense = dense_retriever
        self._alpha = alpha if alpha is not None else settings.HYBRID_ALPHA

    @property
    def name(self) -> str:
        return "hybrid"

    async def retrieve(
        self,
        query: str,
        top_k: int = None,
        query_embedding: list[float] | None = None,
    ) -> list[tuple[DocumentChunk, float]]:
        k = top_k or settings.TOP_K_INITIAL

        # Get results from both retrievers
        bm25_results = await self._bm25.retrieve(query, top_k=k)

        if query_embedding:
            dense_results = self._dense.retrieve_with_embedding(query_embedding, top_k=k)
        else:
            dense_results = []

        # Reciprocal Rank Fusion (RRF) for hybrid scoring
        all_doc_ids = set()
        doc_scores: dict[str, dict] = {}

        for rank, (doc, score) in enumerate(bm25_results):
            all_doc_ids.add(doc.id)
            doc_scores[doc.id] = {
                "doc": doc,
                "bm25_rank": rank,
                "dense_rank": None,
                "bm25_score": score,
                "dense_score": 0.0,
            }

        for rank, (doc, score) in enumerate(dense_results):
            all_doc_ids.add(doc.id)
            if doc.id in doc_scores:
                doc_scores[doc.id]["dense_rank"] = rank
                doc_scores[doc.id]["dense_score"] = score
            else:
                doc_scores[doc.id] = {
                    "doc": doc,
                    "bm25_rank": None,
                    "dense_rank": rank,
                    "bm25_score": 0.0,
                    "dense_score": score,
                }

        # Compute hybrid score using RRF
        K = 60  # RRF constant
        scored_results = []
        for doc_id, data in doc_scores.items():
            bm25_rrf = 1.0 / (K + (data["bm25_rank"] if data["bm25_rank"] is not None else K * 2))
            dense_rrf = 1.0 / (K + (data["dense_rank"] if data["dense_rank"] is not None else K * 2))
            hybrid_score = (1 - self._alpha) * bm25_rrf + self._alpha * dense_rrf
            scored_results.append((data["doc"], hybrid_score))

        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:k]
