import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.core.formatter import ResponseFormatter
from app.core.llm.factory import get_llm_gateway
from app.core.rag.retriever import RAGRetriever
from app.core.router import RoutingEngine
from app.core.vector_store.chroma import ChromaVectorStore
from app.models.chat import ErrorDetail, ErrorResponse
from app.services.chat_service import ChatService
from app.services.ingestion_service import IngestionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    vector_store = ChromaVectorStore(persist_dir=settings.CHROMA_PERSIST_DIR)
    llm = get_llm_gateway(settings)
    retriever = RAGRetriever(vector_store=vector_store, llm=llm, settings=settings)
    formatter = ResponseFormatter()
    router = RoutingEngine(settings=settings)
    app.state.chat_service = ChatService(
        retriever=retriever, llm=llm, formatter=formatter, router=router
    )
    app.state.ingestion_service = IngestionService(
        vector_store=vector_store, llm=llm, settings=settings
    )
    logger.info("TravelBot AI started — provider=%s", settings.LLM_PROVIDER)
    yield
    logger.info("TravelBot AI shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="TravelBot AI",
        version=settings.APP_VERSION,
        docs_url="/api/v1/docs",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_logging(request: Request, call_next):
        start = time.time()
        response: Response = await call_next(request)
        duration_ms = int((time.time() - start) * 1000)
        logger.info(
            "%s %s %d %dms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception: %s", exc, exc_info=True)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(code="INTERNAL_ERROR", message="An internal error occurred")
            ).model_dump(),
        )

    from app.api.routers import health, chat, ingest
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(ingest.router, prefix="/api/v1")

    return app


app = create_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
