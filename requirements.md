# TravelBot AI — Requirements

## MVP Scope

Validate core RAG-powered chatbot functionality and demonstrate end-to-end customer support flow — from question intake to structured answer to human handoff — via a web interface backed by a real knowledge base.

---

## Feature Areas

1. [Knowledge Base Ingestion](#1-knowledge-base-ingestion)
2. [RAG Retrieval & Response Generation](#2-rag-retrieval--response-generation)
3. [Structured Response Formatting](#3-structured-response-formatting)
4. [Human Handoff / Escalation](#4-human-handoff--escalation)
5. [Web Chat Widget](#5-web-chat-widget)
6. [REST API](#6-rest-api)

---

## 1. Knowledge Base Ingestion

### User Stories

**US-1.1** — As an admin, I want to upload PDF documents to the knowledge base so that the bot can answer questions grounded in agency-specific content.

**US-1.2** — As an admin, I want to upload FAQ files (plain text or structured format) so that common questions are answered accurately without manual entry.

**US-1.3** — As an admin, I want to see the ingestion status of uploaded files so that I know when the content is available to the bot.

### Acceptance Criteria

| ID | Criteria |
|----|----------|
| AC-1.1 | System accepts PDF uploads up to 50 MB per file |
| AC-1.2 | System accepts FAQ uploads in `.txt` or `.json` format |
| AC-1.3 | Uploaded documents are chunked, embedded, and stored in the vector store |
| AC-1.4 | Ingestion status is returned (`pending`, `processing`, `completed`, `failed`) |
| AC-1.5 | Failed ingestions surface an error message with a reason |
| AC-1.6 | Duplicate file uploads are detected and skipped or replaced (configurable) |

---

## 2. RAG Retrieval & Response Generation

### User Stories

**US-2.1** — As a customer, I want to ask a travel-related question and receive an answer grounded in the agency's actual content, not a generic reply.

**US-2.2** — As a customer, I want the bot to find the most relevant information even if my phrasing doesn't exactly match the source document.

**US-2.3** — As a developer, I want the LLM gateway to be pluggable so that the underlying model (Claude, GPT-4, Gemini) can be swapped without changing business logic.

### Acceptance Criteria

| ID | Criteria |
|----|----------|
| AC-2.1 | System retrieves the top-N most semantically relevant chunks from the vector store for each query |
| AC-2.2 | Retrieved chunks are injected into the LLM prompt as context |
| AC-2.3 | Response is generated only from retrieved context — not from model's general knowledge when context is available |
| AC-2.4 | LLM provider is configurable via environment variable or config file |
| AC-2.5 | If no relevant context is found (similarity below threshold), the system flags the query rather than hallucinating |
| AC-2.6 | End-to-end response latency is under 5 seconds for 95% of queries under normal load |

---

## 3. Structured Response Formatting

### User Stories

**US-3.1** — As a customer, I want every bot response to include a direct answer, a relevant booking link, and related service suggestions so that I can act on the information immediately.

**US-3.2** — As a developer, I want the API to return a consistent response schema so that the frontend and future SDK integrations can reliably parse and render responses.

### Acceptance Criteria

| ID | Criteria |
|----|----------|
| AC-3.1 | Every bot response includes three fields: `answer`, `booking_link`, `related_services` |
| AC-3.2 | `answer` is a plain-language reply to the customer's question |
| AC-3.3 | `booking_link` is contextually surfaced from the knowledge base when applicable; `null` otherwise |
| AC-3.4 | `related_services` is an array of 0–3 relevant service suggestions |
| AC-3.5 | Response schema is documented and versioned |
| AC-3.6 | Malformed or incomplete LLM output is caught and a fallback structured response is returned |

**Response Schema (v1):**
```json
{
  "answer": "string",
  "booking_link": "string | null",
  "related_services": ["string"],
  "confidence": "high | medium | low",
  "escalate": false
}
```

---

## 4. Human Handoff / Escalation

### User Stories

**US-4.1** — As a customer, I want the bot to recognize when it can't confidently answer my question and connect me to a human agent instead of giving me a wrong answer.

**US-4.2** — As a travel agent, I want to receive escalated conversations with context (the customer's question and the bot's attempted answer) so that I can continue without asking the customer to repeat themselves.

**US-4.3** — As an admin, I want to configure the confidence threshold that triggers escalation so that I can tune the bot's autonomy for our use case.

### Acceptance Criteria

| ID | Criteria |
|----|----------|
| AC-4.1 | Queries with confidence below the configured threshold set `escalate: true` in the response |
| AC-4.2 | Escalated responses include the original query, retrieved context (if any), and bot's attempted answer |
| AC-4.3 | Confidence threshold is configurable (default: `0.6` on a 0–1 scale) |
| AC-4.4 | Escalation trigger is also fired when the query explicitly requests a human (e.g., "speak to an agent") |
| AC-4.5 | Escalated sessions are logged with a unique session ID for agent pickup |
| AC-4.6 | The bot informs the customer that their query has been escalated and sets response time expectations |

---

## 5. Web Chat Widget

### User Stories

**US-5.1** — As a stakeholder, I want to interact with TravelBot AI through a web interface so that I can experience the end-to-end demo without any integration setup.

**US-5.2** — As a customer (demo), I want to type a question and see a formatted response in real time so that the interaction feels natural and usable.

**US-5.3** — As a demo viewer, I want to see escalation in action — where the bot hands off to a human — so that I understand the full support flow.

### Acceptance Criteria

| ID | Criteria |
|----|----------|
| AC-5.1 | Chat widget renders in a modern browser (Chrome, Firefox, Safari — latest 2 versions) |
| AC-5.2 | Widget displays conversation history in a scrollable thread |
| AC-5.3 | Structured response fields (`answer`, `booking_link`, `related_services`) are rendered distinctly in the UI |
| AC-5.4 | Escalation state is visually indicated (e.g., "Connecting you to an agent...") |
| AC-5.5 | Widget sends user message to the REST API and displays the response within the latency SLA |
| AC-5.6 | Empty or error states are handled gracefully with user-facing messages |
| AC-5.7 | Widget is responsive and usable on desktop and tablet screen sizes |

---

## 6. REST API

### User Stories

**US-6.1** — As a developer, I want a single REST API endpoint to send a customer message and receive a structured response so that any frontend or integration can use TravelBot AI without bespoke logic.

**US-6.2** — As a developer, I want the API to be stateless so that it can scale horizontally without session affinity concerns.

**US-6.3** — As a developer, I want clear API documentation so that I can integrate without requiring support from the TravelBot team.

### Acceptance Criteria

| ID | Criteria |
|----|----------|
| AC-6.1 | `POST /chat` accepts `{ "session_id": "string", "message": "string" }` |
| AC-6.2 | `POST /chat` returns the structured response schema (see AC-3.1) |
| AC-6.3 | API returns appropriate HTTP status codes: `200` success, `400` bad request, `422` validation error, `500` internal error |
| AC-6.4 | API is stateless — no server-side session state required between calls |
| AC-6.5 | `POST /ingest` accepts file uploads and returns ingestion status |
| AC-6.6 | `GET /health` returns service health status |
| AC-6.7 | All endpoints return JSON |
| AC-6.8 | API is documented via OpenAPI 3.0 spec |

**Core Endpoints (MVP):**

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send a message, receive a structured bot response |
| `POST` | `/ingest` | Upload a PDF or FAQ file to the knowledge base |
| `GET` | `/ingest/{job_id}` | Get ingestion job status |
| `GET` | `/health` | Service health check |

---

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-1 | Response latency p95 ≤ 5 seconds |
| NFR-2 | API is horizontally scalable (stateless design) |
| NFR-3 | LLM provider is swappable via config — no code changes required |
| NFR-4 | Vector store is abstracted behind an interface to allow backend migration |
| NFR-5 | All API inputs are validated before processing |
| NFR-6 | Secrets (API keys, DB credentials) are managed via environment variables, never hardcoded |
| NFR-7 | Ingestion and chat errors are logged with enough context to debug |

---

## Out of Scope (Post-MVP)

- White-label UI customization
- JavaScript SDK / iFrame embed
- Traveloka / Tiket.com platform integrations
- Multi-tenant knowledge base support (per-platform KB isolation)
- Analytics and conversation dashboard
- Native mobile SDK
- SLA monitoring and alerting
