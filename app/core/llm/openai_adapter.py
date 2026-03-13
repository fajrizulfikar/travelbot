from openai import AsyncOpenAI, RateLimitError, APIConnectionError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.llm.gateway import LLMGateway, LLMUnavailableError


class OpenAIAdapter(LLMGateway):
    def __init__(self, api_key: str):
        self._client = AsyncOpenAI(api_key=api_key)

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=False,
    )
    async def _complete_with_retry(self, prompt: str, system: str) -> str:
        response = await self._client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    async def complete(self, prompt: str, system: str) -> str:
        try:
            return await self._complete_with_retry(prompt, system)
        except Exception as e:
            raise LLMUnavailableError(f"OpenAI unavailable: {e}") from e

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=False,
    )
    async def _embed_with_retry(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding

    async def embed(self, text: str) -> list[float]:
        try:
            return await self._embed_with_retry(text)
        except Exception as e:
            raise LLMUnavailableError(f"Embedding unavailable: {e}") from e
