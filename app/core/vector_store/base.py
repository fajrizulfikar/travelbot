from abc import ABC, abstractmethod
from app.core.models import Chunk, SearchResult


class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, chunks: list[Chunk]) -> None: ...

    @abstractmethod
    async def query(self, query_vector: list[float], top_n: int) -> list[SearchResult]: ...

    @abstractmethod
    async def delete_by_source(self, source_id: str) -> None: ...
