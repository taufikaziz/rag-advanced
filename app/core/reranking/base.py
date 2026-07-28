# Base reranker interface

from abc import ABC, abstractmethod
from app.models.document import DocumentChunk


class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self, query: str, documents: list[tuple[DocumentChunk, float]]
    ) -> list[tuple[DocumentChunk, float]]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
