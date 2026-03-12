# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

TravelBot AI — RAG-powered chatbot MVP for travel agencies. Validates AI-powered customer support with a real knowledge base, structured responses, and human escalation. The codebase is not yet implemented; `requirements.md`, `design.md`, and `tasks.md` define what to build.

## Commands

```bash
# Install dependencies (Python >=3.11 required)
uv sync

# Run the API server
uvicorn app.main:app --reload

# Run all tests
pytest

# Run a single test file
pytest tests/unit/test_formatter.py -v

# Run a specific test
pytest tests/unit/test_formatter.py::test_valid_json_returns_chat_response -v

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Lint
ruff check .

# Type check
mypy app/
```

Test markers: `pytest -m unit`, `pytest -m integration`, `pytest -m e2e`

## Architecture

The app is structured in four strict layers — each layer only calls inward:

```
API Layer → Service Layer → Core Engine → Infrastructure (VectorStore, LLMGateway)
```

**`app/api/routers/`** — FastAPI route handlers. No business logic. Translate HTTP ↔ service calls.

**`app/services/`** — Two services orchestrate all work:
- `ChatService` — wires RAGRetriever → LLMGateway → ResponseFormatter → RoutingEngine into one `chat()` call
- `IngestionService` — runs parse → chunk → embed → upsert as a background task; holds in-memory job state

**`app/core/`** — Pure business logic, no framework dependencies:
- `rag/` — `RAGRetriever` (embed query → vector search → score filter) and `PromptBuilder` (assembles system + context + user prompt)
- `llm/` — `LLMGateway` abstract base + `ClaudeAdapter` / `OpenAIAdapter`. Active adapter chosen at startup by `LLM_PROVIDER` env var via `factory.py`. **Never reference a concrete adapter outside `app/core/llm/`.**
- `vector_store/` — `VectorStore` abstract base + `ChromaVectorStore`. **Never reference ChromaDB outside `app/core/vector_store/`.**
- `document/` — `parser.py` (PDF/txt/JSON → raw text) and `chunker.py` (raw text → `list[Chunk]`)
- `formatter.py` — Parses LLM JSON output into `ChatResponse`. Always returns a safe fallback on failure; never raises.
- `router.py` — `RoutingEngine` checks 4 conditions for escalation. `should_escalate()` is a pure function with no side effects.

**`app/models/`** — Pydantic schemas only. `ChatResponse` is the canonical response shape used end-to-end.

**`app/config.py`** — Single `Settings(BaseSettings)` instance via `get_settings()` (lru_cache). All tunables live here.

## Key Design Constraints

- **LLM and VectorStore are behind interfaces.** Swapping providers = new adapter class only. No provider-specific imports outside their respective `app/core/` subdirectories.
- **API is stateless.** `session_id` is client-generated and used only for log correlation. No server-side session state.
- **Ingestion is async.** `POST /ingest` returns `job_id` immediately (`202`). Status is polled via `GET /ingest/{job_id}`.
- **Formatter never raises.** On any LLM output parse failure it returns `FALLBACK_RESPONSE` with `escalate=True`.
- **Escalation has 4 triggers** (any one is sufficient): retrieval score below threshold, LLM reports `confidence=low`, explicit human-request pattern in message, formatter used fallback.

## Environment Variables

Copy `.env.example` to `.env`. Required vars:

| Var | Default | Notes |
|-----|---------|-------|
| `LLM_PROVIDER` | `claude` | `claude` or `openai` |
| `CLAUDE_API_KEY` | — | Required if `LLM_PROVIDER=claude` |
| `OPENAI_API_KEY` | — | Required if `LLM_PROVIDER=openai` or for embeddings |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | Use `:memory:` for tests |
| `CONFIDENCE_THRESHOLD` | `0.60` | Escalation trigger |
| `SIMILARITY_THRESHOLD` | `0.70` | Retrieval score filter |

## Task Tracking

`tasks.md` contains 30 implementation tasks (T-01–T-30). Update status symbols as work progresses:
- `[ ]` todo → `[~]` in-progress → `[x]` done

Critical path for a working demo: T-01 → T-03 → T-04 → T-05 → T-06 → T-07 → T-10 → T-11 → T-13 → T-08 → T-09 → T-14 → T-15 → T-16 → T-17 → T-18 → T-19 → T-20 → T-21 → T-22 → T-23 → T-24
