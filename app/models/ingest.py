from datetime import datetime
from typing import Literal
from pydantic import BaseModel


class IngestJob(BaseModel):
    job_id: str
    filename: str
    status: Literal["pending", "processing", "completed", "failed"] = "pending"
    error: str | None = None
    chunk_count: int | None = None
    created_at: datetime
    updated_at: datetime
