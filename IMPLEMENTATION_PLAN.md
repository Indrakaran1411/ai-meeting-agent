# Implementation Plan: Enterprise Meeting & Channel Intelligence Agent

This document outlines the step-by-step implementation roadmap for building the **Meeting & Channel Intelligence Agent (Agent 5)** using the open-source, containerized stack: FastAPI, PostgreSQL + pgvector, Redis + Celery, and LLM APIs (Gemini/Claude).

The roadmap is structured into bite-sized milestones designed to be executed sequentially, ordered from easiest (scaffolding and schema setup) to hardest (integrations and multi-agent systems).

---

## Roadmap Overview

```mermaid
gantt
    title Implementation Timeline
    dateFormat  D
    axisFormat %d
    section Phase 0: Scaffolding
    M1: Docker Compose & DB Scaffold :active, m1, 0, 2d
    M2: SQLAlchemy Schema Models   :m2, after m1, 3d
    M3: API Webhooks Scaffold      :m3, after m2, 2d
    section Phase 1: Processing & AI
    M4: Queue Orchestration (Celery):m4, after m3, 3d
    M5: AI Insight Extraction       :m5, after m4, 3d
    M6: pgvector Semantic Search    :m6, after m5, 3d
    section Phase 2: Signals & UI
    M7: Chat Signal Classifier      :m7, after m6, 4d
    M8: Human-In-The-Loop Dashboard :m8, after m7, 4d
    section Phase 3: Rollup & Sync
    M9: Weekly Digest Generator    :m9, after m8, 4d
    M10: Downstream PM Agent Sync   :m10, after m9, 4d
    M11: MCP Server Bridge          :m11, after m10, 4d
```

---

## Phase 0: Scaffolding & Base Setup

### Milestone 1: Docker Compose & Database Scaffold
*   **Time Estimate**: 2 hours
*   **Objective**: Build the local dev environment with multi-container services including Postgres, Redis, and a base FastAPI folder structure.
*   **Files/Assets to Create**:
    *   `docker-compose.yml`
    *   `backend/Dockerfile`
    *   `backend/requirements.txt`
*   **Dependencies**: Docker Desktop installed.
*   **Acceptance Criteria**:
    *   Running `docker-compose up` spins up Postgres (with pgvector), Redis, and backend containers successfully.
    *   FastAPI hello world is accessible.
*   **Manual Testing Steps**:
    1. Navigate to the backend URL (`http://localhost:8000/docs`).
    2. Confirm that the swagger docs load.
    3. Run a test connection to Postgres and check that `CREATE EXTENSION IF NOT EXISTS vector;` runs without error.

### Milestone 2: SQLAlchemy Schema Models
*   **Time Estimate**: 3 hours
*   **Objective**: Map out relational entities in SQLAlchemy/SQLModel code matching the Postgres schema specifications.
*   **Files/Assets to Create**:
    *   `backend/app/database.py`
    *   `backend/app/models.py`
*   **Dependencies**: Milestone 1 completed.
*   **Acceptance Criteria**:
    *   Entities for Meetings, Transcripts, Action Items, Decisions, Risks, and Chat Signals compile successfully.
    *   Foreign keys and lookups are functional.
*   **Manual Testing Steps**:
    1. Run the database initialization script.
    2. Inspect table schemas in Postgres to verify column data types and indexes match `models.py`.

### Milestone 3: Ingestion API Webhooks Scaffold
*   **Time Estimate**: 2 hours
*   **Objective**: Set up endpoints to ingest meeting uploads and validate the mandatory consent checkbox configuration.
*   **Files/Assets to Create**:
    *   `backend/app/api/v1/meetings.py`
    *   `backend/app/schemas.py`
*   **Dependencies**: Milestone 2 completed.
*   **Acceptance Criteria**:
    *   Uploads containing `consent_flag = false` return `HTTP 400 Bad Request`.
    *   Valid uploads return `HTTP 202 Accepted` and register a database row.
*   **Manual Testing Steps**:
    1. Send a POST request to `/api/v1/meetings/upload` with a test audio file and `consent_flag=false`. Verify 400 response.
    2. Resubmit with `consent_flag=true`. Verify 202 response and database insertion.

---

## Phase 1: Asynchronous Queue & AI Insights

### Milestone 4: Queue Orchestration (Celery Worker)
*   **Time Estimate**: 3 hours
*   **Objective**: Configure Celery and Redis to extract high-latency tasks from the HTTP loop.
*   **Files/Assets to Create**:
    *   `backend/app/workers/celery_app.py`
    *   `backend/app/workers/tasks.py`
*   **Dependencies**: Milestone 3 completed.
*   **Acceptance Criteria**:
    *   A Celery task runs asynchronously when a meeting file is uploaded.
    *   Worker logs print task states correctly.
*   **Manual Testing Steps**:
    1. Upload a valid meeting.
    2. Check the Celery worker container logs to verify `process_meeting_audio` was picked up and completed.

### Milestone 5: AI Insight Extraction Topic
*   **Time Estimate**: 3 hours
*   **Objective**: Develop structured parsing prompts for extracting actions, decisions, and risks using Claude/Gemini API.
*   **Files/Assets to Create**:
    *   `backend/app/services/ai_service.py`
*   **Dependencies**: Milestone 4 completed.
*   **Acceptance Criteria**:
    *   Action items are extracted with assignee, description, verbatim quote, and due date.
    *   Strict grounding rules prevent hallucinated due dates (returned as null if missing).
*   **Manual Testing Steps**:
    1. Run a test file through the AI service.
    2. Verify the JSON output schema contains valid segments and quotes matching the text.

### Milestone 6: pgvector Semantic Search
*   **Time Estimate**: 3 hours
*   **Objective**: Implement embedding generation and pgvector similarity querying on meeting transcripts.
*   **Files/Assets to Create**:
    *   `backend/app/services/vector_service.py`
    *   `backend/app/api/v1/search.py`
*   **Dependencies**: Milestone 5 completed.
*   **Acceptance Criteria**:
    *   Transcript chunks are embedded and indexed.
    *   Semantic queries return the top-3 matching transcripts with cosine relevance scores.
*   **Manual Testing Steps**:
    1. Index a meeting transcript about "refactoring database schema".
    2. Query `/api/v1/search` with the term "database update".
    3. Verify that the correct meeting and matching text snippet are returned in the response list.

---

## Phase 2: Webhooks & Interactive UI

### Milestone 7: Chat Signal Classifier
*   **Time Estimate**: 4 hours
*   **Objective**: Set up incoming webhook routes to capture channel chat logs and classify them for blockers or decisions.
*   **Files/Assets to Create**:
    *   `backend/app/api/v1/signals.py`
*   **Dependencies**: Milestone 2 completed.
*   **Acceptance Criteria**:
    *   HTTP webhook endpoint parses channel message payloads.
    *   Classifies content into Choice values: Blocker, Decision, Risk, General.
    *   Saves valid signals in the database.
*   **Manual Testing Steps**:
    1. Send a POST request simulating a Slack message with the text "We have a blocker on API auth".
    2. Verify the record is saved under `chat_signals` and classified as "blocker".

### Milestone 8: Human-In-The-Loop Dashboard (React UI)
*   **Time Estimate**: 4 hours
*   **Objective**: Build a clean React application dashboard to search meetings, view summaries, and approve action items.
*   **Files/Assets to Create**:
    *   `frontend/Dockerfile`
    *   `frontend/src/App.tsx`
    *   `frontend/src/components/MeetingDetails.tsx`
*   **Dependencies**: Milestone 6 completed.
*   **Acceptance Criteria**:
    *   Displays meeting list and details.
    *   Renders summaries and action items with edit inputs.
    *   "Approve" button sets action items state to `approved`.
*   **Manual Testing Steps**:
    1. Open dashboard in a browser.
    2. Navigate to a meeting page.
    3. Click edit on an action item, modify the due date, and click Approve. Verify database change.

---

## Phase 3: Rollups & Downstream Integration

### Milestone 9: Weekly Meeting Digest Generator
*   **Time Estimate**: 4 hours
*   **Objective**: Build a scheduled worker task that synthesizes a narrative weekly rollup document via the Claude/Gemini API.
*   **Files/Assets to Create**:
    *   Celery Beat scheduled task configs
    *   `backend/app/services/digest_service.py`
*   **Dependencies**: Milestone 5 completed.
*   **Acceptance Criteria**:
    *   A task runs weekly, reading meetings from the last 7 days.
    *   Generates a structured markdown file summarizing achievements and risks.
*   **Manual Testing Steps**:
    1. Force-run the digest task.
    2. Confirm a new summary file is saved to the local file storage / document folder.

### Milestone 10: Downstream PM Agent Sync
*   **Time Estimate**: 4 hours
*   **Objective**: Sync approved meeting outcomes to the PM Agent's REST API endpoint.
*   **Files or assets**:
    *   `backend/app/services/sync_service.py`
*   **Dependencies**: Milestone 8 completed.
*   **Acceptance Criteria**:
    *   Approving action items on the UI triggers an API POST dispatch.
    *   Action items database status updates from `approved` to `synced` upon success.
*   **Manual Testing Steps**:
    1. Trigger approval in the dashboard.
    2. Verify the webhook payload contains the meeting details and is received by the receiver mock endpoint.

### Milestone 11: MCP Server Bridge
*   **Time Estimate**: 4 hours
*   **Objective**: Construct an MCP server mapping Dataverse/Postgres meeting tables to tool schemas.
*   **Files/Assets to Create**:
    *   `mcp-server/package.json`
    *   `mcp-server/server.js`
*   **Dependencies**: Milestone 2 completed.
*   **Acceptance Criteria**:
    *   Exposes `list_meetings` and `search_transcripts` tools.
    *   Serves requests over standard input/output (stdio).
*   **Manual Testing Steps**:
    1. Run local MCP Inspector: `npx @modelcontextprotocol/inspector node server.js`.
    2. Confirm that tools appear and execute successfully.
