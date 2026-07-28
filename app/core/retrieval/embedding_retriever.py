# Dense Retriever — semantic search using embedding vectors

from typing import Optional
import numpy as np
from app.core.retrieval.base import BaseRetriever
from app.models.document import DocumentChunk
from app.config import settings


class DenseRetriever(BaseRetriever):
    def __init__(self):
        self._documents: list[DocumentChunk] = []
        self._embeddings: np.ndarray | None = None
        self._built: bool = False

    @property
    def name(self) -> str:
        return "dense"

    def index_documents(self, documents: list[DocumentChunk]):
        self._documents = documents
        valid = [d for d in documents if d.embedding is not None]
        if valid:
            self._embeddings = np.array([d.embedding for d in valid], dtype=np.float32)
        else:
            self._embeddings = None
        self._built = True

    async def retrieve(self, query: str, top_k: int = 10) -> list[tuple[DocumentChunk, float]]:
        if not self._built or self._embeddings is None:
            return []

        # Query embedding should be computed externally; for now, this is a stub
        # In production, use the embedding provider to encode the query
        raise NotImplementedError(
            "DenseRetriever requires an embedding provider to encode queries. "
            "Use HybridRetriever which handles embedding automatically."
        )

    def retrieve_with_embedding(
        self, query_embedding: list[float], top_k: int = 10
    ) -> list[tuple[DocumentChunk, float]]:
        if not self._built or self._embeddings is None:
            return []

        q_vec = np.array(query_embedding, dtype=np.float32)
        # Normalize vectors for cosine similarity
        q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-10)
        doc_norms = self._embeddings / (np.linalg.norm(self._embeddings, axis=1, keepdims=True) + 1e-10)
        similarities = np.dot(doc_norms, q_norm)

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0:
                results.append((self._documents[idx], score))
        return results
