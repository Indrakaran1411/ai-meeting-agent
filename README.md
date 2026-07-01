# Meeting Intelligence Agent

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15.5-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%20%7C%20pgvector-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, production-ready AI Meeting and Channel Intelligence Agent designed to ingest meeting audio files, extract transcriptions, perform structured AI analysis (extracting summaries, action items, decisions, and risks), and classify chat channel signals for actionable corporate intelligence.

---

## 1. Project Overview

The **Meeting Intelligence Agent** solves the challenge of corporate knowledge loss and administrative overhead by automating the ingestion of meeting recordings and chat communications, transforming raw audio into structured, queryable knowledge.

### High-Level Workflow
1. **Ingest & Validate**: Receives audio uploads (MP3, WAV, M4A) via a FastAPI REST endpoint with mandatory privacy consent checks, or via the Next.js Drag-and-Drop file uploader.
2. **Queue**: Streams audio to local storage and enqueues a Celery task in a Redis broker.
3. **Speech-to-Text**: The Celery worker transcribes audio using a thread-safe `faster-whisper` model.
4. **AI Insight Extraction**: Transcripts are analyzed using `gemini-2.5-flash` with JSON schema enforcement to extract high-level summaries, action items, decisions, and risks.
5. **Deduplicated Sync**: Dispatches meeting data to configured PM tool webhooks using deterministic SHA-256 hashing to guarantee single-delivery semantics.
6. **Dashboard UI**: Displays KPIs, paginated meetings tables, inline insight editing, and webhook synchronization controls in a premium Next.js 15 web console.
7. **Bridge**: Exposes insights through a REST API and a Model Context Protocol (MCP) server for direct LLM client consumption.

---

## 2. Features

* **Consolidated Web Dashboard**: React Query (TanStack v5) front page detailing corporate KPIs (total meetings, completed, processing, action items, decisions, risks) and recent drafts.
* **AI Semantic Search Workspace**: Custom workspace (`/search`) querying contextual meaning (using cosine similarity on 768-dimensional embeddings) and highlighting matches.
* **Audio Ingestion**: Drag-and-drop file uploader with upload stream progress indicators and Celery task polling.
* **Paginated Log Table**: Search and filter list of meetings in a structured grid with deletion confirmations.
* **Interactive Tabs details**: Layout rendering summaries, transcripts keyword search, editable action items, decisions, severity-controlled risks, Slack chat signals, and webhook audit trails.
* **Outbound Webhook Hub**: Integration control page displaying payload hashes, last sync times, and dispatch buttons.
* **Speech-to-Text Pipeline**: Decoupled transcription worker using the `faster-whisper` library with Voice Activity Detection (VAD) filtering.
* **AI Meeting Analysis**: Google Gemini SDK integration using `gemini-2.5-flash` with strict Pydantic JSON schema validation.
* **PostgreSQL + pgvector**: Relationally indexes all meetings, segments, and insights. Includes compound indices to support fast lookups.
* **Redis + Celery**: Resilient background processing with automatic retries, late task acknowledgements, and exponential backoff + jitter.
* **Webhook Integration**: PM sync endpoint utilizing deterministic payload SHA-256 hashing for idempotency protection, with complete audit logs tracking webhook responses and network faults.
* **MCP Server**: Stdio-based Node.js Model Context Protocol (MCP) server connecting directly to PostgreSQL, allowing AI agents to query corporate meeting history and search transcripts.

---

## 3. System Architecture

### Core System Workflow
```text
Client (Web / Curl)
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

---

## 4. Technology Stack

* **Backend**: Python 3.11, FastAPI, Uvicorn, Pydantic v2 (Settings v2), SQLAlchemy 2.0 (Async), Alembic, Faster-Whisper, Google GenAI SDK (`google-genai`)
* **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS v4, Lucide React, Axios, TanStack React Query, Sonner
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
│   │   │   ├── transcription_service.py # Faster-Whisper audio transcription service
│   │   │   └── webhook_service.py     # Outbound webhook sender with socket pooling
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
├── frontend/                          # Next.js 15 Web Dashboard Application
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx               # Dashboard Home Page (Page 1)
│   │   │   ├── upload/                # Audio upload & status monitor (Page 2)
│   │   │   ├── meetings/              # Paginated, filterable meeting logs (Page 3)
│   │   │   │   └── [id]/              # Details tabs (Page 4) & Webhook Sync manager (Page 5)
│   │   ├── components/                # Shared layout & QueryClient providers
│   │   └── lib/                       # Typesafe Axios API wrappers
│   ├── package.json
│   └── next.config.ts
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
*   [Docker & Docker Compose](https://www.docker.com/)
*   [Node.js (v18+)](https://nodejs.org/)
*   [Python 3.11+](https://www.python.org/)

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
* `GEMINI_API_KEY`: Google Gemini Key for structured analysis.

---

## 7. Environment Variables

Below are the key variables supported by the `.env` configuration:

| Variable Name | Description | Example Placeholder |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgrespassword@db:5432/meeting_agent` |
| `REDIS_URL` | Redis URL for Celery broker | `redis://redis:6379/0` |
| `GEMINI_API_KEY` | Google Gemini API key | `AIzaSyYourGeminiApiKeyHere` |
| `GEMINI_MODEL` | Gemini model name to use | `gemini-2.5-flash` |
| `UPLOAD_DIRECTORY` | Location to store meeting recordings | `uploads/meetings` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `PM_WEBHOOK_URL` | Downstream PM Webhook endpoint URL | `https://api.pm-tool.com/webhooks/meetings` |

---

## 8. Running with Docker Compose

Running the backend services (DB, Redis, API, Worker) inside Docker Compose is the recommended path:

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

### Inspect logs
```bash
# View Celery worker logs
docker compose logs worker -f

# View FastAPI API logs
docker compose logs backend -f
```

### Stop the Stack
```bash
docker compose down
```

---

## 9. Running Backend Locally (Alternative)

If you want to run the backend directly on the host (for testing or debugging):

### 1. Create a Python Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Database Migrations
```bash
export DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/meeting_agent"
alembic upgrade head
```

### 3. Run FastAPI Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run Celery Worker
```bash
export REDIS_URL="redis://localhost:6379/0"
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

---

## 10. Running Frontend Locally

### 1. Create Environment Configuration
In the root of the `/frontend` directory, create `.env.local`:
```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local
```

### 2. Install Node Dependencies
```bash
npm install
```

### 3. Start Development Server
Runs the web app on `http://localhost:3002`:
```bash
npm run dev -- -p 3002
```

### 4. Create Production Build
```bash
npm run build
npm run start -- -p 3002
```

---

## 11. Swagger API Documentation & Key Endpoints

The backend API automatically generates interactive Swagger documentation.

* **Documentation URL**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **OpenAPI Spec URL**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Key Endpoints:
* `GET /api/v1/search/semantic?q=<query>`: Performs ranked semantic vector search using cosine similarity across meeting summaries and transcript segment vectors.
* `POST /api/v1/meetings/upload`: Upload recording (requires title, audio file, and `consent_given=True` form fields).
* `GET /api/v1/meetings`: Paginated list of meetings.
* `GET /api/v1/meetings/search`: Case-insensitive title and summary keyword text search.
* `POST /api/v1/meetings/{id}/sync`: outbound project sync dispatcher utilizing SHA-256 idempotency.

---

## 12. MCP Server Bridge

### What is MCP?
The **Model Context Protocol (MCP)** is an open standard that enables LLM applications (like Cursor, Claude Desktop, or custom agent systems) to securely interact with database servers, filesystem directories, and local tools.

### Available Tools
1. `list_meetings` (Paginated list of meetings with status filters)
2. `search_transcripts` (Keyword text searches across transcript segments)

### Launching the MCP Inspector
```bash
cd mcp-server
npm install

# Run the Inspector pointing to your PostgreSQL instance
DATABASE_URL="postgresql://postgres:postgrespassword@localhost:5432/meeting_agent" npx @modelcontextprotocol/inspector node server.js
```

---

## 13. Screenshots Section Placeholders

### Dashboard Landing Page
*(Placeholder for Dashboard screenshot displaying KPI cards and task lists)*

### Ingestion Uploader
*(Placeholder for Upload screenshot displaying drag-and-drop file import progress)*

### Meeting Details Tabbed View
*(Placeholder for Details page screenshot showing editable action items and speaker segments)*

---

## 14. Future Enhancements

* **OAuth2 Authentication**: Integrate JWT tokens to secure REST API endpoints.
* **tenancy Scopes**: Support isolating meeting uploads per user/organization.
* **Vector Index Fine-tuning (HNSW)**: Build HNSW indexes on `summary_embedding` and `embedding` using `vector_cosine_ops` to optimize semantic lookup speed as database size increases.
* **Real-time Meeting Streaming**: Implement WebSockets support to pipe audio live to the transcription worker for real-time meeting transcription.

---

## 15. License

Distributed under the MIT License. See `LICENSE` for more information.
