# BM25 Sparse Retriever — lexical search using BM25 ranking

from typing import Optional
import math
from collections import Counter
from app.core.retrieval.base import BaseRetriever
from app.models.document import DocumentChunk
from app.config import settings


class BM25Retriever(BaseRetriever):
    def __init__(self, k1: float = None, b: float = None):
        self.k1 = k1 or settings.BM25_K1
        self.b = b or settings.BM25_B
        self._documents: list[DocumentChunk] = []
        self._doc_freqs: list[Counter] = []
        self._idf: dict[str, float] = {}
        self._avg_doc_length: float = 0.0
        self._corpus_size: int = 0
        self._built: bool = False

    @property
    def name(self) -> str:
        return "bm25"

    def index_documents(self, documents: list[DocumentChunk]):
        self._documents = documents
        self._doc_freqs = []
        total_length = 0
        df: dict[str, int] = {}

        for doc in documents:
            tokens = doc.content.lower().split()
            freq = Counter(tokens)
            self._doc_freqs.append(freq)
            total_length += len(tokens)
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1

        self._corpus_size = len(documents)
        self._avg_doc_length = total_length / self._corpus_size if self._corpus_size > 0 else 1.0

        # Compute IDF
        self._idf = {}
        for token, doc_count in df.items():
            self._idf[token] = math.log(1 + (self._corpus_size - doc_count + 0.5) / (doc_count + 0.5))

        self._built = True

    def _score_document(self, query_tokens: list[str], doc_idx: int) -> float:
        freq = self._doc_freqs[doc_idx]
        doc_len = sum(freq.values())
        score = 0.0

        for token in query_tokens:
            if token not in self._idf:
                continue
            tf = freq.get(token, 0)
            idf = self._idf[token]
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self._avg_doc_length))
            score += idf * (numerator / denominator)

        return score

    async def retrieve(self, query: str, top_k: int = 10) -> list[tuple[DocumentChunk, float]]:
        if not self._built:
            return []

        query_tokens = query.lower().split()
        scores = []
        for i in range(self._corpus_size):
            score = self._score_document(query_tokens, i)
            scores.append((i, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in scores[:top_k]:
            if score > 0:
                results.append((self._documents[idx], score))
        return results
