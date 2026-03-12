from pydantic import BaseModel


class Chunk(BaseModel):
    id: str
    source_id: str
    text: str
    embedding: list[float] = []
    metadata: dict = {}


class SearchResult(BaseModel):
    chunk: Chunk
    score: float
