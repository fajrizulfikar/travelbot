# TravelBot AI — Implementation Tasks

## Status Legend
| Symbol | Status |
|--------|--------|
| `[ ]` | todo |
| `[~]` | in-progress |
| `[x]` | done |
| `[!]` | blocked |

---

## Task Groups

1. [Project Scaffold](#group-1-project-scaffold)
2. [Configuration & Environment](#group-2-configuration--environment)
3. [Data Models](#group-3-data-models)
4. [Vector Store Abstraction](#group-4-vector-store-abstraction)
5. [Document Processing](#group-5-document-processing)
6. [LLM Gateway](#group-6-llm-gateway)
7. [RAG Engine](#group-7-rag-engine)
8. [Response Formatter](#group-8-response-formatter)
9. [Routing Engine](#group-9-routing-engine)
10. [Ingestion Service](#group-10-ingestion-service)
11. [Chat Service](#group-11-chat-service)
12. [API Layer](#group-12-api-layer)
13. [Web Chat Widget](#group-13-web-chat-widget)
14. [Tests](#group-14-tests)
15. [Docs & Packaging](#group-15-docs--packaging)

---

## Group 1 — Project Scaffold

### T-01 · Initialize Python project
- **Status:** `[x]`
- **File(s):** `pyproject.toml`, `.python-version`
- **Steps:**
  1. Create `pyproject.toml` using `uv init` or manual definition
  2. Set Python `>=3.11`
  3. Define project metadata (name, version, description)
- **Done when:** `python -m travelbot` runs without import errors; `uv sync` installs all deps cleanly

---

### T-02 · Install core dependencies
- **Status:** `[x]`
- **Depends on:** T-01
- **File(s):** `pyproject.toml`
- **Dependencies to add:**
  ```
  fastapi>=0.111
  uvicorn[standard]>=0.29
  pydantic>=2.7
  pydantic-settings>=2.3
  anthropic>=0.28
  openai>=1.30
  langchain>=0.2
  langchain-community>=0.2
  langchain-openai>=0.1
  chromadb>=0.5
  python-multipart>=0.0.9
  pypdf>=4.2
  httpx>=0.27
  tenacity>=8.3
  python-dotenv>=1.0
  ```
  Dev dependencies:
  ```
  pytest>=8.2
  pytest-asyncio>=0.23
  pytest-cov>=5.0
  httpx>=0.27          # TestClient
  ruff>=0.4
  mypy>=1.10
  vcrpy>=6.0
  ```
- **Done when:** `uv sync` succeeds with no conflicts; `import fastapi, chromadb, anthropic` all resolve

---

### T-03 · Create directory structure
- **Status:** `[x]`
- **Depends on:** T-01
- **File(s):** all `__init__.py` files, directory skeleton
- **Steps:**
  1. Create all directories per `design.md` project structure
  2. Add `__init__.py` to every package directory
  3. Create `app/`, `app/api/`, `app/api/routers/`, `app/services/`, `app/core/`, `app/core/rag/`, `app/core/llm/`, `app/core/vector_store/`, `app/core/document/`, `app/models/`, `frontend/`, `tests/unit/`, `tests/integration/`, `tests/e2e/`
- **Done when:** `find . -name "__init__.py"` shows one file per package; no import path errors

---

## Group 2 — Configuration & Environment

### T-04 · Implement app configuration
- **Status:** `[x]`
- **Depends on:** T-03
- **File(s):** `app/config.py`, `.env.example`
- **Steps:**
  1. Define `Settings(BaseSettings)` with all env vars:
     - `LLM_PROVIDER: str = "claude"`
     - `CLAUDE_API_KEY: str`
     - `OPENAI_API_KEY: str = ""`
     - `VECTOR_STORE_BACKEND: str = "chroma"`
     - `CHROMA_PERSIST_DIR: str = "./data/chroma"`
     - `CONFIDENCE_THRESHOLD: float = 0.60`
     - `SIMILARITY_THRESHOLD: float = 0.70`
     - `TOP_N_RESULTS: int = 5`
     - `MAX_FILE_SIZE_MB: int = 50`
     - `LOG_LEVEL: str = "INFO"`
     - `CORS_ORIGINS: list[str] = ["*"]`
  2. Use `lru_cache` singleton to expose `get_settings()`
  3. Create `.env.example` with all vars, empty secrets, documented defaults
- **Done when:** `Settings()` loads correctly from `.env`; missing required vars raise a clear error at startup

---

## Group 3 — Data Models

### T-05 · Implement Pydantic models
- **Status:** `[x]`
- **Depends on:** T-03
- **File(s):** `app/models/chat.py`, `app/models/ingest.py`
- **Steps:**
  1. `app/models/chat.py`:
     - `ChatRequest(BaseModel)`: `session_id: str`, `message: Annotated[str, MinLen(1), MaxLen(2000)]`
     - `ChatResponse(BaseModel)`: `answer`, `booking_link: str | None`, `related_services: list[str]`, `confidence: Literal["high","medium","low"]`, `escalate: bool`, `session_id: str`
     - `ErrorDetail(BaseModel)`: `code`, `message`, `details: dict`
     - `ErrorResponse(BaseModel)`: `error: ErrorDetail`
  2. `app/models/ingest.py`:
     - `IngestJob(BaseModel)`: `job_id`, `filename`, `status: Literal["pending","processing","completed","failed"]`, `error: str | None`, `chunk_count: int | None`, `created_at`, `updated_at`
  3. Internal models (`app/core/`):
     - `Chunk`: `id`, `source_id`, `text`, `embedding: list[float]`, `metadata: dict`
     - `SearchResult`: `chunk: Chunk`, `score: float`
- **Done when:** All models instantiate correctly; Pydantic validation rejects invalid input (e.g., message > 2000 chars raises `ValidationError`)

---

## Group 4 — Vector Store Abstraction

### T-06 · Define VectorStore interface
- **Status:** `[x]`
- **Depends on:** T-05
- **File(s):** `app/core/vector_store/base.py`
- **Steps:**
  1. Define `VectorStore(ABC)` with three abstract async methods: `upsert`, `query`, `delete_by_source`
  2. Define method signatures exactly as in `design.md §3.2`
- **Done when:** Class is importable; attempting to instantiate directly raises `TypeError`

---

### T-07 · Implement ChromaDB vector store
- **Status:** `[x]`
- **Depends on:** T-06
- **File(s):** `app/core/vector_store/chroma.py`
- **Steps:**
  1. Implement `ChromaVectorStore(VectorStore)`
  2. `__init__`: initialize `chromadb.Client` (persistent or in-memory based on `CHROMA_PERSIST_DIR`)
  3. `upsert`: batch insert chunks with embeddings and metadata
  4. `query`: cosine similarity search, return `list[SearchResult]` sorted by score descending
  5. `delete_by_source`: delete all chunks matching `source_id` metadata field
  6. Handle `chromadb` exceptions, wrap in application-level errors
- **Done when:** Unit test inserts 5 chunks, queries with a vector, returns top-3 results with correct scores; `delete_by_source` leaves zero matching documents

---

## Group 5 — Document Processing

### T-08 · Implement document parser
- **Status:** `[x]`
- **Depends on:** T-03
- **File(s):** `app/core/document/parser.py`
- **Steps:**
  1. `parse_pdf(file_bytes: bytes) -> str` — use `langchain_community.document_loaders.PyPDFLoader` (write to temp file, extract text, clean up)
  2. `parse_txt(file_bytes: bytes) -> str` — UTF-8 decode
  3. `parse_faq_json(file_bytes: bytes) -> str` — parse JSON array of `{question, answer}` objects, join into readable text
  4. `parse(filename: str, file_bytes: bytes) -> str` — dispatch by file extension; raise `ValueError` for unsupported types
- **Done when:** Parser extracts non-empty text from a sample PDF and a sample FAQ JSON; unsupported extension raises `ValueError` with the filename included in the message

---

### T-09 · Implement text chunker
- **Status:** `[x]`
- **Depends on:** T-03
- **File(s):** `app/core/document/chunker.py`
- **Steps:**
  1. `chunk(text: str, source_id: str, chunk_size: int = 512, overlap: int = 50) -> list[Chunk]`
  2. Use `langchain.text_splitter.RecursiveCharacterTextSplitter`
  3. Generate a UUID per chunk; populate `metadata` with `chunk_index`
  4. Return empty list (not error) for empty/whitespace-only input
  5. Leave `embedding` field as empty list (filled later by ingestion service)
- **Done when:** 1000-token input produces ≥2 chunks, each ≤512 tokens; overlap content appears at the boundary between consecutive chunks

---

## Group 6 — LLM Gateway

### T-10 · Define LLMGateway interface
- **Status:** `[x]`
- **Depends on:** T-03
- **File(s):** `app/core/llm/gateway.py`
- **Steps:**
  1. Define `LLMGateway(ABC)` with two abstract async methods:
     - `complete(prompt: str, system: str) -> str`
     - `embed(text: str) -> list[float]`
- **Done when:** Interface is importable; concrete subclass must implement both methods to instantiate

---

### T-11 · Implement Claude adapter
- **Status:** `[x]`
- **Depends on:** T-10
- **File(s):** `app/core/llm/claude_adapter.py`
- **Steps:**
  1. `ClaudeAdapter(LLMGateway)` using `anthropic.AsyncAnthropic`
  2. `complete()`: call `claude-sonnet-4-6`, pass `system` and `prompt` as user message, return text content
  3. `embed()`: delegate to OpenAI embedding (`text-embedding-3-small`) since Claude has no native embedding API
  4. Wrap both methods with `tenacity.retry`: max 3 attempts, exponential backoff (1s, 2s), retry on `anthropic.RateLimitError` and `anthropic.APIConnectionError`
  5. Raise `LLMUnavailableError` (custom exception) after exhausting retries
- **Done when:** Mocked Anthropic SDK returns a completion; retry fires on `RateLimitError`; `LLMUnavailableError` raised after 3 failures

---

### T-12 · Implement OpenAI adapter
- **Status:** `[x]`
- **Depends on:** T-10
- **File(s):** `app/core/llm/openai_adapter.py`
- **Steps:**
  1. `OpenAIAdapter(LLMGateway)` using `openai.AsyncOpenAI`
  2. `complete()`: call `gpt-4o`, return text content
  3. `embed()`: call `text-embedding-3-small`, return embedding vector
  4. Same retry policy as Claude adapter
- **Done when:** Mocked OpenAI SDK returns a completion and an embedding vector; retry behavior mirrors T-11

---

### T-13 · Implement LLM gateway factory
- **Status:** `[x]`
- **Depends on:** T-11, T-12, T-04
- **File(s):** `app/core/llm/factory.py`
- **Steps:**
  1. `get_llm_gateway(settings: Settings) -> LLMGateway`
  2. Returns `ClaudeAdapter` when `settings.LLM_PROVIDER == "claude"`
  3. Returns `OpenAIAdapter` when `settings.LLM_PROVIDER == "openai"`
  4. Raises `ValueError` for unknown provider
- **Done when:** Factory returns correct adapter type for each provider string; unknown string raises `ValueError`

---

## Group 7 — RAG Engine

### T-14 · Implement prompt builder
- **Status:** `[x]`
- **Depends on:** T-05
- **File(s):** `app/core/rag/prompt_builder.py`
- **Steps:**
  1. `SYSTEM_PROMPT` constant — instructs LLM to: answer only from context, respond as valid JSON matching `ChatResponse` schema, set `confidence` based on context quality, use `null` for `booking_link` if not in context
  2. `build_prompt(message: str, chunks: list[SearchResult]) -> tuple[str, str]` — returns `(system_prompt, user_prompt)`
  3. User prompt format: numbered context chunks followed by the question
  4. When `chunks` is empty, include explicit instruction: "No context found. Respond that you cannot answer this question and set confidence to low."
  5. Enforce max context length: trim oldest chunks if total tokens exceed 3000
- **Done when:** Prompt with 3 chunks contains all chunk text and the user question; empty chunks produce a prompt with the no-context instruction

---

### T-15 · Implement RAG retriever
- **Status:** `[x]`
- **Depends on:** T-06, T-10, T-14
- **File(s):** `app/core/rag/retriever.py`
- **Steps:**
  1. `RAGRetriever(vector_store: VectorStore, llm: LLMGateway, settings: Settings)`
  2. `retrieve(query: str) -> tuple[list[SearchResult], float]`:
     - Embed `query` via `llm.embed()`
     - Call `vector_store.query(vector, top_n=settings.TOP_N_RESULTS)`
     - Filter results where `score >= settings.SIMILARITY_THRESHOLD`
     - Return filtered results and max score (0.0 if no results pass filter)
- **Done when:** Query matching seeded chunks returns results above threshold; unrelated query returns empty list with score 0.0

---

## Group 8 — Response Formatter

### T-16 · Implement response formatter
- **Status:** `[x]`
- **Depends on:** T-05
- **File(s):** `app/core/formatter.py`
- **Steps:**
  1. `FALLBACK_RESPONSE` constant (as defined in `design.md §3.4`)
  2. `parse(raw_text: str, session_id: str) -> ChatResponse`:
     - Strip markdown code fences if present (` ```json ... ``` `)
     - `json.loads()` the content
     - Validate against `ChatResponse` fields; fill missing optional fields with defaults
     - Clamp `related_services` to max 3 items
     - Return `ChatResponse` with `session_id` injected
  3. On any exception (`JSONDecodeError`, `ValidationError`, `KeyError`): log warning with raw_text hash, return `FALLBACK_RESPONSE` with the provided `session_id`
- **Done when:** Valid JSON string → correct `ChatResponse`; invalid JSON → `FALLBACK_RESPONSE` with `escalate=true`; JSON missing optional fields → filled with safe defaults

---

## Group 9 — Routing Engine

### T-17 · Implement routing engine
- **Status:** `[x]`
- **Depends on:** T-05, T-04
- **File(s):** `app/core/router.py`
- **Steps:**
  1. `HUMAN_REQUEST_PATTERNS: list[str]` — regex patterns for: `speak to agent`, `human`, `representative`, `talk to someone`, `need help`, `contact support`
  2. `RoutingEngine(settings: Settings)`
  3. `should_escalate(response: ChatResponse, max_score: float, message: str, formatter_used_fallback: bool) -> bool`:
     - Return `True` if any condition is met:
       1. `max_score < settings.CONFIDENCE_THRESHOLD`
       2. `response.confidence == "low"`
       3. Any `HUMAN_REQUEST_PATTERNS` matches `message` (case-insensitive)
       4. `formatter_used_fallback is True`
  4. `escalate_response(response: ChatResponse) -> ChatResponse`: set `escalate=True`, update `answer` to handoff message
- **Done when:** Each of the 4 conditions independently triggers `should_escalate=True`; none of the conditions being met returns `False`

---

## Group 10 — Ingestion Service

### T-18 · Implement ingestion service
- **Status:** `[x]`
- **Depends on:** T-07, T-08, T-09, T-10, T-05
- **File(s):** `app/services/ingestion_service.py`
- **Steps:**
  1. `IngestionService(vector_store: VectorStore, llm: LLMGateway, settings: Settings)`
  2. `in_memory_jobs: dict[str, IngestJob]` — job state store
  3. `create_job(filename: str) -> IngestJob` — generate UUID, set `status=pending`
  4. `get_job(job_id: str) -> IngestJob | None`
  5. `run(job_id: str, filename: str, file_bytes: bytes) -> None` (async, runs as background task):
     - Set `status=processing`
     - `parse()` → raw text
     - `chunk()` → chunks
     - For each chunk: `llm.embed(chunk.text)` → set `chunk.embedding`
     - Embed in batches of 20 to avoid rate limits
     - `vector_store.upsert(chunks)`
     - Set `status=completed`, `chunk_count=len(chunks)`, `updated_at=now()`
     - On any exception: set `status=failed`, `error=str(exception)`, log ERROR
- **Done when:** End-to-end: create job → run with test PDF bytes → job status becomes `completed` with correct `chunk_count`; corrupt file input → status becomes `failed` with non-empty `error`

---

## Group 11 — Chat Service

### T-19 · Implement chat service
- **Status:** `[x]`
- **Depends on:** T-15, T-11, T-14, T-16, T-17
- **File(s):** `app/services/chat_service.py`
- **Steps:**
  1. `ChatService(retriever: RAGRetriever, llm: LLMGateway, formatter: ResponseFormatter, router: RoutingEngine)`
  2. `chat(request: ChatRequest) -> ChatResponse`:
     - `chunks, max_score = await retriever.retrieve(request.message)`
     - `system, prompt = prompt_builder.build_prompt(request.message, chunks)`
     - `raw = await llm.complete(prompt, system)`
     - `response, used_fallback = formatter.parse(raw, request.session_id)` — track if fallback was used
     - `if router.should_escalate(response, max_score, request.message, used_fallback): response = router.escalate_response(response)`
     - Return `response`
  3. Log: `session_id`, retrieval score, confidence, `escalate` flag, duration_ms at INFO level
- **Done when:** Full pipeline from `ChatRequest` → `ChatResponse` with correct `escalate` flag set; slow LLM mock still returns within service timeout

---

## Group 12 — API Layer

### T-20 · Implement health router
- **Status:** `[x]`
- **Depends on:** T-03
- **File(s):** `app/api/routers/health.py`
- **Steps:**
  1. `GET /health` → `200 {"status": "ok", "version": settings.APP_VERSION}`
- **Done when:** `curl /health` returns `200` with JSON body

---

### T-21 · Implement chat router
- **Status:** `[x]`
- **Depends on:** T-19, T-05
- **File(s):** `app/api/routers/chat.py`
- **Steps:**
  1. `POST /chat`:
     - Accept `ChatRequest` body
     - Inject `ChatService` via FastAPI dependency
     - Call `await chat_service.chat(request)`
     - Return `ChatResponse` with `200`
  2. Handle `ValidationError` → `422` with field details
  3. Handle `LLMUnavailableError` → `503` with `LLM_UNAVAILABLE` error code
  4. Handle unhandled exceptions → `500` with `INTERNAL_ERROR` (no stack trace in response)
- **Done when:** `POST /chat` with valid body returns `200`; missing `message` field returns `422`; `LLMUnavailableError` returns `503`

---

### T-22 · Implement ingest router
- **Status:** `[x]`
- **Depends on:** T-18, T-05
- **File(s):** `app/api/routers/ingest.py`
- **Steps:**
  1. `POST /ingest` (multipart/form-data, field name: `file`):
     - Validate MIME type: `application/pdf`, `text/plain`, `application/json`
     - Validate size ≤ `settings.MAX_FILE_SIZE_MB` MB
     - Call `ingestion_service.create_job(filename)` → return `202` with `IngestJob`
     - Schedule `ingestion_service.run(...)` as `BackgroundTasks`
  2. `GET /ingest/{job_id}`:
     - Return `IngestJob` if found → `200`
     - Return `404` if `job_id` unknown
  3. Invalid file type → `422` with `INVALID_FILE_TYPE`
  4. File too large → `422` with `FILE_TOO_LARGE`
- **Done when:** Upload returns `202` with `job_id`; polling returns current status; unknown ID returns `404`

---

### T-23 · Implement FastAPI app factory and middleware
- **Status:** `[x]`
- **Depends on:** T-20, T-21, T-22, T-04
- **File(s):** `app/main.py`, `app/api/dependencies.py`
- **Steps:**
  1. `create_app() -> FastAPI` factory:
     - Register all three routers with `/api/v1` prefix
     - Add `CORSMiddleware` with `settings.CORS_ORIGINS`
     - Add request logging middleware (log method, path, status, duration_ms)
     - Add global exception handler → always returns JSON error body, never HTML
     - Lifespan: initialize `VectorStore`, `LLMGateway`, `ChatService`, `IngestionService` on startup; close connections on shutdown
  2. `app/api/dependencies.py`:
     - `get_chat_service()`, `get_ingestion_service()` — FastAPI `Depends` functions using app state
  3. Entry point: `if __name__ == "__main__": uvicorn.run("app.main:app", ...)`
- **Done when:** `uvicorn app.main:app --reload` starts without errors; all routes registered and reachable; unhandled error returns JSON (not HTML 500 page)

---

## Group 13 — Web Chat Widget

### T-24 · Build web chat widget
- **Status:** `[x]`
- **Depends on:** T-23
- **File(s):** `frontend/index.html`
- **Steps:**
  1. Single self-contained HTML file (no external build tools, no CDN dependencies)
  2. Layout: full-height chat thread + fixed input bar at bottom
  3. Render user message in a right-aligned bubble immediately on send
  4. Show a typing indicator while waiting for API response
  5. Render bot response with three visually distinct sections:
     - **Answer** — primary text bubble
     - **Booking Link** — button (only rendered when non-null)
     - **Related Services** — tag chips (only rendered when array non-empty)
  6. On `escalate: true` — show a yellow/amber "Connecting you to an agent..." banner
  7. On API error — show an inline error message, keep input enabled for retry
  8. Auto-scroll to the latest message
  9. Enter key submits; disabled while request is in-flight
  10. Hardcode API base URL to `http://localhost:8000/api/v1` for demo (comment for easy swap)
  11. Generate `session_id` as `crypto.randomUUID()` on page load; persist for the session
- **Done when:** Widget loads in Chrome/Firefox/Safari; full send → response → render cycle works end-to-end; escalation banner appears for escalated responses; error state renders without crashing

---

## Group 14 — Tests

### T-25 · Write unit tests — formatter and router
- **Status:** `[x]`
- **Depends on:** T-16, T-17
- **File(s):** `tests/unit/test_formatter.py`, `tests/unit/test_router.py`
- **Coverage target: 100%**
- **Formatter tests:**
  - Valid JSON → correct `ChatResponse` fields
  - JSON with markdown code fences stripped → parses correctly
  - `related_services` > 3 items → clamped to 3
  - `JSONDecodeError` → `FALLBACK_RESPONSE` returned
  - Missing required field → `FALLBACK_RESPONSE` returned
  - `session_id` always present in returned response
- **Router tests:**
  - `max_score < threshold` → escalates
  - `confidence == "low"` → escalates
  - `"speak to agent"` in message → escalates
  - `formatter_used_fallback=True` → escalates
  - All conditions false → no escalation
  - `escalate_response()` sets `escalate=True` and updates `answer`
- **Done when:** `pytest tests/unit/test_formatter.py tests/unit/test_router.py --cov` reports 100% coverage on both files

---

### T-26 · Write unit tests — retriever, chunker, parser
- **Status:** `[x]`
- **Depends on:** T-08, T-09, T-15
- **File(s):** `tests/unit/test_retriever.py`, `tests/unit/test_chunker.py`, `tests/unit/test_parser.py`
- **Retriever tests:**
  - Results above threshold returned; results below filtered out
  - Empty vector store → empty list + score 0.0
  - `embed()` called once per query
- **Chunker tests:**
  - Output chunks each ≤ chunk_size
  - Overlap content present at chunk boundaries
  - Empty input → empty list (no error)
  - Each chunk has a unique UUID
- **Parser tests:**
  - PDF bytes → non-empty string
  - Valid FAQ JSON → non-empty string
  - Plain text bytes → original content preserved
  - Unsupported extension → `ValueError`
- **Done when:** `pytest tests/unit/ --cov` passes; overall unit coverage ≥ 80%

---

### T-27 · Write integration tests — chat and ingestion services
- **Status:** `[x]`
- **Depends on:** T-18, T-19
- **File(s):** `tests/integration/test_chat_service.py`, `tests/integration/test_ingestion_service.py`
- **Setup:** In-memory ChromaDB (`CHROMA_PERSIST_DIR=:memory:`); LLM gateway mocked to return pre-recorded fixture responses
- **Chat service tests:**
  - Known question → chunks retrieved → mocked LLM → structured response returned
  - Unknown question (no matching chunks) → `escalate=True` in response
  - LLM returns malformed JSON → fallback response with `escalate=True`
  - Explicit human request message → `escalate=True`
- **Ingestion service tests:**
  - Upload small PDF fixture → job reaches `completed`, `chunk_count > 0`
  - Upload FAQ JSON fixture → job reaches `completed`
  - Corrupt file bytes → job reaches `failed`, `error` non-empty
  - `get_job()` returns correct status after each state transition
- **Done when:** All integration tests pass with mocked LLM; no real API calls made during CI

---

### T-28 · Write end-to-end API tests
- **Status:** `[x]`
- **Depends on:** T-23, T-27
- **File(s):** `tests/e2e/test_api.py`, `tests/conftest.py`
- **Setup:** `httpx.AsyncClient` against live FastAPI app via `TestClient`; LLM intercepted by VCR cassette fixtures; in-memory ChromaDB
- **Tests:**
  - `GET /health` → `200`
  - `POST /chat` valid body → `200`, all schema fields present
  - `POST /chat` missing `message` → `422`
  - `POST /chat` message > 2000 chars → `422`
  - `POST /ingest` valid PDF → `202` with `job_id`
  - `GET /ingest/{job_id}` → `200` with status
  - `GET /ingest/unknown-id` → `404`
  - `POST /ingest` unsupported file type → `422`
  - `POST /ingest` file > 50 MB → `422`
  - Full flow: ingest PDF → chat with known question → verify answer is grounded
- **Done when:** `pytest tests/e2e/` passes; no live LLM calls; all HTTP status codes match spec

---

## Group 15 — Docs & Packaging

### T-29 · Create .env.example and README
- **Status:** `[x]`
- **Depends on:** T-04
- **File(s):** `.env.example`, `README.md`
- **Steps:**
  1. `.env.example`: all env vars from T-04, empty secret values, inline comments explaining each var
  2. `README.md`:
     - Quick start (clone → copy `.env.example` → `uv sync` → `uvicorn`)
     - How to ingest a file (`curl` example)
     - How to chat (`curl` example)
     - How to open the widget (open `frontend/index.html`)
     - How to run tests
- **Done when:** A developer can clone the repo and run the app by following only the README, with zero prior context

---

### T-30 · Verify OpenAPI spec generation
- **Status:** `[x]`
- **Depends on:** T-23
- **File(s):** auto-generated at `/api/v1/docs` and `/api/v1/openapi.json`
- **Steps:**
  1. Start server and confirm `/api/v1/docs` renders Swagger UI
  2. Confirm `/api/v1/openapi.json` is valid and contains all 4 endpoints
  3. Export spec to `openapi.json` in project root for reference
- **Done when:** All 4 endpoints appear in the Swagger UI with correct request/response schemas; spec file committed to repo

---

## Run Order

### Run all in sequence
```
T-01 → T-02 → T-03 → T-04 → T-05
                                 ↓
T-06 → T-07          T-08 → T-09
  ↓                       ↓
T-10 → T-11 → T-12 → T-13
  ↓
T-14 → T-15
  ↓
T-16 → T-17
  ↓
T-18   T-19
  ↓      ↓
T-20 → T-21 → T-22 → T-23
                         ↓
                       T-24
                         ↓
              T-25 → T-26 → T-27 → T-28
                                      ↓
                              T-29 → T-30
```

### Critical path (minimum viable demo)
`T-01 → T-02 → T-03 → T-04 → T-05 → T-06 → T-07 → T-10 → T-11 → T-13 → T-08 → T-09 → T-14 → T-15 → T-16 → T-17 → T-18 → T-19 → T-20 → T-21 → T-22 → T-23 → T-24`

### Run individually
Each task is self-contained — implement the listed file(s), verify the "Done when" condition, update status from `[ ]` to `[x]`.

---

## Progress

| Group | Tasks | Done |
|-------|-------|------|
| 1 · Project Scaffold | T-01, T-02, T-03 | 3 / 3 |
| 2 · Configuration | T-04 | 1 / 1 |
| 3 · Data Models | T-05 | 1 / 1 |
| 4 · Vector Store | T-06, T-07 | 2 / 2 |
| 5 · Document Processing | T-08, T-09 | 2 / 2 |
| 6 · LLM Gateway | T-10, T-11, T-12, T-13 | 4 / 4 |
| 7 · RAG Engine | T-14, T-15 | 2 / 2 |
| 8 · Response Formatter | T-16 | 1 / 1 |
| 9 · Routing Engine | T-17 | 1 / 1 |
| 10 · Ingestion Service | T-18 | 1 / 1 |
| 11 · Chat Service | T-19 | 1 / 1 |
| 12 · API Layer | T-20, T-21, T-22, T-23 | 4 / 4 |
| 13 · Web Chat Widget | T-24 | 1 / 1 |
| 14 · Tests | T-25, T-26, T-27, T-28 | 4 / 4 |
| 15 · Docs & Packaging | T-29, T-30 | 2 / 2 |
| **Total** | | **30 / 30** |
