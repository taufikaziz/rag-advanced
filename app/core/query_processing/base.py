# Base query processor interface

from abc import ABC, abstractmethod
from typing import Optional


class BaseQueryProcessor(ABC):
    @abstractmethod
    async def process(self, query: str) -> str:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...
