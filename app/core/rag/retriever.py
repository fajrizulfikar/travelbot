from app.core.vector_store.base import VectorStore
from app.core.llm.gateway import LLMGateway
from app.core.models import SearchResult
from app.config import Settings


class RAGRetriever:
    def __init__(self, vector_store: VectorStore, llm: LLMGateway, settings: Settings):
        self._vector_store = vector_store
        self._llm = llm
        self._settings = settings

    async def retrieve(self, query: str) -> tuple[list[SearchResult], float]:
        query_vector = await self._llm.embed(query)
        results = await self._vector_store.query(query_vector, top_n=self._settings.TOP_N_RESULTS)
        filtered = [r for r in results if r.score >= self._settings.SIMILARITY_THRESHOLD]
        max_score = max((r.score for r in filtered), default=0.0)
        return filtered, max_score
