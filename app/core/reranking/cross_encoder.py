# Cross-Encoder Reranker — reranking presisi menggunakan cross-encoder model

from typing import Optional
from app.core.reranking.base import BaseReranker
from app.models.document import DocumentChunk
from app.config import settings


class CrossEncoderReranker(BaseReranker):
    def __init__(self, model_name: str = None, device: str = None):
        self._model_name = model_name or settings.RERANKER_MODEL
        self._device = device or settings.RERANKER_DEVICE
        self._model = None

    @property
    def name(self) -> str:
        return "cross_encoder"

    async def _load_model(self):
        if self._model is not None:
            return
        # Lazy load to avoid heavy import at startup
        from sentence_transformers import CrossEncoder
        self._model = CrossEncoder(self._model_name, device=self._device)

    async def rerank(
        self, query: str, documents: list[tuple[DocumentChunk, float]]
    ) -> list[tuple[DocumentChunk, float]]:
        if not documents:
            return []

        await self._load_model()

        pairs = [(query, doc.content[:settings.RERANKER_MAX_LENGTH]) for doc, _ in documents]
        scores = self._model.predict(pairs)

        scored = []
        for i, (doc, original_score) in enumerate(documents):
            cross_score = float(scores[i])
            scored.append((doc, cross_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
