# Base retriever interface

from abc import ABC, abstractmethod
from typing import Optional
from app.models.document import DocumentChunk


class BaseRetriever(ABC):
    @abstractmethod
    async def retrieve(self, query: str, top_k: int = 10) -> list[tuple[DocumentChunk, float]]:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
