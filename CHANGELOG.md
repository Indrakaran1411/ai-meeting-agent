# Changelog

All notable changes to the **Meeting Intelligence Agent** project are documented in this file. This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-07-01

### Added
*   **Semantic Vector Search (`GET /api/v1/search/semantic`) (T13.1 - T13.5)**:
    *   Added pgvector `Vector(768)` columns to `meetings` and `transcripts` database tables.
    *   Created `3714d8d5d642` database migration enabling the `vector` PostgreSQL extension and updating schemas.
    *   Developed `EmbeddingService` generating 768-dimensional embeddings using `gemini-embedding-001`.
    *   Hooked up automated embedding generation in the Celery tasks pipeline immediately following meeting analysis completion.
    *   Implemented REST API route `/api/v1/search/semantic` performing cosine distance queries across summaries and transcripts, returning scores normalized to similarity percentages.
*   **Dashboard AI Search View (`/search`) (T13.6)**:
    *   Built typesafe Next.js 15 search page displaying query inputs, skeletons, and ranked matching items.
    *   Highlights summary matches and transcript snippets separately, with direct linking to meeting detail views.
    *   Added search link directly inside the desktop and mobile navigation Sidebars.
*   **Embedding Backfill Utility**:
    *   Implemented `scratch_populate_embeddings.py` to seed embeddings retroactively for all historical records.
*   **Documentation Alignment**:
    *   Synchronized the Gantt charts, Task Breakdown sheets, Implementation specifications, and installation readmes to match the current release.

---

## [1.0.0] - 2026-07-01

### Added
*   **Next.js 15 Frontend Client (`/frontend`) (T12.1 - T12.6)**:
    *   Constructed a responsive, typesafe dashboard web client using Next.js 15, React 19, Tailwind CSS v4, shadcn/ui, and TanStack React Query.
    *   **Consolidated Dashboard Page**: Implemented KPI metrics card grid, recent meetings table, and draft task list.
    *   **Audio Ingestion Page**: Created drag-and-drop uploader supporting progress bar tracking and Celery worker polling.
    *   **Meetings Log Page**: Renders paginated, searchable meeting records table with status filters and cascading deletes.
    *   **Tabbed Details Page**: Renders meeting summaries, speaker-marked transcripts, inline actions/decisions/risks editing forms, and out-of-meeting chat signal flows.
    *   **Webhook Synchronization Page**: Integrates the outbound project sync button, showing SHA-256 payload hashes and attempt counters.
*   **CORS Configuration & allowedDevOrigins**:
    *   Registered `CORSMiddleware` in FastAPI to whitelist loopback and localhost connections on ports 3000, 3001, 3002, and 3003.
    *   Added local network origin mappings to `allowedDevOrigins` in `next.config.ts`.
*   **Cascading Meeting Deletion Router**:
    *   Implemented `DELETE /api/v1/meetings/{id}` endpoint to purge meeting files, transcripts, insights, and sync audits.

### Fixed
*   **FastAPI Router NameError**: Resolved circular dependency module load crash by importing schemas globally rather than inline.
*   **TypeScript & Linter Hardening**: Resolved typescript compilation issues by removing explicit `any` types, cleaning up unused imports, and using typesafe casting.

---

## [0.1.0] - 2026-06-30

### Added
- **Model Context Protocol (MCP) Support (T11.1 - T11.5)**
  - Initialized Node.js MCP server using ESM and `@modelcontextprotocol/sdk`.
  - Implemented Postgres connection pooling in `database.js` with fast-fail safeguards (5s timeout).
  - Implemented `list_meetings` MCP tool with pagination and status-mapping filters.
  - Implemented `search_transcripts` MCP tool with case-insensitive `ILIKE` database querying and optimized text layouts for LLMs.
  - Hardened server output by routing all telemetry/diagnostics to `stderr` to keep `stdout` clean for JSON-RPC transport.
  - Added full graceful shutdown hook for PostgreSQL database pools on `SIGINT` / `SIGTERM`.

- **PM Webhook Sync & Idempotency Pipeline (T10.2 - T10.6)**
  - Created outward webhook transmitter `WebhookService` with `httpx.AsyncClient` socket pooling.
  - Added webhook payload mapping schemas inside `backend/app/schemas/sync.py`.
  - Configured `POST /api/v1/meetings/{id}/sync` endpoint.
  - Introduced SHA-256 deterministic payload hashing (excluding metadata timestamps) to implement strict client idempotency.
  - Added `sync_logs` audit tables to log every outbound request, including detailed error payloads on network drops.

- **System Uptime, Observability & Error Handling (T9.1 - T9.3, T10.1)**
  - Configured centralized standard logging with `X-Request-ID` correlation middleware to track request lifecycles.
  - Added global Starlette exception translation layers to output structured JSON error envelopes instead of tracebacks.
  - Implemented operational health `/health` and readiness `/ready` routes to check PostgreSQL/Redis ping times.
  - Hardened OpenAPI documentation, adding descriptions, validation bounds, and response examples to the Swagger UI.

- **Dashboard, Statistics & Search APIs (T8.1 - T8.3)**
  - Created `GET /api/v1/dashboard` compiling stats, 5 recent meetings, and 5 draft action items.
  - Added `GET /api/v1/meetings/stats` return counts without causing SQLAlchemy N+1 loads.
  - Implemented case-insensitive meeting searches `GET /api/v1/meetings/search` querying titles and summaries.

- **Insight CRUD REST Handlers (T7.1 - T7.3)**
  - Created paginated and filtered lists `GET /api/v1/meetings`.
  - Implemented partial update validation schemas (`ActionItemUpdateRequest`, `DecisionUpdateRequest`, `RiskUpdateRequest`) and PATCH endpoints.
  - Added DELETE endpoints for action items, decisions, and risks returning `204 No Content`.

- **AI Analysis & Persistence (T6.1 - T6.3)**
  - Integrated `google-genai` client using the `gemini-2.5-flash` model.
  - Configured prompt templates enforcing structured JSON payloads that validate against Pydantic models.
  - Orchestrated worker flow to extract action items (with due dates and verbatim quotes), decisions, risks, and chat signals.
  - Added atomic persistence transaction to insert all extracted insights into Postgres.

- **Faster-Whisper Speech-to-Text Pipeline (T5.1 - T5.2)**
  - Integrated `faster-whisper` for audio-to-text decoding.
  - Configured class-level lock pattern in `TranscriptionService` to ensure single model execution thread.
  - Added transaction logic persisting transcription results to the `transcripts` table and updating meeting status.

- **Celery & Redis Worker Broker (T4.1 - T4.2)**
  - Orchestrated Celery worker task loop inside Docker Compose.
  - Integrated task idempotency checking to skip duplicate work, and enabled retry schedules with exponential backoff and jitter.
  - Fixed SQLAlchemy connection pool collision issues using thread-local event loops.

- **Ingestion & Audio Upload APIs (T3.1 - T3.2)**
  - Formulated multipart form endpoint `POST /api/v1/meetings/upload` to stream audio to local storage.
  - Enforced mandatory consent checks and 100MB file limits.
  - Decoupled disk storage handlers (`StorageService`) from database transaction controllers (`MeetingService`).

- **Database Model & Migrations (T2.1 - T2.2)**
  - Designed SQLAlchemy models: `Meeting`, `Transcript`, `ActionItem`, `Decision`, `Risk`, `ChatSignal`, and `SyncLog`.
  - Configured Alembic online async engine and generated initial schema.

- **Project Scaffolding (T1.1 - T1.2)**
  - Formulated multi-container Docker Compose file linking FastAPI backend, Celery worker, Redis broker, and PostgreSQL database.

---

[0.1.0]: https://github.com/Indrakaran1411/ai-meeting-agent/releases/tag/v0.1.0
