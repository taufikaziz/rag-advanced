# Query Decomposition — memecah query kompleks menjadi sub-queries

from typing import Optional
from app.core.query_processing.base import BaseQueryProcessor
from app.core.generation.base import BaseLLM


DECOMPOSE_SYSTEM_PROMPT = """You are a query decomposition assistant.
Break down the given complex query into simpler, atomic sub-queries.
Each sub-query should focus on one specific aspect and be self-contained for retrieval.
Return the sub-queries as a numbered list, one per line. No explanation."""


class DecomposeProcessor(BaseQueryProcessor):
    def __init__(self, llm: BaseLLM):
        self._llm = llm

    @property
    def name(self) -> str:
        return "decompose"

    async def process(self, query: str) -> str:
        result = await self._llm.generate(
            system_prompt=DECOMPOSE_SYSTEM_PROMPT,
            user_prompt=query,
        )
        return result.strip()

    async def process_to_list(self, query: str) -> list[str]:
        result = await self.process(query)
        lines = [line.strip() for line in result.split("\
") if line.strip()]
        sub_queries = []
        for line in lines:
            cleaned = line.lstrip("0123456789.-) ").strip()
            if cleaned:
                sub_queries.append(cleaned)
        return sub_queries if sub_queries else [query]
