# TravelBot AI — Technical Design

## Table of Contents

1. [Tech Stack](#1-tech-stack)
2. [System Architecture](#2-system-architecture)
3. [Component Design](#3-component-design)
4. [Data Models](#4-data-models)
5. [Sequence Diagrams](#5-sequence-diagrams)
6. [Data Flow](#6-data-flow)
7. [Error Handling Strategy](#7-error-handling-strategy)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| API Framework | **FastAPI** (Python) | Async-native, auto OpenAPI spec generation, Pydantic validation built-in |
| LLM Gateway | **Anthropic Claude** (default) | Pluggable — Claude / GPT-4 / Gemini via adapter pattern |
| Embeddings | **OpenAI `text-embedding-3-small`** | High quality, cost-efficient; swappable via same adapter pattern |
| Vector Store | **ChromaDB** (MVP) | Zero-infrastructure, file-persisted; abstracted for Pinecone/pgvector migration |
| Document Parsing | **LangChain** (PDF + text loaders) | Mature chunking strategies; decoupled from retrieval logic |
| Job State | **In-memory dict + UUID** (MVP) | Sufficient for demo; swap to Redis/DB for production |
| Frontend | **Vanilla HTML/CSS/JS** | Zero build tooling for demo speed; ships as a single file |
| Configuration | **Pydantic Settings + `.env`** | Type-safe config, secrets via environment variables |

---

## 2. System Architecture

### High-Level Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│                                                                 │
│              Web Chat Widget (HTML/CSS/JS)                      │
│                   Demo Portal (static)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP/JSON
┌───────────────────────────▼─────────────────────────────────────┐
│                          API LAYER                              │
│                                                                 │
│   FastAPI Application                                           │
│   ├── POST /chat          (ChatRouter)                          │
│   ├── POST /ingest        (IngestRouter)                        │
│   ├── GET  /ingest/{id}   (IngestRouter)                        │
│   └── GET  /health        (HealthRouter)                        │
│                                                                 │
│   Middleware: request logging, error handling, CORS             │
└──────┬────────────────────────────────────┬──────────────────────┘
       │                                    │
┌──────▼──────────────┐          ┌──────────▼──────────────────────┐
│   CHAT SERVICE      │          │      INGESTION SERVICE           │
│                     │          │                                  │
│  1. Validate input  │          │  1. Validate file type/size     │
│  2. Retrieve chunks │          │  2. Parse document              │
│  3. Build prompt    │          │  3. Chunk text                  │
│  4. Call LLM        │          │  4. Generate embeddings         │
│  5. Format response │          │  5. Store in vector store       │
│  6. Route/escalate  │          │  6. Update job status           │
└──────┬──────────────┘          └──────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────────────────────────┐
│                         CORE ENGINE                             │
│                                                                 │
│  ┌──────────────────┐   ┌───────────────────┐                  │
│  │   RAG Retriever   │   │   LLM Gateway     │                  │
│  │                  │   │                   │                  │
│  │ - embed query    │   │ - ClaudeAdapter   │                  │
│  │ - similarity     │   │ - OpenAIAdapter   │                  │
│  │   search (top-N) │   │ - GeminiAdapter   │                  │
│  │ - score filter   │   │ (active: config)  │                  │
│  └────────┬─────────┘   └─────────┬─────────┘                  │
│           │                       │                             │
│  ┌────────▼─────────┐   ┌─────────▼─────────┐                  │
│  │  Vector Store    │   │ Response Formatter │                  │
│  │  (Interface)     │   │                   │                  │
│  │  └ ChromaDB      │   │ - parse LLM output│                  │
│  │    (MVP)         │   │ - validate schema │                  │
│  └──────────────────┘   │ - fallback on err │                  │
│                         └─────────┬─────────┘                  │
│                                   │                             │
│                         ┌─────────▼─────────┐                  │
│                         │  Routing Engine   │                  │
│                         │                   │                  │
│                         │ - confidence check│                  │
│                         │ - intent detect   │                  │
│                         │ - escalate flag   │                  │
│                         └───────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### Project Directory Structure

```
travelbot-ai/
├── requirements.md
├── design.md
├── .env.example
├── pyproject.toml
│
├── app/
│   ├── main.py                  # FastAPI app factory, middleware, lifespan
│   ├── config.py                # Pydantic Settings — all env vars
│   │
│   ├── api/
│   │   ├── routers/
│   │   │   ├── chat.py          # POST /chat
│   │   │   ├── ingest.py        # POST /ingest, GET /ingest/{id}
│   │   │   └── health.py        # GET /health
│   │   └── dependencies.py      # Shared FastAPI deps (service injection)
│   │
│   ├── services/
│   │   ├── chat_service.py      # Orchestrates RAG → LLM → format → route
│   │   └── ingestion_service.py # Orchestrates parse → chunk → embed → store
│   │
│   ├── core/
│   │   ├── rag/
│   │   │   ├── retriever.py     # Semantic search against vector store
│   │   │   └── prompt_builder.py # Assembles system + context + user prompt
│   │   │
│   │   ├── llm/
│   │   │   ├── gateway.py       # LLMGateway interface (abstract base)
│   │   │   ├── claude_adapter.py
│   │   │   ├── openai_adapter.py
│   │   │   └── factory.py       # Returns correct adapter from config
│   │   │
│   │   ├── vector_store/
│   │   │   ├── base.py          # VectorStore interface (abstract base)
│   │   │   └── chroma.py        # ChromaDB implementation
│   │   │
│   │   ├── document/
│   │   │   ├── parser.py        # PDF + FAQ file → raw text
│   │   │   └── chunker.py       # Text → overlapping chunks
│   │   │
│   │   ├── formatter.py         # LLM output → ChatResponse schema
│   │   └── router.py            # Confidence + intent → escalate decision
│   │
│   └── models/
│       ├── chat.py              # ChatRequest, ChatResponse Pydantic models
│       └── ingest.py            # IngestRequest, IngestJob models
│
├── frontend/
│   └── index.html               # Self-contained web chat widget
│
└── tests/
    ├── unit/
    │   ├── test_retriever.py
    │   ├── test_formatter.py
    │   ├── test_router.py
    │   ├── test_chunker.py
    │   └── test_parser.py
    ├── integration/
    │   ├── test_chat_service.py
    │   └── test_ingestion_service.py
    └── e2e/
        └── test_api.py
```

---

## 3. Component Design

### 3.1 LLM Gateway (Pluggable Adapter)

**Interface contract** — all adapters must implement:

```python
class LLMGateway(ABC):
    @abstractmethod
    async def complete(self, prompt: str, system: str) -> str:
        """Send prompt, return raw text completion."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Return embedding vector for text."""
```

Active adapter is selected at startup via `LLM_PROVIDER` env var (`claude` | `openai` | `gemini`). No adapter-specific code exists outside `app/core/llm/`.

### 3.2 Vector Store (Abstraction)

**Interface contract:**

```python
class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, chunks: list[Chunk]) -> None:
        """Embed and store chunks."""

    @abstractmethod
    async def query(self, query_vector: list[float], top_n: int) -> list[SearchResult]:
        """Return top-N chunks by cosine similarity with score."""

    @abstractmethod
    async def delete_by_source(self, source_id: str) -> None:
        """Remove all chunks for a given document."""
```

`ChromaDB` is the MVP implementation. Migration to Pinecone or pgvector requires only a new class implementing this interface.

### 3.3 RAG Retriever

```
query_text
    │
    ▼
embed(query_text) → query_vector
    │
    ▼
vector_store.query(query_vector, top_n=5)
    │
    ▼
filter chunks where score >= SIMILARITY_THRESHOLD (default: 0.70)
    │
    ├── chunks found  → return chunks + max_score
    └── no chunks     → return empty + score=0.0
```

`SIMILARITY_THRESHOLD` and `TOP_N` are configurable via env vars.

### 3.4 Response Formatter

Parses LLM output (structured JSON instruction in system prompt) into `ChatResponse`. On parse failure, returns a safe fallback:

```python
FALLBACK_RESPONSE = ChatResponse(
    answer="I'm sorry, I couldn't process that. Please try again or speak to an agent.",
    booking_link=None,
    related_services=[],
    confidence="low",
    escalate=True,
)
```

### 3.5 Routing Engine

Escalation is triggered when **any** of these conditions is true:

| Condition | Check |
|-----------|-------|
| Low retrieval score | `max_similarity_score < CONFIDENCE_THRESHOLD` (default: 0.60) |
| Low LLM confidence | LLM self-reports `confidence: low` in output |
| Explicit human request | Query matches intent patterns: `speak to agent`, `human`, `representative`, `help me` |
| Formatter fallback fired | `formatter_used_fallback = True` |

### 3.6 Ingestion Service

```
file_upload
    │
    ▼
validate (type: pdf/txt/json, size ≤ 50MB)
    │
    ▼
create job_id, set status=pending
    │
    ▼ (async background task)
parse file → raw text
    │
    ▼
chunk text (size=512 tokens, overlap=50 tokens)
    │
    ▼
embed each chunk via LLM gateway
    │
    ▼
upsert to vector store with metadata { source_id, filename, chunk_index }
    │
    ▼
set status=completed (or failed + reason on error)
```

Ingestion runs as a **FastAPI BackgroundTask** — the `POST /ingest` endpoint returns `job_id` immediately with `status: pending`. Callers poll `GET /ingest/{job_id}` for status.

---

## 4. Data Models

### ChatRequest
```python
class ChatRequest(BaseModel):
    session_id: str          # UUID — client-generated, used for log correlation
    message: str             # 1–2000 characters
```

### ChatResponse
```python
class ChatResponse(BaseModel):
    answer: str
    booking_link: str | None
    related_services: list[str]   # max 3 items
    confidence: Literal["high", "medium", "low"]
    escalate: bool
    session_id: str
```

### IngestJob
```python
class IngestJob(BaseModel):
    job_id: str
    filename: str
    status: Literal["pending", "processing", "completed", "failed"]
    error: str | None          # populated on failure
    chunk_count: int | None    # populated on completion
    created_at: datetime
    updated_at: datetime
```

### Chunk (internal)
```python
class Chunk(BaseModel):
    id: str                    # UUID
    source_id: str             # parent document ID
    text: str
    embedding: list[float]
    metadata: dict             # filename, chunk_index, page_number (PDF)
```

### SearchResult (internal)
```python
class SearchResult(BaseModel):
    chunk: Chunk
    score: float               # cosine similarity 0.0–1.0
```

---

## 5. Sequence Diagrams

### 5.1 Happy Path — Chat Request (Answer Found)

```
Client          API Layer       ChatService     RAGRetriever    VectorStore     LLMGateway      Formatter       Router
  │                 │               │               │               │               │               │              │
  │─POST /chat─────►│               │               │               │               │               │              │
  │                 │─validate req──►               │               │               │               │              │
  │                 │               │               │               │               │               │              │
  │                 │───────────────►embed(message)─►               │               │               │              │
  │                 │               │               │─embed(msg)────────────────────►               │              │
  │                 │               │               │◄──────────────────────────────query_vector    │              │
  │                 │               │               │─query(vector)─►               │               │              │
  │                 │               │               │◄──────────────SearchResults   │               │              │
  │                 │               │               │               │               │               │              │
  │                 │               │◄──chunks+scores               │               │               │              │
  │                 │               │                               │               │               │              │
  │                 │               │─build_prompt(chunks+message)──────────────────►               │              │
  │                 │               │◄──────────────────────────────────────────────raw_text        │              │
  │                 │               │                               │               │               │              │
  │                 │               │───────────────────────────────────────────────►parse(raw_text)│              │
  │                 │               │◄───────────────────────────────────────────────ChatResponse   │              │
  │                 │               │                               │               │               │              │
  │                 │               │───────────────────────────────────────────────────────────────►route(resp)   │
  │                 │               │◄───────────────────────────────────────────────────────────────escalate=false│
  │                 │               │                               │               │               │              │
  │                 │◄──ChatResponse│               │               │               │               │              │
  │◄─200 JSON───────│               │               │               │               │               │              │
```

### 5.2 Escalation Path — Low Confidence

```
Client          API Layer       ChatService     RAGRetriever    VectorStore     LLMGateway      Formatter       Router
  │                 │               │               │               │               │               │              │
  │─POST /chat─────►│               │               │               │               │               │              │
  │                 │───────────────►               │               │               │               │              │
  │                 │               │─embed+query───►────────────────►               │               │              │
  │                 │               │◄──no results (score < 0.70)    │               │               │              │
  │                 │               │                               │               │               │              │
  │                 │               │─build_prompt (no context)─────────────────────►               │              │
  │                 │               │◄──────────────────────────────────────────────raw_text        │              │
  │                 │               │                               │               │               │              │
  │                 │               │───────────────────────────────────────────────►parse()        │              │
  │                 │               │◄───────────────────────────────────────────────ChatResponse(confidence=low)  │
  │                 │               │                               │               │               │              │
  │                 │               │───────────────────────────────────────────────────────────────►route()       │
  │                 │               │  score=0.0 < threshold AND confidence=low                      │◄─escalate=true
  │                 │               │◄────────────────────────────────────────────────────────────────             │
  │                 │               │                               │               │               │              │
  │                 │               │─log escalation event (session_id)             │               │              │
  │                 │               │                               │               │               │              │
  │                 │◄──ChatResponse(escalate=true, answer="Connecting you to an agent...")          │              │
  │◄─200 JSON───────│               │               │               │               │               │              │
```

### 5.3 Ingestion Flow

```
Admin           API Layer       IngestService   DocumentParser  Chunker         LLMGateway      VectorStore     JobStore
  │                 │               │               │               │               │               │              │
  │─POST /ingest───►│               │               │               │               │               │              │
  │                 │─validate file─►               │               │               │               │              │
  │                 │               │─create_job────────────────────────────────────────────────────────────────►  │
  │◄─202 {job_id}───│               │               │               │               │               │              │
  │                 │               │                                                               │              │
  │                 │       [BackgroundTask starts]  │               │               │               │              │
  │                 │               │─set status=processing──────────────────────────────────────────────────────► │
  │                 │               │─parse(file)───►               │               │               │              │
  │                 │               │◄──────────────raw_text        │               │               │              │
  │                 │               │─chunk(raw_text)────────────────►               │               │              │
  │                 │               │◄───────────────────────────────chunks[]        │               │              │
  │                 │               │                               │               │               │              │
  │                 │               │─embed(chunk) × N──────────────────────────────►               │              │
  │                 │               │◄──────────────────────────────────────────────vectors[]       │              │
  │                 │               │─upsert(chunks+vectors)────────────────────────────────────────►              │
  │                 │               │◄──────────────────────────────────────────────────────────────ok             │
  │                 │               │─set status=completed(chunk_count)──────────────────────────────────────────► │
  │                 │               │               │               │               │               │              │
  │─GET /ingest/{id}►               │               │               │               │               │              │
  │◄─{status: "completed", chunk_count: N}          │               │               │               │              │
```

---

## 6. Data Flow

### 6.1 Chat Request Data Flow

```
Input
──────
POST /chat
{
  "session_id": "abc-123",
  "message": "What is the baggage policy for Bali packages?"
}

Step 1 — Embedding
──────────────────
message → LLMGateway.embed() → [0.12, -0.45, 0.88, ...]   (1536-dim vector)

Step 2 — Retrieval
──────────────────
query_vector → VectorStore.query(top_n=5)
→ [
    SearchResult(chunk="Baggage allowance for...", score=0.91),
    SearchResult(chunk="Our Bali packages include...", score=0.87),
    SearchResult(chunk="Excess baggage fees...", score=0.72),
  ]

Step 3 — Context Filter
───────────────────────
Filter: score >= 0.70  →  all 3 pass
max_score = 0.91  →  above CONFIDENCE_THRESHOLD (0.60)  →  no escalation yet

Step 4 — Prompt Construction
─────────────────────────────
System prompt:
  "You are TravelBot AI... answer ONLY from context... respond as JSON: {answer, booking_link, related_services, confidence}"

Context:
  [Chunk 1 text] [Chunk 2 text] [Chunk 3 text]

User:
  "What is the baggage policy for Bali packages?"

Step 5 — LLM Completion
────────────────────────
LLMGateway.complete(prompt) →
  '{"answer": "...", "booking_link": "https://...", "related_services": [...], "confidence": "high"}'

Step 6 — Format & Route
────────────────────────
Formatter.parse() → ChatResponse(escalate=False, confidence="high", ...)

Output
──────
200 OK
{
  "answer": "Each Bali package includes 20kg checked baggage...",
  "booking_link": "https://agency.com/bali-packages",
  "related_services": ["Travel Insurance", "Airport Transfer"],
  "confidence": "high",
  "escalate": false,
  "session_id": "abc-123"
}
```

### 6.2 Ingestion Data Flow

```
Input
──────
POST /ingest  (multipart/form-data)
  file: bali_travel_guide.pdf  (2.4 MB)

Step 1 — Validation
────────────────────
type: application/pdf  ✓
size: 2.4 MB < 50 MB   ✓
job_id: "job-xyz-789" created, status=pending

Step 2 — Parse (Background)
────────────────────────────
PDF → LangChain PDFLoader → raw text (42 pages, ~28,000 tokens)

Step 3 — Chunk
──────────────
RecursiveCharacterTextSplitter(chunk_size=512, overlap=50)
→ 84 chunks

Step 4 — Embed
──────────────
embed(chunk_1) → vector_1
embed(chunk_2) → vector_2
... (84 calls, batched in groups of 20)

Step 5 — Store
──────────────
VectorStore.upsert([
  Chunk(id, source_id="job-xyz-789", text=chunk_1, embedding=vector_1, metadata={...}),
  ...
])

Output
──────
GET /ingest/job-xyz-789
{
  "job_id": "job-xyz-789",
  "filename": "bali_travel_guide.pdf",
  "status": "completed",
  "chunk_count": 84,
  "error": null,
  "created_at": "2026-03-12T10:00:00Z",
  "updated_at": "2026-03-12T10:00:47Z"
}
```

---

## 7. Error Handling Strategy

### 7.1 Error Classification

| Class | Examples | HTTP Status | Behavior |
|-------|----------|-------------|----------|
| **Validation Error** | Missing fields, oversized file, unsupported format | 422 | Reject immediately, return field-level error detail |
| **Bad Request** | Empty message, invalid session_id format | 400 | Reject, return descriptive message |
| **LLM Failure** | API timeout, rate limit, provider error | — | Retry up to 2× with exponential backoff, then fallback response |
| **Vector Store Failure** | ChromaDB write/read error | — | Log + escalate chat response; fail ingestion job with reason |
| **Formatter Parse Error** | LLM output not valid JSON | — | Return `FALLBACK_RESPONSE` with `escalate=true` |
| **Ingestion Parse Error** | Corrupt PDF, unreadable file | — | Set job `status=failed`, populate `error` field |
| **Unhandled Exception** | Any uncaught error | 500 | Log with request context, return generic 500 JSON (never expose stack trace) |

### 7.2 LLM Retry Policy

```
attempt 1 → wait 1s → attempt 2 → wait 2s → attempt 3
                                                 │
                                           still failed?
                                                 │
                                    return FALLBACK_RESPONSE
                                    escalate = true
                                    log: ERROR with session_id + prompt hash
```

### 7.3 Error Response Schema

All error responses follow a consistent shape:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": {}
  }
}
```

Error codes: `VALIDATION_ERROR`, `INVALID_FILE_TYPE`, `FILE_TOO_LARGE`, `LLM_UNAVAILABLE`, `INGESTION_FAILED`, `INTERNAL_ERROR`

### 7.4 Logging Contract

Every log entry includes:

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 |
| `level` | DEBUG / INFO / WARNING / ERROR |
| `session_id` | For chat requests |
| `job_id` | For ingestion requests |
| `component` | Which component logged (e.g., `rag.retriever`) |
| `message` | Human-readable description |
| `duration_ms` | For timed operations |
| `error` | Exception message (ERROR level only) |

No PII (user messages) is logged at WARNING/ERROR level. Full message content logged at DEBUG only (disabled by default).

---

## 8. Testing Strategy

### 8.1 Test Pyramid

```
          /\
         /E2E\         ← 5% — full API round-trips (real ChromaDB, mocked LLM)
        /──────\
       /        \
      /Integration\    ← 25% — service-level tests, real components wired together
     /──────────────\
    /                \
   /    Unit Tests    \  ← 70% — isolated component tests, all deps mocked
  /────────────────────\
```

### 8.2 Unit Tests

| Component | What's Tested | Mocks |
|-----------|--------------|-------|
| `rag/retriever.py` | Correct top-N returned, score filtering, empty result handling | VectorStore, LLMGateway |
| `rag/prompt_builder.py` | Prompt contains context chunks, system prompt present, truncation at token limit | — |
| `core/formatter.py` | Valid JSON → ChatResponse, malformed JSON → FALLBACK_RESPONSE, missing fields → fallback | — |
| `core/router.py` | Each escalation condition fires independently and in combination | — |
| `document/chunker.py` | Chunk sizes within limit, overlap applied, empty input handled | — |
| `document/parser.py` | PDF → text extraction, FAQ JSON → text, unsupported type raises | — |
| `llm/claude_adapter.py` | Correct API call shape, retry on 429, propagates errors after retries | `httpx` / `anthropic` SDK |

### 8.3 Integration Tests

| Test | Scope | External Services |
|------|-------|------------------|
| `test_chat_service.py` | Full RAG pipeline: retrieve → build prompt → LLM call → format → route | LLM mocked via fixture; real ChromaDB in-memory |
| `test_ingestion_service.py` | Upload → parse → chunk → embed → store → status=completed | LLM mocked for embeddings; real ChromaDB |
| `test_escalation_flow.py` | Low-score query → escalate=true in response | LLM mocked |

Integration tests use a **test knowledge base fixture** — a small pre-loaded ChromaDB with 10 known chunks about Bali packages — so retrieval results are deterministic.

### 8.4 End-to-End Tests

Run against the live FastAPI server with a real ChromaDB instance. LLM calls are intercepted by a **recorded fixture** (VCR cassette pattern) — no live LLM calls during CI.

| Test | Flow |
|------|------|
| `test_happy_path_chat` | Ingest test PDF → POST /chat with known question → assert structured response fields present |
| `test_escalation_e2e` | POST /chat with out-of-domain question → assert `escalate=true` |
| `test_ingest_and_poll` | POST /ingest → poll GET /ingest/{id} until completed → assert chunk_count > 0 |
| `test_invalid_file_type` | POST /ingest with `.exe` → assert 422 |
| `test_health` | GET /health → assert 200 |

### 8.5 Test Configuration

```
# Test environment variables (.env.test)
LLM_PROVIDER=claude
CLAUDE_API_KEY=test-key-not-used        # overridden by VCR fixture
VECTOR_STORE_BACKEND=chroma
CHROMA_PERSIST_DIR=:memory:             # in-memory for tests
CONFIDENCE_THRESHOLD=0.60
SIMILARITY_THRESHOLD=0.70
TOP_N_RESULTS=5
LOG_LEVEL=ERROR                         # suppress logs during test runs
```

### 8.6 CI Pipeline (MVP)

```
push / PR
    │
    ▼
lint (ruff)
    │
    ▼
type check (mypy)
    │
    ▼
unit tests (pytest -m unit)
    │
    ▼
integration tests (pytest -m integration)
    │
    ▼
e2e tests (pytest -m e2e)
    │
    ▼
✓ all pass → ready to merge
```

Coverage target: **≥ 80%** overall, **100%** on `formatter.py` and `router.py` (critical path, no untested branches).
