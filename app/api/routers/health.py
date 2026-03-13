from fastapi import APIRouter, Depends
from app.config import Settings, get_settings

router = APIRouter()


@router.get("/health")
async def health(settings: Settings = Depends(get_settings)):
    return {"status": "ok", "version": settings.APP_VERSION}
