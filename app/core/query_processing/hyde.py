# HyDE (Hypothetical Document Embedding) — generates a hypothetical document from the query

from typing import Optional
from app.core.query_processing.base import BaseQueryProcessor
from app.core.generation.base import BaseLLM


HYDE_SYSTEM_PROMPT = """You are a HyDE (Hypothetical Document Embedding) generator.
Given a user query, write a short hypothetical document snippet that would be the ideal
answer or passage to satisfy the query. This document will be used for semantic retrieval,
so write it in a factual, informative style as if it were a real knowledge base entry.
Return ONLY the hypothetical document text, no explanation."""


class HyDEProcessor(BaseQueryProcessor):
    def __init__(self, llm: BaseLLM):
        self._llm = llm

    @property
    def name(self) -> str:
        return "hyde"

    async def process(self, query: str) -> str:
        document = await self._llm.generate(
            system_prompt=HYDE_SYSTEM_PROMPT,
            user_prompt=query,
        )
        return document.strip()
