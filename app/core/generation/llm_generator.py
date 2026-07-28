# LLM Generator — abstraction over LLM providers (OpenAI, Anthropic, Ollama)

from typing import Optional
from app.core.generation.base import BaseLLM
from app.config import settings


class LLMGenerator(BaseLLM):
    def __init__(self, provider: str = None, model: str = None):
        self._provider = provider or settings.LLM_PROVIDER
        self._model = model or settings.LLM_MODEL
        self._client = None

    @property
    def model_name(self) -> str:
        return self._model

    async def _init_client(self):
        if self._client is not None:
            return

        if self._provider == "openai":
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(
                api_key=settings.LLM_API_KEY,
                base_url=settings.LLM_API_BASE,
            )
        elif self._provider == "anthropic":
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=settings.LLM_API_KEY)
        elif self._provider == "ollama":
            import ollama
            self._client = ollama
        else:
            raise ValueError(f"Unsupported LLM provider: {self._provider}")

    async def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
    ) -> str:
        await self._init_client()
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        if self._provider == "openai":
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temp,
                max_tokens=tokens,
            )
            return response.choices[0].message.content or ""

        elif self._provider == "anthropic":
            response = await self._client.messages.create(
                model=self._model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=tokens,
                temperature=temp,
            )
            return response.content[0].text if response.content else ""

        elif self._provider == "ollama":
            response = self._client.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                options={"temperature": temp, "num_predict": tokens},
            )
            return response["message"]["content"]

        raise ValueError(f"Unsupported LLM provider: {self._provider}")

    async def generate_with_usage(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
    ) -> tuple[str, int, float]:
        """Generate text and return (text, token_count, estimated_cost)"""
        await self._init_client()
        temp = temperature if temperature is not None else settings.LLM_TEMPERATURE
        tokens = max_tokens if max_tokens is not None else settings.LLM_MAX_TOKENS

        if self._provider == "openai":
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temp,
                max_tokens=tokens,
            )
            text = response.choices[0].message.content or ""
            usage = response.usage
            total_tokens = usage.total_tokens if usage else 0
            # Approximate cost: GPT-4o-mini ~.15/1M input, .60/1M output
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
            return text, total_tokens, cost

        text = await self.generate(system_prompt, user_prompt, temp, tokens)
        return text, len(text.split()) * 2, 0.0  # rough estimate
