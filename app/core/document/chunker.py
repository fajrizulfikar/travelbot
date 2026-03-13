import uuid
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.models import Chunk


def chunk(text: str, source_id: str, chunk_size: int = 512, overlap: int = 50) -> list[Chunk]:
    if not text or not text.strip():
        return []
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    texts = splitter.split_text(text)
    chunks = []
    for i, t in enumerate(texts):
        chunks.append(Chunk(
            id=str(uuid.uuid4()),
            source_id=source_id,
            text=t,
            embedding=[],
            metadata={"chunk_index": i},
        ))
    return chunks
