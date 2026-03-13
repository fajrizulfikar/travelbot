import logging
import time

from app.core.formatter import ResponseFormatter
from app.core.rag.prompt_builder import build_prompt
from app.core.rag.retriever import RAGRetriever
from app.core.llm.gateway import LLMGateway
from app.core.router import RoutingEngine
from app.models.chat import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        retriever: RAGRetriever,
        llm: LLMGateway,
        formatter: ResponseFormatter,
        router: RoutingEngine,
    ):
        self._retriever = retriever
        self._llm = llm
        self._formatter = formatter
        self._router = router

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.time()
        chunks, max_score = await self._retriever.retrieve(request.message)
        system, prompt = build_prompt(request.message, chunks)
        raw = await self._llm.complete(prompt, system)
        response, used_fallback = self._formatter.parse(raw, request.session_id)
        if self._router.should_escalate(response, max_score, request.message, used_fallback):
            response = self._router.escalate_response(response)
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "chat: session_id=%s score=%.2f confidence=%s escalate=%s duration_ms=%d",
            request.session_id, max_score, response.confidence, response.escalate, duration_ms,
        )
        return response
