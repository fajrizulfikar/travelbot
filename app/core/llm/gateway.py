from abc import ABC, abstractmethod


class LLMUnavailableError(Exception):
    pass


class LLMGateway(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str) -> str: ...

    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...
