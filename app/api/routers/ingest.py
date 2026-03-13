from fastapi import APIRouter, Depends, HTTPException, UploadFile, BackgroundTasks
from app.models.ingest import IngestJob
from app.models.chat import ErrorDetail, ErrorResponse
from app.services.ingestion_service import IngestionService
from app.api.dependencies import get_ingestion_service
from app.config import Settings, get_settings

ALLOWED_MIME_TYPES = {"application/pdf", "text/plain", "application/json"}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".json"}

router = APIRouter()


@router.post("/ingest", status_code=202, response_model=IngestJob)
async def ingest_file(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
    settings: Settings = Depends(get_settings),
):
    from pathlib import Path
    ext = Path(file.filename or "").suffix.lower()
    content_type = file.content_type or ""

    if ext not in ALLOWED_EXTENSIONS and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="INVALID_FILE_TYPE",
                    message=f"Unsupported file type: {file.filename}",
                )
            ).model_dump(),
        )

    file_bytes = await file.read()
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code="FILE_TOO_LARGE",
                    message=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
                )
            ).model_dump(),
        )

    job = ingestion_service.create_job(file.filename or "unknown")
    background_tasks.add_task(
        ingestion_service.run, job.job_id, file.filename or "unknown", file_bytes
    )
    return job


@router.get("/ingest/{job_id}", response_model=IngestJob)
async def get_ingest_job(
    job_id: str,
    ingestion_service: IngestionService = Depends(get_ingestion_service),
):
    job = ingestion_service.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail=ErrorResponse(
                error=ErrorDetail(code="NOT_FOUND", message=f"Job {job_id} not found")
            ).model_dump(),
        )
    return job
