# TravelBot AI

RAG-powered chatbot MVP for travel agencies. Validates AI-powered customer support with a real knowledge base, structured responses, and human escalation.

## Features

- **Knowledge Base Ingestion** — Upload PDF, TXT, or FAQ JSON files
- **RAG Retrieval** — Semantic search over your knowledge base with ChromaDB
- **Structured Responses** — Consistent JSON schema with answer, booking link, related services
- **Human Escalation** — Automatic escalation on low confidence, explicit human requests, or parse failures
- **Pluggable LLM** — Switch between Claude and OpenAI via environment variable
- **Web Chat Widget** — Standalone HTML widget, no build tools required

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd travelbot-ai

# Copy environment file and fill in your API keys
cp .env.example .env
# Edit .env and set CLAUDE_API_KEY or OPENAI_API_KEY

# Install dependencies
uv sync

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

Interactive API docs: `http://localhost:8000/api/v1/docs`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `claude` | `claude` or `openai` |
| `CLAUDE_API_KEY` | — | Required if `LLM_PROVIDER=claude` |
| `OPENAI_API_KEY` | — | Required if `LLM_PROVIDER=openai` or for embeddings |
| `CHROMA_PERSIST_DIR` | `./data/chroma` | ChromaDB storage path. Use `:memory:` for tests |
| `CONFIDENCE_THRESHOLD` | `0.60` | Escalation trigger: score below this escalates |
| `SIMILARITY_THRESHOLD` | `0.70` | Retrieval: minimum similarity score |
| `TOP_N_RESULTS` | `5` | Number of chunks to retrieve |
| `MAX_FILE_SIZE_MB` | `50` | Maximum upload file size |

## API Reference

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Response:
```json
{"status": "ok", "version": "0.1.0"}
```

### Chat

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "my-session-id",
    "message": "What are your refund policies?"
  }'
```

Response:
```json
{
  "answer": "Our refund policy allows full refunds within 24 hours of booking.",
  "booking_link": null,
  "related_services": ["Flight Booking", "Hotel Reservations"],
  "confidence": "high",
  "escalate": false,
  "session_id": "my-session-id"
}
```

When `escalate` is `true`, the user should be connected to a human agent.

### Ingest a File

```bash
# Upload a PDF
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@/path/to/travel-guide.pdf"

# Upload a FAQ JSON file
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@/path/to/faq.json"

# Upload a text file
curl -X POST http://localhost:8000/api/v1/ingest \
  -F "file=@/path/to/knowledge-base.txt"
```

Response (202 Accepted):
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "travel-guide.pdf",
  "status": "pending",
  "error": null,
  "chunk_count": null,
  "created_at": "2026-03-12T10:00:00",
  "updated_at": "2026-03-12T10:00:00"
}
```

### Poll Ingestion Status

```bash
curl http://localhost:8000/api/v1/ingest/550e8400-e29b-41d4-a716-446655440000
```

Response when complete:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "travel-guide.pdf",
  "status": "completed",
  "error": null,
  "chunk_count": 42,
  "created_at": "2026-03-12T10:00:00",
  "updated_at": "2026-03-12T10:00:05"
}
```

Status values: `pending` → `processing` → `completed` | `failed`

### FAQ JSON Format

```json
[
  {
    "question": "What is your refund policy?",
    "answer": "Full refund within 24 hours of booking."
  },
  {
    "question": "How do I book a group tour?",
    "answer": "Contact our sales team for groups of 10 or more."
  }
]
```

## Web Chat Widget

Open `frontend/index.html` directly in a browser (no server needed):

```bash
open frontend/index.html
```

The widget connects to `http://localhost:8000/api/v1` by default. To change the API URL, edit the `API_BASE` constant near the top of the `<script>` block in `frontend/index.html`.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run by marker
pytest -m unit
pytest -m integration
pytest -m e2e

# Run a specific file
pytest tests/unit/test_formatter.py -v

# Run a specific test
pytest tests/unit/test_formatter.py::TestResponseFormatter::test_valid_json_returns_chat_response -v
```

## OpenAPI Specification

After starting the server, the auto-generated OpenAPI spec is available at:

- **Swagger UI**: `http://localhost:8000/api/v1/docs`
- **JSON spec**: `http://localhost:8000/api/v1/openapi.json`

To export the spec:

```bash
curl http://localhost:8000/api/v1/openapi.json > openapi.json
```

## Architecture

```
API Layer (FastAPI routers)
    ↓
Service Layer (ChatService, IngestionService)
    ↓
Core Engine (RAGRetriever, PromptBuilder, ResponseFormatter, RoutingEngine)
    ↓
Infrastructure (ChromaVectorStore, ClaudeAdapter / OpenAIAdapter)
```

- **Pluggable LLM**: swap providers by changing `LLM_PROVIDER` in `.env`
- **Pluggable vector store**: `VectorStore` abstract base; implement for any backend
- **Stateless API**: `session_id` is client-generated, used only for log correlation
- **Async ingestion**: `POST /ingest` returns `202` immediately; poll `GET /ingest/{job_id}`
- **Formatter never raises**: always returns a safe fallback with `escalate=true` on failures

## Project Structure

```
app/
  api/
    routers/       # health.py, chat.py, ingest.py
    dependencies.py
  core/
    document/      # parser.py, chunker.py
    llm/           # gateway.py, claude_adapter.py, openai_adapter.py, factory.py
    rag/           # retriever.py, prompt_builder.py
    vector_store/  # base.py, chroma.py
    formatter.py
    models.py
    router.py
  models/          # chat.py, ingest.py (Pydantic schemas)
  services/        # chat_service.py, ingestion_service.py
  config.py
  main.py
frontend/
  index.html       # Self-contained chat widget
tests/
  unit/
  integration/
  e2e/
  conftest.py
```
