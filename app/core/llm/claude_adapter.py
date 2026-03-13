import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.llm.gateway import LLMGateway, LLMUnavailableError


class ClaudeAdapter(LLMGateway):
    def __init__(self, api_key: str, openai_api_key: str = ""):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._openai_api_key = openai_api_key

    @retry(
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=False,
    )
    async def _complete_with_retry(self, prompt: str, system: str) -> str:
        message = await self._client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    async def complete(self, prompt: str, system: str) -> str:
        try:
            return await self._complete_with_retry(prompt, system)
        except Exception as e:
            raise LLMUnavailableError(f"Claude unavailable: {e}") from e

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        reraise=False,
    )
    async def _embed_with_retry(self, text: str) -> list[float]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self._openai_api_key)
        response = await client.embeddings.create(
            input=text,
            model="text-embedding-3-small",
        )
        return response.data[0].embedding

    async def embed(self, text: str) -> list[float]:
        try:
            return await self._embed_with_retry(text)
        except Exception as e:
            raise LLMUnavailableError(f"Embedding unavailable: {e}") from e
