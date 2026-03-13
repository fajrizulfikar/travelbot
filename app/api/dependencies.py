from fastapi import Request
from app.services.chat_service import ChatService
from app.services.ingestion_service import IngestionService


def get_chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


def get_ingestion_service(request: Request) -> IngestionService:
    return request.app.state.ingestion_service
