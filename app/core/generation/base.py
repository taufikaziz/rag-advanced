# Base LLM interface

from abc import ABC, abstractmethod
from typing import Optional


class BaseLLM(ABC):
    @abstractmethod
    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...
