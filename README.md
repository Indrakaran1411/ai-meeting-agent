# Meeting Intelligence Agent

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%7C%20pgvector-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, production-ready AI Meeting and Channel Intelligence Agent designed to ingest meeting audio files, extract transcriptions, perform structured AI analysis (extracting summaries, action items, decisions, and risks), and classify chat channel signals for actionable corporate intelligence.

---

## 1. Project Overview

The **Meeting Intelligence Agent** solves the challenge of corporate knowledge loss and administrative overhead by automating the ingestion of meeting recordings and chat communications, transforming raw audio into structured, queryable knowledge.

### High-Level Workflow
1. **Ingest & Validate**: Receives audio uploads (MP3, WAV, M4A) via a FastAPI REST endpoint with mandatory privacy consent checks.
2. **Queue**: Streams audio to local storage and enqueues a Celery task in a Redis broker.
3. **Speech-to-Text**: The Celery worker transcribes audio using a thread-safe `faster-whisper` model.
4. **AI Insight Extraction**: Transcripts are analyzed using `gemini-2.5-flash` with JSON schema enforcement to extract high-level summaries, action items, decisions, and risks.
5. **Deduplicated Sync**: Dispatches meeting data to configured PM tool webhooks using deterministic SHA-256 hashing to guarantee single-delivery semantics.
6. **Query & Retrieve**: Exposes insights through a REST API and a Model Context Protocol (MCP) server for direct LLM client consumption.

---

## 2. Features

* **Meeting Ingestion**: Streamlined multipart uploading of audio files up to 100MB with mandatory consent validation.
* **Speech-to-Text Pipeline**: Decoupled transcription worker using the `faster-whisper` library with Voice Activity Detection (VAD) filtering.
* **AI Meeting Analysis**: Google Gemini SDK integration using `gemini-2.5-flash` with strict SDK-level JSON schema validation.
* **Action Item Extraction**: Captures description, assignee, due date, and verbatim transcript quotes.
* **Decision Extraction**: Captures decision description, rationale, and verbatim transcript quotes.
* **Risk Extraction**: Captures description, severity level (`low`, `medium`, `high`, `critical`), verbatim quotes, and mitigation strategies.
* **Chat Signals**: Classifies external Slack/Teams channel messages into actionable categories (`blocker`, `decision`, `risk`, `general`) with confidence scores.
* **PostgreSQL + pgvector**: Relationally indexes all meetings, segments, and insights. Includes compound indices to support fast lookups.
* **Redis + Celery**: Resilient background processing with automatic retries, late acknowledgements (`acks_late=True`), and exponential backoff + jitter.
* **Webhook Integration**: PM sync endpoint utilizing deterministic payload SHA-256 hashing for idempotency protection, with complete audit logs tracking webhook responses and network faults.
* **MCP Server**: Stdio-based Node.js Model Context Protocol (MCP) server connecting directly to PostgreSQL, allowing AI agents to query corporate meeting history and search transcripts.
* **Docker Support**: Decoupled, multi-container architecture for database, queue, api, and worker with automated health checks.
* **Swagger API**: Auto-generated interactive API documentation at `/docs` with detailed schema examples.
* **Background Processing**: Heavy-duty transcription and LLM inference offloaded asynchronously to worker threads.

---

## 3. System Architecture

### Core System Workflow
```text
Client
  │ (Multipart Form Upload / audio_file + consent)
  ▼
FastAPI Backend (API Router)
  │
  ├─► PostgreSQL Database ──► [Persist Meeting (PENDING)]
  │
  │ (Enqueue process_meeting Task)
  ▼
Redis Broker
  │
  │ (Dispatch Task)
  ▼
Celery Worker
  │
  ├─► Faster-Whisper ──► [Speech-to-Text Transcription]
  │
  ├─► Google Gemini API (google-genai) ──► [Structured Insight Extraction]
  │
  ├─► PostgreSQL Database ──► [Save Summary, Action Items, Decisions, Risks, Status=COMPLETED]
  │
  └─► Webhook Dispatcher ──► [POST to PM Webhook URL (Idempotent check via SyncLogs)]
```

### Model Context Protocol (MCP) Workflow
```text
MCP Inspector / Client (Cursor, Claude Desktop)
  │ (JSON-RPC over Stdio)
  ▼
MCP Server (Node.js)
  │ (pg connection pool)
  ▼
PostgreSQL Database
```

---

## 4. Technology Stack

* **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic v2 (Settings v2), SQLAlchemy 2.0 (Async), Alembic, Faster-Whisper, Google GenAI SDK (`google-genai`)
* **Database**: PostgreSQL 16 (with `pgvector` extension), Node-postgres (`pg`) for the MCP server
* **Queue / Broker**: Redis 7, Celery 5.3
* **AI**: Google Gemini (`gemini-2.5-flash` model for structured extraction)
* **Infrastructure**: Docker, Docker Compose, Docker Volumes
* **Dev Tools**: `@modelcontextprotocol/sdk` (Node.js), MCP Inspector, HTTPX Mocking

---

## 5. Project Structure

```text
meeting_agent/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── infrastructure.py   # Health and readiness endpoints
│   │   │   │   └── meetings.py         # Meeting uploads, lists, updates, deletes, and syncs
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py              # Environment configuration & Settings validation
│   │   │   ├── exceptions.py          # Unified exception handling and JSON envelopes
│   │   │   └── logging_config.py      # Structured logs & request correlation middleware
│   │   ├── db/
│   │   │   ├── base.py                # SQLAlchemy declarative base
│   │   │   └── database.py            # Async engine and session configuration
│   │   ├── models/
│   │   │   ├── action_item.py         # Action item ORM model
│   │   │   ├── chat_signal.py         # Classified chat signal ORM model
│   │   │   ├── decision.py            # Decision ORM model
│   │   │   ├── enums.py               # Shared DB enums (status, severity, signal types)
│   │   │   ├── meeting.py             # Main meeting metadata ORM model
│   │   │   ├── risk.py                # Risk ORM model
│   │   │   ├── sync_log.py            # Outbound webhook sync logging & idempotency
│   │   │   ├── transcript.py          # Transcription segments ORM model
│   │   │   └── __init__.py
│   │   ├── prompts/
│   │   │   ├── meeting_analysis.py    # Structured extraction system instructions
│   │   │   └── __init__.py
│   │   ├── schemas/
│   │   │   ├── meeting.py             # Meeting schemas, update schemas, API DTOs
│   │   │   ├── meeting_analysis.py    # Structured extraction Pydantic schemas
│   │   │   ├── sync.py                # Outbound PM tool sync validation schemas
│   │   │   └── __init__.py
│   │   ├── services/
│   │   │   ├── ai_service.py          # Google Gemini SDK connection wrapper
│   │   │   ├── meeting_analysis_service.py # Prompt loading and pipeline analysis
│   │   │   ├── meeting_service.py     # Database writes, paginations, updates, and deletes
│   │   │   ├── storage_service.py     # Multipart disk streamer & MIME constraints
│   │   │   ├── sync_log_service.py    # Hashing, idempotency checks, and sync auditing
│   │   │   ├── sync_service.py        # Mapping ORM items to sync payload DTOs
│   │   │   ├── transcription_service.py # Faster-Whisper audio transcription model
│   │   │   └── webhook_service.py     # outbound webhook sender with socket pooling
│   │   │   └── __init__.py
│   │   └── workers/
│   │       ├── celery_app.py          # Celery configuration
│   │       ├── tasks.py               # Background execution worker tasks
│   │       └── __init__.py
│   │   ├── main.py                    # FastAPI entrypoint
│   │   └── __init__.py
│   ├── alembic/                       # Database schema version migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── alembic.ini                    # Alembic Config
│   ├── Dockerfile                     # API and Worker Dockerfile
│   └── requirements.txt               # App dependencies
├── mcp-server/                        # Model Context Protocol workspace
│   ├── database.js                    # PostgreSQL connection pool singleton
│   ├── server.js                      # Stdio transport registration and execution router
│   ├── package.json                   # Node dependencies and starts script
│   ├── package-lock.json
│   └── tools/
│       ├── list_meetings.js           # list_meetings tool query code
│       └── search_transcripts.js      # search_transcripts tool ILIKE code
├── docker-compose.yml                 # Orchestration definition for the stack
├── .env.example                       # Environment template
├── CHANGELOG.md                       # Historical log of commits and milestones
└── CONTRIBUTING.md                    # Guidelines on code style and PR submissions
```

---

## 6. Installation

### Prerequisites
- [Docker & Docker Compose](https://www.docker.com/)
- [Node.js (v18+)](https://nodejs.org/)
- [Python 3.11+](https://www.python.org/)

### 1. Clone the Repository
```bash
git clone https://github.com/Indrakaran1411/ai-meeting-agent.git
cd ai-meeting-agent
```

### 2. Configure Environment Variables
Copy the template and fill in your keys:
```bash
cp .env.example .env
```
Open `.env` and configure at minimum:
* `GEMINI_API_KEY`: Google Gemini Key for extraction.
* `DATABASE_URL`: Set to local or containerized Postgres host (see next sections).

---

## 7. Environment Variables

Below are the variables supported by the `.env` file configuration:

| Variable Name | Description | Example Placeholder |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/dbname` |
| `DB_POOL_SIZE` | Database connection pool size | `10` |
| `DB_MAX_OVERFLOW` | Extra connections allowed beyond pool size | `20` |
| `DB_POOL_TIMEOUT` | Seconds to wait before timing out a connection | `30` |
| `DB_POOL_RECYCLE` | Recycle connection threshold in seconds | `1800` |
| `DB_POOL_PRE_PING` | Verify connection health on checkout | `True` |
| `REDIS_URL` | Redis URL for Celery broker | `redis://host:6379/0` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSyYourGeminiApiKeyHere` |
| `GEMINI_MODEL` | Gemini model name to use | `gemini-2.5-flash` |
| `GEMINI_TEMPERATURE` | Temperature for Gemini generation | `0.2` |
| `GEMINI_MAX_OUTPUT_TOKENS` | Max tokens output limit | `4096` |
| `CLAUDE_API_KEY` | Optional Anthropic key | `sk-ant-xxx` |
| `UPLOAD_DIRECTORY` | Location to store meeting recordings | `uploads/meetings` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `WHISPER_MODEL_SIZE` | Faster-whisper model type | `base` |
| `WHISPER_DEVICE` | Hardware device for STT inference | `cpu` |
| `WHISPER_COMPUTE_TYPE` | Inference precision quantization | `int8` |
| `WHISPER_BEAM_SIZE` | Decoding beam size | `5` |
| `WHISPER_LANGUAGE` | Default language for STT (null for auto) | `en` |
| `WHISPER_VAD_FILTER` | Enable Voice Activity Detection | `true` |
| `PM_WEBHOOK_URL` | Downstream PM Webhook endpoint URL | `https://api.pm-tool.com/webhooks/meetings` |

---

## 8. Running with Docker Compose

Running the entire ecosystem inside Docker Compose is the recommended path for development and testing.

### Start the Stack
Spins up Postgres, Redis, the FastAPI Backend, and the Celery Worker:
```bash
docker compose up -d --build
```

### Check Container Status
Verify that all four containers are running and healthy:
```bash
docker compose ps
```

### Inspect Logs
To tail logs for all services or target specific ones:
```bash
# All logs
docker compose logs -f

# Worker logs only
docker compose logs worker -f

# Backend API logs only
docker compose logs backend -f
```

### Stop the Stack
Stops services and preserves database volume data:
```bash
docker compose down
```

To wipe the database volumes:
```bash
docker compose down -v
```

---

## 9. Running Backend Locally

If you want to run the backend without Docker (e.g., for local profiling or debugging):

### 1. Create a Python Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up Local Environment Variables
Ensure your `.env` is loaded or set in your session. Point `DATABASE_URL` and `REDIS_URL` to your local database/Redis instances:
```bash
export DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/meeting_agent"
export REDIS_URL="redis://localhost:6379/0"
export GEMINI_API_KEY="your-api-key"
```

### 4. Run Database Migrations
Use Alembic to upgrade the database schema:
```bash
alembic upgrade head
```

### 5. Run FastAPI Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Run Celery Worker
In a separate terminal (with the virtual environment activated):
```bash
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

---

## 10. Swagger API

The backend API automatically generates interactive Swagger documentation using FastAPI.

* **Documentation URL**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **OpenAPI Spec URL**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Important Endpoints

#### Meetings & Uploads
* `POST /api/v1/meetings/upload`: Upload recording (requires title, audio file, and `consent_given=True` form fields).
* `GET /api/v1/meetings`: Paginated list of meetings.
* `GET /api/v1/meetings/search`: Text search filtering titles/summaries.
* `GET /api/v1/meetings/{id}`: Detailed metadata and summary.
* `GET /api/v1/meetings/{id}/summary`: Clean high-level summary paragraph.

#### Extracted Insights
* `GET /api/v1/meetings/{id}/action-items`: Extracted action items.
* `GET /api/v1/meetings/{id}/decisions`: Extracted decisions.
* `GET /api/v1/meetings/{id}/risks`: Extracted risks.
* `PATCH /api/v1/action-items/{id}`: Partially update status/assignee/due_date for action items.
* `PATCH /api/v1/decisions/{id}`: Update descriptions/rationale for decisions.
* `PATCH /api/v1/risks/{id}`: Update severity/mitigations for risks.
* `DELETE /api/v1/action-items/{id}` / `DELETE /api/v1/decisions/{id}` / `DELETE /api/v1/risks/{id}`: Hard delete insights.

#### Statistics & Dashboard
* `GET /api/v1/meetings/stats`: Aggregated status counts and insight numbers.
* `GET /api/v1/dashboard`: Composite dashboard data (statistics + 5 recent meetings + 5 draft action items).

#### Integration Sync
* `POST /api/v1/meetings/{id}/sync`: Dispatches a formatted sync payload to the PM Webhook. Checks `sync_logs` for payload duplicate hashes to prevent double dispatch.

#### Operations
* `GET /health`: Basic operational uptime.
* `GET /ready`: Health check verifying active connections to PostgreSQL and Redis.

---

## 11. MCP Server

### What is MCP?
The **Model Context Protocol (MCP)** is an open standard that enables LLM applications (like Cursor, Claude Desktop, or custom agent systems) to securely interact with database servers, filesystem directories, and local tools.

### Why is it used here?
It acts as a secure, real-time read-only bridge between AI clients and the `meeting_agent` database. Rather than building custom database connectors, AI clients use the standard JSON-RPC over stdio interface provided by this MCP server to read meeting summaries or locate transcript contexts.

### Available Tools

1. `list_meetings`
   - **Description**: Lists meetings from the database with pagination and status filtering.
   - **Arguments**:
     * `limit` (integer, default: `10`, max: `100`): Max records to retrieve.
     * `offset` (integer, default: `0`): Pagination offset.
     * `status` (string, options: `pending`, `processing`, `completed`, `failed`): Filter by processing state.
2. `search_transcripts`
   - **Description**: Searches transcript segments using case-insensitive keyword queries. Returns matching segments formatted for LLM consumption.
   - **Arguments**:
     * `query` (string, **required**): Term to locate in transcripts.
     * `limit` (integer, default: `10`): Max segment results.

### Launching the MCP Inspector

The MCP Inspector is a visual developer console for testing tools. To launch it locally, connect it to your database using the `DATABASE_URL` environment variable:

```bash
cd mcp-server
npm install

# Run the Inspector pointing to your local PostgreSQL instance
DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/meeting_agent" npx @modelcontextprotocol/inspector node server.js
```
The inspector interface will open in your browser, enabling you to test tool registration and execution.

---

## 12. Example MCP Usage

Below are examples of JSON-RPC payloads exchanged with the MCP server over standard input/output.

### Tool: `list_meetings`

#### Request Payload
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "list_meetings",
    "arguments": {
      "limit": 2,
      "status": "completed"
    }
  },
  "id": 1
}
```

#### Response Content
```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"meetings\": [\n    {\n      \"id\": \"d3b07384-d113-4c5b-90f7-ebf4709cc5b1\",\n      \"title\": \"Q2 Product Roadmap Alignment\",\n      \"meeting_date\": \"2026-06-30T09:00:00.000Z\",\n      \"duration_minutes\": 45,\n      \"source\": \"Zoom\",\n      \"status\": \"COMPLETED\",\n      \"summary\": \"Aligned on Q2 key roadmap dates. Confirmed Whisper integration timeline.\",\n      \"created_at\": \"2026-06-30T09:10:00.000Z\"\n    }\n  ]\n}"
      }
    ]
  },
  "id": 1
}
```

---

### Tool: `search_transcripts`

#### Request Payload
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "search_transcripts",
    "arguments": {
      "query": "whisper",
      "limit": 1
    }
  },
  "id": 2
}
```

#### Response Content
```json
{
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Meeting: Q2 Product Roadmap Alignment (ID: d3b07384-d113-4c5b-90f7-ebf4709cc5b1)\nSpeaker: John Doe\nTimestamp: 120s - 145s\nTranscript: We need to make sure the whisper transcription service is configured with a proper VAD filter to bypass background white noise."
      }
    ]
  },
  "id": 2
}
```

---

## 13. AI Processing Pipeline

The ingestion and insight extraction pipeline consists of the following phases:

```text
Upload Audio File (Consent Verified)
  │
  ▼
Segment Transcription (Faster-Whisper)
  │
  ▼
Assemble Full Transcript Text
  │
  ▼
Gemini LLM Processing (System Prompt + Structured MIME Schema)
  │
  ├─► Summarization ──────► High-Level Executive Summary
  │
  ├─► Action Items ───────► Tasks + Assignee + Due Date + Quotes
  │
  ├─► Decisions ──────────► Decision Details + Rationale + Quotes
  │
  ├─► Risks ──────────────► Severity + Risk Details + Mitigations + Quotes
  │
  └─► Chat Signals ───────► Message Classifications + Confidence Scores
      │
      ▼
Atomic Write to PostgreSQL Database
```

* **SDK Schema Enforcement**: Using the `google-genai` SDK, Pydantic validation is performed at the model inference layer (`response_schema=MeetingAnalysis`). If the LLM generates output that does not match the schema, it fails prior to database insertion.
* **Idempotency Safeguard**: Every time the processing task is triggered, it checks for existing transcript entries in the database. If present, it aborts immediately, preventing duplicate speech-to-text inference or extra LLM calls.

---

## 14. Background Processing

Asynchronous background execution is handled by **Celery** using a **Redis** message broker.

```text
[FastAPI Process] ────► [Redis Task Queue] ────► [Celery Worker Pool]
  Upload File            Enqueues task            Invokes transcription
  Returns HTTP 202       with meeting_id          and Gemini analysis
```

### Safety Features
1. **Late Acknowledgements (`acks_late=True`)**: Tasks are only acknowledged *after* successful database commit. If a worker container crashes midway, the broker automatically re-queues the task.
2. **Worker Loss Rejection (`task_reject_on_worker_lost=True`)**: Rejects and re-enqueues tasks if a worker process is terminated abruptly (e.g., out-of-memory).
3. **Thread-Local Event Loops**: Reuses the event loop inside the worker's synchronous task thread via a helper (`get_event_loop()`) to prevent SQLAlchemy connection pool collisions.
4. **Exponential Backoff and Jitter**: Tasks retry automatically on transient network or API rate limit failures, following an exponential backoff schedule to prevent overloading downstreams.

---

## 15. Database Design

The schema is built on a PostgreSQL database utilizing the `pgvector` extension. Below are the core tables and relationships:

```text
                       ┌─────────────────────────┐
                       │        meetings         │
                       └───────────┬─────────────┘
                                   │
         ┌─────────────┬───────────┼───────────┬─────────────┐
         │ (1:N)       │ (1:N)     │ (1:N)     │ (1:N)       │ (1:N)
         ▼             ▼           ▼           ▼             ▼
  ┌────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐
  │transcripts │ │action_it.│ │decisions │ │  risks   │ │ sync_logs  │
  └────────────┘ └──────────┘ └──────────┘ └──────────┘ └────────────┘
```

* **`meetings`**: Master metadata record storing title, date, duration, source, consent status, processing status (`pending`, `processing`, `completed`, `failed`), file path, and the AI-generated high-level summary.
* **`transcripts`**: Storing individual speaker segments with order index (`segment_index`), speaker identification, content text, start times, and end times.
* **`action_items`**: Extracted action items with their review state (`draft`, `approved`, `synced`), target assignee, due date, description, and verbatim transcript quote.
* **`decisions`**: Decisions made, detailing description, rationale, verbatim quote, and status.
* **`risks`**: Captured risks storing severity classification (`low`, `medium`, `high`, `critical`), description, mitigation strategy, verbatim quote, and status.
* **`chat_signals`**: Classified chat messages tracking origin platform, sender, content, signal type (`blocker`, `decision`, `risk`, `general`), and classification confidence score.
* **`sync_logs`**: Outbound audit trail logs containing `payload_hash` and status (`pending`, `success`, `failed`) to handle webhook idempotency and network diagnostics.

---

## 16. API Workflow

Here is an end-to-end payload workflow:

### 1. Register and Upload audio
```bash
curl -X POST "http://localhost:8000/api/v1/meetings/upload" \
  -F "title=Weekly Sync" \
  -F "consent_given=true" \
  -F "source=Zoom" \
  -F "audio_file=@recording.mp3"
```
**Response (HTTP 202 Accepted)**:
```json
{
  "meeting_id": "d3b07384-d113-4c5b-90f7-ebf4709cc5b1",
  "status": "pending",
  "message": "Meeting registered successfully and is pending processing."
}
```

### 2. Check Pipeline Progress
```bash
curl -X GET "http://localhost:8000/api/v1/meetings/d3b07384-d113-4c5b-90f7-ebf4709cc5b1"
```
**Response (HTTP 200 OK - After processing completes)**:
```json
{
  "id": "d3b07384-d113-4c5b-90f7-ebf4709cc5b1",
  "title": "Weekly Sync",
  "status": "completed",
  "summary": "Aligned on Q2 key roadmap dates...",
  "created_at": "2026-06-30T09:10:00Z"
}
```

### 3. Retrieve Extracted AI Insights
```bash
curl -X GET "http://localhost:8000/api/v1/meetings/d3b07384-d113-4c5b-90f7-ebf4709cc5b1/action-items"
```
**Response (HTTP 200 OK)**:
```json
[
  {
    "id": "f5b6c7a8-1234-5678-abcd-ef0123456789",
    "description": "Configure whisper transcription service with proper VAD filter",
    "assignee": "John Doe",
    "due_date": "2026-07-05",
    "status": "draft"
  }
]
```

### 4. Update Assignee or Approve Insight
```bash
curl -X PATCH "http://localhost:8000/api/v1/action-items/f5b6c7a8-1234-5678-abcd-ef0123456789" \
  -H "Content-Type: application/json" \
  -d '{"status": "approved", "assignee": "Jane Smith"}'
```

### 5. Dispatch Webhook Sync
```bash
curl -X POST "http://localhost:8000/api/v1/meetings/d3b07384-d113-4c5b-90f7-ebf4709cc5b1/sync"
```
**Response (HTTP 200 OK)**:
```json
{
  "success": true,
  "meeting_id": "d3b07384-d113-4c5b-90f7-ebf4709cc5b1",
  "status_code": 200,
  "message": "Webhook dispatched successfully.",
  "dispatched_at": "2026-06-30T09:15:00Z",
  "sync_log_id": "e4c5d6e7-8899-aabb-ccdd-eeff00112233",
  "skipped": false
}
```

---

## 17. Testing

### Docker Stack Verification
Check service dependencies health checks (DB and Redis should report healthy):
```bash
docker compose ps
```

### Swagger Interactive Route Testing
1. Navigate to `http://localhost:8000/docs` in your browser.
2. Select `POST /api/v1/meetings/upload`, click "Try it out", check `consent_given`, upload a mock `.mp3` or `.wav` file, and click "Execute".
3. Verify it returns `202 Accepted` with a UUID.
4. Hit `/ready` to inspect database and message broker health:
   ```bash
   curl -i http://localhost:8000/ready
   ```

### MCP Inspector Verification
Ensure the Node.js MCP server is registered correctly:
1. Connect using the Inspector CLI:
   ```bash
   cd mcp-server
   DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/meeting_agent" npx @modelcontextprotocol/inspector node server.js
   ```
2. Navigate to the displayed local inspector URL.
3. Test executing `list_meetings` or search transcripts using key terms.

---

## 18. Troubleshooting

### `DATABASE_URL` Connection Issues
* **Problem**: FastAPI backend returns connection errors or Celery worker throws loop errors.
* **Fix**: Ensure `DATABASE_URL` is correct. If running inside Docker Compose, the database host must be `db` (e.g. `postgresql://postgres:postgrespassword@db:5432/meeting_agent`). If running locally outside Docker, set it to `localhost` or `127.0.0.1`.

### Docker Network Collisions
* **Problem**: Ports `5432` or `6379` are already in use.
* **Fix**: Stop any local Postgres or Redis servers running on the host system:
  ```bash
  # On macOS
  brew services stop postgresql
  brew services stop redis
  ```

### MCP Inspector Fails to Start
* **Problem**: MCP server stdout contains non-JSON content.
* **Fix**: The standard Model Context Protocol relies strictly on stdin/stdout for communication. In the Node MCP codebase, avoid writing `console.log` statements. All debug/logging calls MUST be routed to `console.error` (which targets stderr).

### Celery / Redis Startup Issues
* **Problem**: Celery tasks are registered but never executed.
* **Fix**: Ensure the Celery worker process is running and connected. Run `docker compose logs worker` to verify it successfully connects to Redis. In a local environment, make sure Redis is running (`redis-cli ping` returns `PONG`).

---

## 19. Future Enhancements

* **Authentication**: Integrate OAuth2 with JWT tokens to secure REST API endpoints.
* **Multi-User & Tenants Support**: Implement tenancy scopes to isolate meeting uploads and transcripts per user/organization.
* **Jira & Slack integrations**: Support authenticating directly with Slack/Jira using OAuth flows to post action items directly as tickets.
* **Semantic Vector Search**: Generate embeddings for transcript segments using models like `text-embedding-3-small` and index them in PostgreSQL using pgvector's HNSW indexes.
* **Multi-Language Transcription**: Extend Whisper parameters to support real-time language detection and automated translation.
* **Real-time Meeting Streaming**: Implement WebSockets support to pipe audio live to the transcription worker for real-time meeting transcription.

---

## 20. License

Distributed under the MIT License. See `LICENSE` for more information.
