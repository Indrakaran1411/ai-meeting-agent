# Task Breakdown: Enterprise Meeting & Channel Intelligence Agent

This document contains the atomic task breakdown for the **Meeting & Channel Intelligence Agent**. The implementation consists of **12 Milestones**, with all tasks 100% completed and verified.

---

## Milestone 1: Docker Compose & Database Scaffold (100% Completed)

### T1.1: Initialize Directory & Docker Setup [COMPLETED]
*   **Task ID**: `T1.1`
*   **Objective**: Create the base directory structure and primary Docker configurations.
*   **Files or assets**: `docker-compose.yml`, `backend/Dockerfile`, `backend/requirements.txt`
*   **Acceptance criteria**: Docker containers compile and build without error.
*   **Manual testing**: Run `docker compose config` to verify syntax.

### T1.2: Set Up PostgreSQL Container [COMPLETED]
*   **Task ID**: `T1.2`
*   **Objective**: Configure the Postgres database container with the pgvector extension.
*   **Files or assets**: `docker-compose.yml` (Postgres service node)
*   **Acceptance criteria**: Database service is accessible on port 5432 and pgvector extension is loaded.
*   **Manual testing**: Run `docker compose up db` and log in via `psql` to check pgvector availability.

### T1.3: Set Up Redis Container [COMPLETED]
*   **Task ID**: `T1.3`
*   **Objective**: Configure the Redis container to serve as the message broker.
*   **Files or assets**: `docker-compose.yml` (Redis service node)
*   **Acceptance criteria**: Redis container running and accepting connections on port 6379.
*   **Manual testing**: Execute `docker compose exec redis redis-cli ping` and check for `PONG` response.

### T1.4: Initialize FastAPI Backend App [COMPLETED]
*   **Task ID**: `T1.4`
*   **Objective**: Configure basic FastAPI hello world application inside the backend container.
*   **Files or assets**: `backend/app/main.py`
*   **Acceptance criteria**: Sending request to `http://localhost:8000/` yields response.
*   **Manual testing**: Run `curl http://localhost:8000/health` and verify returns successfully.

---

## Milestone 2: SQLAlchemy Schema Models (100% Completed)

### T2.1: Establish Database Helper [COMPLETED]
*   **Task ID**: `T2.1`
*   **Objective**: Write base database connection and session management scripts.
*   **Files or assets**: `backend/app/db/database.py`, `backend/app/db/base.py`
*   **Acceptance criteria**: Able to fetch session engine and execute queries.
*   **Manual testing**: Execute a test connection to query current timestamp from Postgres.

### T2.2: Define Meeting Model [COMPLETED]
*   **Task ID**: `T2.2`
*   **Objective**: Write the SQLAlchemy model representing meeting metadata.
*   **Files or assets**: `backend/app/models/meeting.py`
*   **Acceptance criteria**: Model matches Postgres schema fields, handles default status configurations.
*   **Manual testing**: Verify table metadata matches DB representation.

### T2.3: Define Insight Models (ActionItem, Decision, Risk) [COMPLETED]
*   **Task ID**: `T2.3`
*   **Objective**: Implement SQLAlchemy models representing AI-derived insights.
*   **Files or assets**: `backend/app/models/action_item.py`, `backend/app/models/decision.py`, `backend/app/models/risk.py`
*   **Acceptance criteria**: Lookups resolve correctly; Foreign keys cascaded on deletion.
*   **Manual testing**: Create sample action items linked to meeting record, verify relational query.

### T2.4: Define Transcript and Chat Signals Models [COMPLETED]
*   **Task ID**: `T2.4`
*   **Objective**: Implement SQLAlchemy models capturing transcript segments and chat platform blocker signals.
*   **Files or assets**: `backend/app/models/transcript.py`, `backend/app/models/chat_signal.py`
*   **Acceptance criteria**: Models correctly capture text content and relationship mappings.
*   **Manual testing**: Insert test row and verify all columns map correctly.

### T2.2: Alembic Migrations Configuration [COMPLETED]
*   **Task ID**: `T2.5`
*   **Objective**: Configure Alembic for async operations, import models metadata, and run schema migration.
*   **Files or assets**: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/366f35fdc6b0_initial_schema.py`
*   **Acceptance criteria**: Alembic generates tables inside PostgreSQL.
*   **Manual testing**: Run `alembic upgrade head` and verify PostgreSQL tables.

---

## Milestone 3: Ingestion API Scaffold (100% Completed)

### T3.1: Initialize Main API Router [COMPLETED]
*   **Task ID**: `T3.1`
*   **Objective**: Set up route groupings and API versioning parameters in FastAPI.
*   **Files or assets**: `backend/app/api/__init__.py`, `backend/app/api/v1/meetings.py`
*   **Acceptance criteria**: Navigating to swagger UI shows correct endpoint paths grouped by tag.

### T3.2: Create Request/Response Validation Schemas [COMPLETED]
*   **Task ID**: `T3.2`
*   **Objective**: Implement Pydantic classes for schema validations.
*   **Files or assets**: `backend/app/schemas/meeting.py`
*   **Acceptance criteria**: Requests matching invalid schemas yield `HTTP 422 Unprocessable Entity`.

### T3.3: Implement Meeting Upload Endpoint [COMPLETED]
*   **Task ID**: `T3.3`
*   **Objective**: Build route to receive multipart file uploads and validate file extensions.
*   **Files or assets**: `backend/app/api/v1/meetings.py` (Upload route)
*   **Acceptance criteria**: Valid uploads yield HTTP 202 status and save file to local directory.
*   **Manual testing**: Post a test audio file via curl/Postman and verify file exists on server disk.

### T3.4: Add Consent Flag Validation [COMPLETED]
*   **Task ID**: `T3.4`
*   **Objective**: Enforce strict check on consent flags during ingestion.
*   **Files or assets**: Validation conditions inside upload route.
*   **Acceptance criteria**: Upload yields 400 error if `consent_given` is not true.
*   **Manual testing**: Attempt upload with `consent_given=false` and confirm rejection error payload.

---

## Milestone 4: Queue Orchestration (Celery Worker) (100% Completed)

### T4.1: Configure Celery Client [COMPLETED]
*   **Task ID**: `T4.1`
*   **Objective**: Initialize Celery client configurations and link to Redis URL.
*   **Files or assets**: `backend/app/workers/celery_app.py`
*   **Acceptance criteria**: Celery worker runs and successfully connects to Redis.

### T4.2: Implement process_meeting Task [COMPLETED]
*   **Task ID**: `T4.2`
*   **Objective**: Create the background job execution wrapper.
*   **Files or assets**: `backend/app/workers/tasks.py` (process_meeting task)
*   **Acceptance criteria**: Triggering task executes asynchronously.

### T4.3: Add Database Update Action inside Worker [COMPLETED]
*   **Task ID**: `T4.3`
*   **Objective**: Ensure worker states update the corresponding row values in the database.
*   **Acceptance criteria**: Worker execution updates meeting row status to "Processing" / "Completed".
*   **Manual testing**: Verify table status column values change during job runs.

### T4.4: Task Retries and Error Handling [COMPLETED]
*   **Task ID**: `T4.4`
*   **Objective**: Wrap task loop in exception catches and update DB to "Failed" on error, using Celery's native backoff.
*   **Acceptance criteria**: Throwing errors inside task logs changes database status state properties.

### T4.5: Task Idempotency Guard [COMPLETED]
*   **Task ID**: `T4.5`
*   **Objective**: Guard task executions against duplication.
*   **Acceptance criteria**: Duplicate task triggers are skipped to avoid redundant DB writes.

---

## Milestone 5: Faster-Whisper Speech-to-Text Integration (100% Completed)

### T5.1: Initialize Whisper Service [COMPLETED]
*   **Task ID**: `T5.1`
*   **Objective**: Integrate Faster-Whisper client with process-level locks to prevent double model instantiation.
*   **Files or assets**: `backend/app/services/transcription_service.py`
*   **Acceptance criteria**: Whisper transcribes audio files successfully.

### T5.2: Save Timestamps & Transcript Segments [COMPLETED]
*   **Task ID**: `T5.2`
*   **Objective**: Slice Whisper results and persist individual segments into the database.
*   **Acceptance criteria**: Transcribed segments are saved to `transcripts` table with speaker and timeline markers.

---

## Milestone 6: AI Insight Extraction Orchestration (100% Completed)

### T6.1: Initialize Gemini SDK Client [COMPLETED]
*   **Task ID**: `T6.1`
*   **Objective**: Configure client interface and authenticate API keys.
*   **Files or assets**: `backend/app/services/ai_service.py`
*   **Acceptance criteria**: Verification ping call to Gemini service responds successfully.

### T6.2: Build Insight Analysis Service [COMPLETED]
*   **Task ID**: `T6.2`
*   **Objective**: Implement system prompt instructions for Action Items, Decisions, and Risks.
*   **Files or assets**: `backend/app/services/meeting_analysis_service.py`
*   **Acceptance criteria**: Gemini returns structured Pydantic response classes.

### T6.3: Save Insights to Database [COMPLETED]
*   **Task ID**: `T6.3`
*   **Objective**: Group insights extractions and execute transactional writes to tables.
*   **Acceptance criteria**: Transcripts analysis completes and inserts rows in database.

---

## Milestone 7: Meeting Listing, Update, and Delete API (100% Completed)

### T7.1: Implement Listing & Details GET Routes [COMPLETED]
*   **Task ID**: `T7.1`
*   **Objective**: Expose API endpoints to list paginated meetings and get meeting transcripts.
*   **Files or assets**: `backend/app/api/v1/meetings.py`
*   **Acceptance criteria**: Returns correct paginated records and segments lists.

### T7.2: Implement PATCH Edit Endpoints [COMPLETED]
*   **Task ID**: `T7.2`
*   **Objective**: Allow updating description, assignee, severity, and status of action items, decisions, and risks.
*   **Acceptance criteria**: Partial updates compile and commit successfully.

### T7.3: Implement DELETE Endpoints [COMPLETED]
*   **Task ID**: `T7.3`
*   **Objective**: Allow deletion of individual insights and cascading deletion of a meeting.
*   **Acceptance criteria**: Deletion removes rows and cascading references.

---

## Milestone 8: Search, Stats, and Dashboard API (100% Completed)

### T8.1: Implement /meetings/search Route [COMPLETED]
*   **Task ID**: `T8.1`
*   **Objective**: Search meeting title and summaries using ILIKE query parameters.
*   **Acceptance criteria**: Case-insensitive text searches return matching records.

### T8.2: Implement /meetings/stats Route [COMPLETED]
*   **Task ID**: `T8.2`
*   **Objective**: Return aggregate count variables of meetings and insights.
*   **Acceptance criteria**: Counts match database totals.

### T8.3: Implement /dashboard Route [COMPLETED]
*   **Task ID**: `T8.3`
*   **Objective**: Return consolidated statistics, recent meetings, and draft action items.
*   **Acceptance criteria**: Consolidated response maps to unified DTO structure.

---

## Milestone 9: Weekly Meeting Digest Generator (Backlog / Future Phase)

> [!NOTE]
> Milestone 9 is moved to post-MVP roadmap enhancements as it is out-of-scope for the primary frontend/backend dashboard release.

---

## Milestone 10: Downstream PM Webhook Sync & Idempotency Audit Logging (100% Completed)

### T10.1: Implement Sync Payload Schemas [COMPLETED]
*   **Task ID**: `T10.1`
*   **Objective**: Define validation schemas representing PM Agent payloads.
*   **Files or assets**: `backend/app/schemas/sync.py`

### T10.2: Implement SyncService & Webhook Dispatcher [COMPLETED]
*   **Task ID**: `T10.2`
*   **Objective**: Convert DB objects to sync schemas and dispatch POST requests using socket pooling.
*   **Files or assets**: `backend/app/services/sync_service.py`, `backend/app/services/webhook_service.py`

### T10.3: Expose POST /meetings/{id}/sync Endpoint [COMPLETED]
*   **Task ID**: `T10.3`
*   **Objective**: Orchestrate outgoing webhook payload dispatches.
*   **Acceptance criteria**: Returns HTTP 200 on success and HTTP 503 on connection failure.

### T10.4: Implement Sync Audit Logging [COMPLETED]
*   **Task ID**: `T10.4`
*   **Objective**: Record every sync attempt as PENDING, SUCCESS, or FAILED.
*   **Files or assets**: `backend/app/models/sync_log.py`, `backend/app/services/sync_log_service.py`

### T10.5: Implement Idempotency Hash Deduplication [COMPLETED]
*   **Task ID**: `T10.5`
*   **Objective**: Hash payload contents via SHA-256 and skip dispatch on identical matching logs.
*   **Acceptance criteria**: Skips duplicate network dispatches, returning `skipped=True`.

---

## Milestone 11: MCP Server Bridge (100% Completed)

### T11.1: MCP Server Bootstrap [COMPLETED]
*   **Task ID**: `T11.1`
*   **Objective**: Initialize Node.js stdio transport server.
*   **Files or assets**: `mcp-server/server.js`

### T11.2: PostgreSQL Connection Pool [COMPLETED]
*   **Task ID**: `T11.2`
*   **Objective**: Implement Postgres client pool wrapping `pg.Pool`.
*   **Files or assets**: `mcp-server/database.js`

### T11.3: Implement list_meetings and search_transcripts Tools [COMPLETED]
*   **Task ID**: `T11.3`
*   **Objective**: Create database query execution logic for listing and searching data.
*   **Files or assets**: `mcp-server/tools/`
*   **Acceptance criteria**: JSON-RPC outputs return query records cleanly over stdio.

---

## Milestone 12: Next.js 15 Frontend Dashboard App (100% Completed)

### T12.1: Initialize Next.js 15 App [COMPLETED]
*   **Task ID**: `T12.1`
*   **Objective**: Setup Next.js 15 app with React Query, Axios, Tailwind CSS v4, and shadcn components.
*   **Files or assets**: `/frontend` workspace files.

### T12.2: Build Dashboard Home Page [COMPLETED]
*   **Task ID**: `T12.2`
*   **Objective**: Render KPI counts cards, recent meetings table, and recent draft action items panel.

### T12.3: Build Ingestion Upload UI [COMPLETED]
*   **Task ID**: `T12.3`
*   **Objective**: Build audio file drag-and-drop ingestion page with upload progress indicators and Celery status polling.

### T12.4: Build Meetings Listing Page [COMPLETED]
*   **Task ID**: `T12.4`
*   **Objective**: Build paginated meetings table with search, status filtering, details navigation, and deletion dialogs.

### T12.5: Build Meeting Details & Webhook Sync Hub [COMPLETED]
*   **Task ID**: `T12.5`
*   **Objective**: Build tabbed details interface (transcripts search, inline actions/decisions/risks editors, chat signals) and integration sync button with full audit log lists.

---

## Milestone 13: Semantic Vector Search using pgvector Embeddings (100% Completed)

### T13.1: Model Schema Updates [COMPLETED]
*   **Task ID**: `T13.1`
*   **Objective**: Add Vector columns to Meeting and Transcript models.
*   **Files or assets**: `backend/app/models/meeting.py`, `backend/app/models/transcript.py`

### T13.2: Database Migration [COMPLETED]
*   **Task ID**: `T13.2`
*   **Objective**: Generate and apply Alembic migration adding columns and enabling the pgvector extension.
*   **Files or assets**: `backend/alembic/versions/3714d8d5d642_add_embeddings_to_meetings_and_.py`

### T13.3: Embedding Service [COMPLETED]
*   **Task ID**: `T13.3`
*   **Objective**: Build service class to generate embeddings and update DB rows using gemini-embedding-001.
*   **Files or assets**: `backend/app/services/embedding_service.py`

### T13.4: Background Integration [COMPLETED]
*   **Task ID**: `T13.4`
*   **Objective**: Trigger embedding updates automatically after Celery saves meeting analysis.
*   **Files or assets**: `backend/app/workers/tasks.py`

### T13.5: REST API Endpoint [COMPLETED]
*   **Task ID**: `T13.5`
*   **Objective**: Implement GET /api/v1/search/semantic and rank outcomes using cosine distance.
*   **Files or assets**: `backend/app/api/v1/meetings.py`

### T13.6: Next.js search UI [COMPLETED]
*   **Task ID**: `T13.6`
*   **Objective**: Add AI Semantic Search workspace page and Sidebar links to the web dashboard.
*   **Files or assets**: `frontend/src/app/search/page.tsx`, `frontend/src/components/Sidebar.tsx`
