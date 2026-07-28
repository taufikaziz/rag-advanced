# Query Rewrite — memperjelas dan memperkaya query sebelum retrieval

from typing import Optional
from app.core.query_processing.base import BaseQueryProcessor
from app.core.generation.base import BaseLLM


REWRITE_SYSTEM_PROMPT = """You are a query rewriting assistant for a RAG system.
Given the original user query, rewrite it to be more specific, clear, and effective for document retrieval.
Expand acronyms, clarify ambiguous terms, and add relevant context when possible.
Return ONLY the rewritten query, no explanation."""


class QueryRewriteProcessor(BaseQueryProcessor):
    def __init__(self, llm: BaseLLM):
        self._llm = llm

    @property
    def name(self) -> str:
        return "rewrite"

    async def process(self, query: str) -> str:
        rewritten = await self._llm.generate(
            system_prompt=REWRITE_SYSTEM_PROMPT,
            user_prompt=query,
        )
        return rewritten.strip()
