import uuid
import chromadb
from app.core.vector_store.base import VectorStore
from app.core.models import Chunk, SearchResult


class ChromaVectorStore(VectorStore):
    def __init__(self, persist_dir: str, collection_name: str = "travelbot"):
        if persist_dir == ":memory:":
            self._client = chromadb.EphemeralClient()
            # Use a unique collection name to prevent cross-instance contamination in tests
            col_name = f"{collection_name}_{uuid.uuid4().hex[:8]}"
        else:
            self._client = chromadb.PersistentClient(path=persist_dir)
            col_name = collection_name
        self._collection = self._client.get_or_create_collection(
            name=col_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def upsert(self, chunks: list[Chunk]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[c.id for c in chunks],
            embeddings=[c.embedding for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[{**c.metadata, "source_id": c.source_id} for c in chunks],
        )

    async def query(self, query_vector: list[float], top_n: int) -> list[SearchResult]:
        count = self._collection.count()
        if count == 0:
            return []
        n = min(top_n, count)
        results = self._collection.query(
            query_embeddings=[query_vector],
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        search_results = []
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]
            # ChromaDB cosine distance: score = 1 - distance
            score = 1.0 - distance
            metadata = results["metadatas"][0][i]
            source_id = metadata.pop("source_id", "")
            chunk = Chunk(
                id=doc_id,
                source_id=source_id,
                text=results["documents"][0][i],
                embedding=[],
                metadata=metadata,
            )
            search_results.append(SearchResult(chunk=chunk, score=score))
        search_results.sort(key=lambda r: r.score, reverse=True)
        return search_results

    async def delete_by_source(self, source_id: str) -> None:
        results = self._collection.get(where={"source_id": source_id})
        if results["ids"]:
            self._collection.delete(ids=results["ids"])
