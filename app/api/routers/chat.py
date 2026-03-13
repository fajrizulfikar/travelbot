from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import ChatRequest, ChatResponse, ErrorResponse, ErrorDetail
from app.services.chat_service import ChatService
from app.api.dependencies import get_chat_service
from app.core.llm.gateway import LLMUnavailableError

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        return await chat_service.chat(request)
    except LLMUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail=ErrorResponse(
                error=ErrorDetail(code="LLM_UNAVAILABLE", message=str(e))
            ).model_dump(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message="An internal error occurred")
            ).model_dump(),
        )
