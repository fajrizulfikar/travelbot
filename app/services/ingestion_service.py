import logging
import uuid
from datetime import datetime

from app.core.document.chunker import chunk
from app.core.document.parser import parse
from app.core.llm.gateway import LLMGateway
from app.core.vector_store.base import VectorStore
from app.config import Settings
from app.models.ingest import IngestJob

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, vector_store: VectorStore, llm: LLMGateway, settings: Settings):
        self._vector_store = vector_store
        self._llm = llm
        self._settings = settings
        self._jobs: dict[str, IngestJob] = {}

    def create_job(self, filename: str) -> IngestJob:
        job_id = str(uuid.uuid4())
        now = datetime.utcnow()
        job = IngestJob(
            job_id=job_id,
            filename=filename,
            status="pending",
            created_at=now,
            updated_at=now,
        )
        self._jobs[job_id] = job
        return job

    def get_job(self, job_id: str) -> IngestJob | None:
        return self._jobs.get(job_id)

    async def run(self, job_id: str, filename: str, file_bytes: bytes) -> None:
        job = self._jobs[job_id]
        job.status = "processing"
        job.updated_at = datetime.utcnow()
        try:
            raw_text = parse(filename, file_bytes)
            source_id = job_id
            chunks = chunk(raw_text, source_id=source_id)

            # Embed in batches of 20
            batch_size = 20
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                for c in batch:
                    c.embedding = await self._llm.embed(c.text)

            await self._vector_store.upsert(chunks)
            job.status = "completed"
            job.chunk_count = len(chunks)
            job.updated_at = datetime.utcnow()
            logger.info("Ingestion completed: job_id=%s, chunks=%d", job_id, len(chunks))
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.updated_at = datetime.utcnow()
            logger.error("Ingestion failed: job_id=%s, error=%s", job_id, e)
