from typing import Annotated, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    message: Annotated[str, Field(min_length=1, max_length=2000)]


class ChatResponse(BaseModel):
    answer: str
    booking_link: str | None = None
    related_services: list[str] = []
    confidence: Literal["high", "medium", "low"] = "low"
    escalate: bool = False
    session_id: str = ""


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict = {}


class ErrorResponse(BaseModel):
    error: ErrorDetail
