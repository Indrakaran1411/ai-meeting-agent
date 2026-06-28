# Task Breakdown: Enterprise Meeting & Channel Intelligence Agent

This document contains the atomic task breakdown for building the **Meeting & Channel Intelligence Agent (Agent 5)**. The implementation is split into **53 tasks** across 11 milestones, with each task designed to be completed in **30–90 minutes** and tested independently.

---

## Milestone 1: Docker Compose & Database Scaffold

### T1.1: Initialize Directory & Docker Setup
*   **Task ID**: `T1.1`
*   **Objective**: Create the base directory structure and primary Docker configurations.
*   **Files or assets**: `docker-compose.yml`, `backend/Dockerfile`, `backend/requirements.txt`
*   **Inputs**: Docker specifications.
*   **Outputs**: Operational baseline docker layout files.
*   **Dependencies**: None.
*   **Acceptance criteria**: Empty Docker containers compile and build without error.
*   **Manual testing**: Run `docker-compose config` to verify syntax.
*   **Common mistakes**: Mixing python and node workspace folders.

### T1.2: Set Up PostgreSQL Container
*   **Task ID**: `T1.2`
*   **Objective**: Configure the Postgres database container with the pgvector extension.
*   **Files or assets**: `docker-compose.yml` (Postgres service node)
*   **Inputs**: Database credentials, vector extension parameters.
*   **Outputs**: Running Postgres service.
*   **Dependencies**: `T1.1`.
*   **Acceptance criteria**: Database service is accessible on port 5432 and pgvector extension is loaded.
*   **Manual testing**: Run `docker-compose up db` and log in via `psql` to check pgvector availability.
*   **Common mistakes**: Selecting base Postgres image without pgvector binaries.

### T1.3: Set Up Redis Container
*   **Task ID**: `T1.3`
*   **Objective**: Configure the Redis container to serve as the message broker.
*   **Files or assets**: `docker-compose.yml` (Redis service node)
*   **Inputs**: Port configuration.
*   **Outputs**: Running Redis service.
*   **Dependencies**: `T1.1`.
*   **Acceptance criteria**: Redis container running and accepting connections on port 6379.
*   **Manual testing**: Execute `docker-compose exec redis redis-cli ping` and check for `PONG` response.
*   **Common mistakes**: Exposing Redis to host without password in production configurations.

### T1.4: Initialize FastAPI Backend App
*   **Task ID**: `T1.4`
*   **Objective**: Configure basic FastAPI hello world application inside the backend container.
*   **Files or assets**: `backend/app/main.py`
*   **Inputs**: FastAPI dependency setup.
*   **Outputs**: Running FastAPI web service.
*   **Dependencies**: `T1.1`.
*   **Acceptance criteria**: Sending request to `http://localhost:8000/` yields response.
*   **Manual testing**: Run `curl http://localhost:8000/` and verify returns successfully.
*   **Common mistakes**: Missing main execution parameters on uvicorn entrypoint config.

---

## Milestone 2: SQLAlchemy Schema Models

### T2.1: Establish Database Helper
*   **Task ID**: `T2.1`
*   **Objective**: Write base database connection and session management scripts.
*   **Files or assets**: `backend/app/database.py`
*   **Inputs**: Database connection string from environment.
*   **Outputs**: Database session helper function.
*   **Dependencies**: `T1.2`.
*   **Acceptance criteria**: Able to fetch session engine and execute raw queries.
*   **Manual testing**: Execute a test connection to query current timestamp from Postgres.
*   **Common mistakes**: Hardcoding credentials instead of environment variables.

### T2.2: Define Meeting Model
*   **Task ID**: `T2.2`
*   **Objective**: Write the SQLAlchemy model representing meeting metadata.
*   **Files or assets**: `backend/app/models.py` (Meetings model section)
*   **Inputs**: Meeting data specifications.
*   **Outputs**: Python models representation of meetings table.
*   **Dependencies**: `T2.1`.
*   **Acceptance criteria**: Model matches Postgres schema fields, handles default status configurations.
*   **Manual testing**: Generate SQL schema from models and verify matching tables in DB.
*   **Common mistakes**: Setting boolean flags as strings.

### T2.3: Define Transcript and Vector Models
*   **Task ID**: `T2.3`
*   **Objective**: Map transcript segments and pgvector arrays to models.
*   **Files or assets**: `backend/app/models.py` (Transcript models)
*   **Inputs**: pgvector dimension size variables.
*   **Outputs**: Transcript segment and embedding models.
*   **Dependencies**: `T2.2`.
*   **Acceptance criteria**: Transcript model links to Meetings via foreign key relationship.
*   **Manual testing**: Create sample transcript segment and verify relational lookup.
*   **Common mistakes**: Mismatch between vector embedding length and array specification.

### T2.4: Define Actions, Decisions, and Risks Models
*   **Task ID**: `T2.4`
*   **Objective**: Implement models representing AI-derived insights.
*   **Files or assets**: `backend/app/models.py` (Action/Decision/Risk section)
*   **Inputs**: Insight metadata profiles.
*   **Outputs**: Models for actions, decisions, and risks tables.
*   **Dependencies**: `T2.2`.
*   **Acceptance criteria**: Lookups resolve correctly; Enum configurations match properties.
*   **Manual testing**: Create sample action items linked to meeting record, verify relational query.
*   **Common mistakes**: Setting due date columns as mandatory constraints.

### T2.5: Define Chat Signals Model
*   **Task ID**: `T2.5`
*   **Objective**: Implement model capturing out-of-meeting channel signals.
*   **Files or assets**: `backend/app/models.py` (ChatSignals section)
*   **Inputs**: Teams/Slack chat metadata specs.
*   **Outputs**: Chat signals model class.
*   **Dependencies**: `T2.1`.
*   **Acceptance criteria**: Model fields match chat signal database requirements.
*   **Manual testing**: Insert test row and verify all columns map correctly.
*   **Common mistakes**: Setting channel/message IDs as integer variables instead of strings.

---

## Milestone 3: Ingestion API Webhooks Scaffold

### T3.1: Initialize Main API Router
*   **Task ID**: `T3.1`
*   **Objective**: Set up route groupings and API versioning parameters in FastAPI.
*   **Files or assets**: `backend/app/api/__init__.py`, `backend/app/api/v1/__init__.py`
*   **Inputs**: Router configuration details.
*   **Outputs**: Structured API routing.
*   **Dependencies**: `T1.4`.
*   **Acceptance criteria**: Navigating to swagger UI shows correct endpoint paths grouped by tag.
*   **Manual testing**: Query `/docs` and confirm router tags appear correctly.
*   **Common mistakes**: Forgetting to register routers in the main app file.

### T3.2: Create Request/Response Validation Schemas
*   **Task ID**: `T3.2`
*   **Objective**: Implement Pydantic classes for schema validations.
*   **Files or assets**: `backend/app/schemas.py`
*   **Inputs**: JSON schemas specs.
*   **Outputs**: Validation model definitions.
*   **Dependencies**: `T2.2`.
*   **Acceptance criteria**: Requests matching invalid schemas yield `HTTP 422 Unprocessable Entity`.
*   **Manual testing**: Send malformed payload to mock endpoint and verify validation error response.
*   **Common mistakes**: Duplicating database logic inside schema models.

### T3.3: Implement Meeting Upload Endpoint
*   **Task ID**: `T3.3`
*   **Objective**: Build route to receive multipart file uploads and save files locally.
*   **Files or assets**: `backend/app/api/v1/meetings.py` (Upload route)
*   **Inputs**: File parameters, consent value metadata.
*   **Outputs**: Saved file path, JSON status response.
*   **Dependencies**: `T3.2`.
*   **Acceptance criteria**: Valid uploads yield HTTP 202 status and save file to local directory.
*   **Manual testing**: Post a test audio file via curl/Postman and verify file exists on server disk.
*   **Common mistakes**: Storing large files directly in memory rather than streaming to disk.

### T3.4: Add Consent Flag Validation
*   **Task ID**: `T3.4`
*   **Objective**: Enforce strict check on consent flags during ingestion.
*   **Files or assets**: Validation conditions inside upload route.
*   **Inputs**: `consent_flag` request parameter.
*   **Outputs**: HTTP 400 response or execution flow.
*   **Dependencies**: `T3.3`.
*   **Acceptance criteria**: Upload yields 400 error if `consent_flag` is not true.
*   **Manual testing**: Attempt upload with `consent_flag=false` and confirm rejection error payload.
*   **Common mistakes**: Permitting file saving before checking consent status.

---

## Milestone 4: Queue Orchestration (Celery Worker)

### T4.1: Configure Celery Client
*   **Task ID**: `T4.1`
*   **Objective**: Initialize Celery client configurations and link to Redis URL.
*   **Files or assets**: `backend/app/workers/celery_app.py`
*   **Inputs**: Redis connection host string.
*   **Outputs**: Configured Celery application wrapper.
*   **Dependencies**: `T1.3`.
*   **Acceptance criteria**: Celery worker runs and successfully connects to Redis.
*   **Manual testing**: Start Celery worker using command line and verify connection is established.
*   **Common mistakes**: Celery starting before Redis is fully online.

### T4.2: Implement process_meeting_audio Task
*   **Task ID**: `T4.2`
*   **Objective**: Create the background job execution wrapper.
*   **Files or assets**: `backend/app/workers/tasks.py` (process_meeting_audio task)
*   **Inputs**: Meeting ID.
*   **Outputs**: Job lifecycle logs.
*   **Dependencies**: `T4.1`, `T3.3`.
*   **Acceptance criteria**: Triggering task executes asynchronously.
*   **Manual testing**: Trigger task via python script and observe logs inside worker shell.
*   **Common mistakes**: Passing complex model objects to tasks instead of simple database IDs.

### T4.3: Implement PII Redaction Helper
*   **Task ID**: `T4.3`
*   **Objective**: Write text utility to scrub email and phone details from raw content text.
*   **Files or assets**: `backend/app/services/redact.py`
*   **Inputs**: String.
*   **Outputs**: Redacted string.
*   **Dependencies**: None.
*   **Acceptance criteria**: Replaces target regex patterns with `[REDACTED]`.
*   **Manual testing**: Pass test string and verify clean output details.
*   **Common mistakes**: Overly aggressive regex matching that sanitizes general formatting.

### T4.4: Add Database Update Action inside Worker
*   **Task ID**: `T4.4`
*   **Objective**: Ensure worker states update the corresponding row values in the database.
*   **Files or assets**: Task logic nodes.
*   **Inputs**: Task status codes.
*   **Outputs**: Database updates.
*   **Dependencies**: `T4.2`, `T2.1`.
*   **Acceptance criteria**: Worker execution updates meeting row status to "Processing" / "Completed".
*   **Manual testing**: Verify table status column values change during job runs.
*   **Common mistakes**: Session leaks inside worker processes.

### T4.5: Configure Worker Error Logging
*   **Task ID**: `T4.5`
*   **Objective**: Wrap task loop in exception catches and update DB to "Failed" on error.
*   **Files or assets**: Task retry/catch blocks.
*   **Inputs**: System errors.
*   **Outputs**: Database error updates.
*   **Dependencies**: `T4.4`.
*   **Acceptance criteria**: Throwing errors inside task logs changes database status state properties.
*   **Manual testing**: Throw deliberate runtime error inside task code and verify status updates to "Failed".
*   **Common mistakes**: Swallowing errors without logging the stack trace.

---

## Milestone 5: AI Insight Extraction

### T5.1: Initialize LLM SDK Client
*   **Task ID**: `T5.1`
*   **Objective**: Configure client interface and authenticate API keys.
*   **Files or assets**: `backend/app/services/ai_service.py`
*   **Inputs**: API client dependency, API key environment variables.
*   **Outputs**: Operational SDK instances.
*   **Dependencies**: `T1.4`.
*   **Acceptance criteria**: Verification ping call to LLM service responds successfully.
*   **Manual testing**: Run small test script to print a simple completion call response.
*   **Common mistakes**: Hardcoding API keys inside code repository.

### T5.2: Create Action Item Prompt
*   **Task ID**: `T5.2`
*   **Objective**: Implement system prompt instructions for action items extraction.
*   **Files or assets**: Prompt strings in AI Service.
*   **Inputs**: Meeting transcript.
*   **Outputs**: Structured JSON response list.
*   **Dependencies**: `T5.1`.
*   **Acceptance criteria**: LLM returns exact JSON format containing action fields.
*   **Manual testing**: Parse text containing action statements and confirm output properties.
*   **Common mistakes**: Allowing the model to hallucinate dates that are not in the text.

### T5.3: Create Decision Prompt
*   **Task ID**: `T5.3`
*   **Objective**: Implement prompt rules to extract decisions and rationale.
*   **Files or assets**: Prompt configuration.
*   **Inputs**: Meeting transcript.
*   **Outputs**: JSON list of decisions.
*   **Dependencies**: `T5.1`.
*   **Acceptance criteria**: Returned decisions include the rationale and a verbatim quote.
*   **Manual testing**: Feed sample transcript text and check output fields.
*   **Common mistakes**: Missing the verbatim quote context parameters.

### T5.4: Create Risk Prompt
*   **Task ID**: `T5.4`
*   **Objective**: Implement risk extraction prompt with severity scales.
*   **Files or assets**: Risk prompt configs.
*   **Inputs**: Transcript text.
*   **Outputs**: JSON list of risks.
*   **Dependencies**: `T5.1`.
*   **Acceptance criteria**: Severity levels map only to allowed values.
*   **Manual testing**: Test transcript and ensure classification results are within choice bounds.
*   **Common mistakes**: Outputting free-text severity classifications.

### T5.5: Save Insights to Database
*   **Task ID**: `T5.5`
*   **Objective**: Group insights extractions and execute transactional writes to tables.
*   **Files or assets**: AI service orchestrator task.
*   **Inputs**: LLM responses.
*   **Outputs**: Database rows.
*   **Dependencies**: `T5.2`, `T5.3`, `T5.4`, `T2.4`.
*   **Acceptance criteria**: Transcripts analysis completes and inserts rows in database.
*   **Manual testing**: Run integration task and verify new action items/decisions exist in Postgres.
*   **Common mistakes**: Storing database rows even if one of the extraction steps fails.

---

## Milestone 6: pgvector Semantic Search

### T6.1: Define Embedding Utility
*   **Task ID**: `T6.1`
*   **Objective**: Implement service to generate float embeddings from text query parameters.
*   **Files or assets**: `backend/app/services/vector_service.py` (embedding function)
*   **Inputs**: Text query string.
*   **Outputs**: Float array.
*   **Dependencies**: `T5.1`.
*   **Acceptance criteria**: Returns float vector list matching target dimension size.
*   **Manual testing**: Generate embeddings for test word and verify vector length is 1536.
*   **Common mistakes**: Vector dimension mismatch due to model updates.

### T6.2: Build Chunking Service
*   **Task ID**: `T6.2`
*   **Objective**: Create logic to slice transcripts into overlapping segments.
*   **Files or assets**: `backend/app/services/vector_service.py` (chunk function)
*   **Inputs**: Transcript array.
*   **Outputs**: List of text chunks.
*   **Dependencies**: `T2.3`.
*   **Acceptance criteria**: Output yields correct overlapping chunk segments.
*   **Manual testing**: Pass test transcript array and confirm chunk boundaries overlap as configured.
*   **Common mistakes**: Splitting text inside a sentence boundary.

### T6.3: Implement Bulk Vector Insertion
*   **Task ID**: `T6.3`
*   **Objective**: Write code to bulk insert transcript chunks and embeddings.
*   **Files or assets**: `backend/app/services/vector_service.py` (insert function)
*   **Inputs**: Transcript chunks, embeddings.
*   **Outputs**: Database row insertions.
*   **Dependencies**: `T6.1`, `T6.2`.
*   **Acceptance criteria**: Database inserts vector type records successfully.
*   **Manual testing**: Perform bulk insert and verify record counts in Postgres.
*   **Common mistakes**: slow row-by-row insertions instead of bulk insert routines.

### T6.4: Write Cosine Similarity Query
*   **Task ID**: `T6.4`
*   **Objective**: Implement SQL query to search pgvector indexes.
*   **Files or assets**: pgvector query functions.
*   **Inputs**: Search vector.
*   **Outputs**: Matching transcript rows with similarity metrics.
*   **Dependencies**: `T6.3`.
*   **Acceptance criteria**: Returns top results sorted by distance.
*   **Manual testing**: Query database and check relevance ordering.
*   **Common mistakes**: Using Euclidean distance instead of Cosine distance for text embeddings.

### T6.5: Implement Search API Endpoint
*   **Task ID**: `T6.5`
*   **Objective**: Connect search query functionality to public API routes.
*   **Files or assets**: `backend/app/api/v1/search.py`
*   **Inputs**: Query string.
*   **Outputs**: JSON list of search results.
*   **Dependencies**: `T6.4`.
*   **Acceptance criteria**: Endpoint returns results within specified latency boundaries.
*   **Manual testing**: Send query to `/api/v1/search` and verify results structure matches specification.
*   **Common mistakes**: Exposing raw database schemas in api outputs.

---

## Milestone 7: Chat Signal Classifier

### T7.1: Implement Signal Webhook Route
*   **Task ID**: `T7.1`
*   **Objective**: Set up REST webhook listener endpoint.
*   **Files or assets**: `backend/app/api/v1/signals.py`
*   **Inputs**: JSON webhook payload.
*   **Outputs**: JSON status code 200.
*   **Dependencies**: `T3.1`.
*   **Acceptance criteria**: Endpoint accepts request payloads without error.
*   **Manual testing**: Send test webhook payload via curl and confirm receipt response.
*   **Common mistakes**: Rejecting incoming request parameters due to strict validation.

### T7.2: Build Webhook Signature Validation
*   **Task ID**: `T7.2`
*   **Objective**: Enforce security validation checks on webhook headers.
*   **Files or assets**: Verification headers inside webhook logic.
*   **Inputs**: Request headers.
*   **Outputs**: Exception or verification validation pass.
*   **Dependencies**: `T7.1`.
*   **Acceptance criteria**: Invalid payloads yield HTTP 401 Unauthorized status.
*   **Manual testing**: Test endpoint with missing or fake security headers. Verify rejection.
*   **Common mistakes**: Hardcoding secret tokens.

### T7.3: Create Classifier Prompt
*   **Task ID**: `T7.3`
*   **Objective**: Implement prompt models to tag messages as Blocker/Decision/Risk/General.
*   **Files or assets**: Prompt settings inside signal logic.
*   **Inputs**: Message text.
*   **Outputs**: Classification text.
*   **Dependencies**: `T5.1`, `T7.2`.
*   **Acceptance criteria**: Returns correct classifications for test patterns.
*   **Manual testing**: Feed typical developer chat texts and verify classification outcomes.
*   **Common mistakes**: Marking standard developer talk as blockers.

### T7.4: Save Chat Signal Record
*   **Task ID**: `T7.4`
*   **Objective**: Insert signal data into target database tables.
*   **Files or assets**: Database insert actions.
*   **Inputs**: Signal properties.
*   **Outputs**: Saved row.
*   **Dependencies**: `T7.3`, `T2.5`.
*   **Acceptance criteria**: Database contains record of signal data.
*   **Manual testing**: Check if database reflects correct classification choices for tests.
*   **Common mistakes**: Database connection leaks during high-frequency message streams.

### T7.5: Connect to Downstream PM Agent Notification
*   **Task ID**: `T7.5`
*   **Objective**: Dispatch webhook alerts when blocker signals are captured.
*   **Files or assets**: Alert output scripts.
*   **Inputs**: Blocker record data.
*   **Outputs**: Outgoing event.
*   **Dependencies**: `T7.4`.
*   **Acceptance criteria**: Webhook dispatches correctly.
*   **Manual testing**: Post blocker message and check downstream mock server logs.
*   **Common mistakes**: Flooding target server with duplicate message notifications.

---

## Milestone 8: Human-In-The-Loop Dashboard

### T8.1: Initialize React Application
*   **Task ID**: `T8.1`
*   **Objective**: Scaffold React web app workspace using Vite.
*   **Files or assets**: `frontend/Dockerfile`, `frontend/package.json`
*   **Inputs**: npm configs.
*   **Outputs**: Running dev server.
*   **Dependencies**: None.
*   **Acceptance criteria**: Local developer interface is accessible on port 5173.
*   **Manual testing**: Navigate to `http://localhost:5173/` and confirm basic UI displays.
*   **Common mistakes**: Hardcoding dev proxy configs.

### T8.2: Build Meeting List View
*   **Task ID**: `T8.2`
*   **Objective**: Build UI to list processed meetings.
*   **Files or assets**: `frontend/src/components/MeetingList.tsx`
*   **Inputs**: Meetings list data from API.
*   **Outputs**: Rendered table interface.
*   **Dependencies**: `T8.1`, `T3.3`.
*   **Acceptance criteria**: Displays database meeting details in table layout.
*   **Manual testing**: View page and confirm records match database listings.
*   **Common mistakes**: Failure to handle empty list states.

### T8.3: Build Meeting Detail View
*   **Task ID**: `T8.3`
*   **Objective**: Render transcription details, summary, and action items.
*   **Files or assets**: `frontend/src/components/MeetingDetails.tsx`
*   **Inputs**: Meeting ID.
*   **Outputs**: Detailed layout page.
*   **Dependencies**: `T8.2`.
*   **Acceptance criteria**: Renders tabs showing transcript segments and extracted insights.
*   **Manual testing**: Navigate to meeting details page and confirm all fields display.
*   **Common mistakes**: Renders blank page if transcript contains no segments.

### T8.4: Add Edit Action Items Panel
*   **Task ID**: `T8.4`
*   **Objective**: Enable edit form inputs on action item lists.
*   **Files or assets**: Inline editor code components.
*   **Inputs**: User input text.
*   **Outputs**: Update request payload.
*   **Dependencies**: `T8.3`.
*   **Acceptance criteria**: Form inputs permit modifying description and due date values.
*   **Manual testing**: Click edit on task and change value parameters.
*   **Common mistakes**: Changes not updating state variables.

### T8.5: Implement Approval Submission
*   **Task ID**: `T8.5`
*   **Objective**: Call API approval endpoint when "Approve" button is clicked.
*   **Files or assets**: Approve event handlers.
*   **Inputs**: Click trigger.
*   **Outputs**: API response status.
*   **Dependencies**: `T8.4`.
*   **Acceptance criteria**: Click changes action item status indicator to "Approved" in UI.
*   **Manual testing**: Click approve and check database record status.
*   **Common mistakes**: Double clicks triggering duplicate API submissions.

---

## Milestone 9: Weekly Meeting Digest Generator

### T9.1: Configure Celery Beat
*   **Task ID**: `T9.1`
*   **Objective**: Define task schedule in Celery configuration files.
*   **Files or assets**: `backend/app/workers/celery_app.py` (Beat settings)
*   **Inputs**: Schedule properties.
*   **Outputs**: Scheduled runner state.
*   **Dependencies**: `T4.1`.
*   **Acceptance criteria**: Task schedule appears in Celery logs.
*   **Manual testing**: Check Celery logs to ensure Beat scheduler matches config.
*   **Common mistakes**: Runner timezone settings mismatched.

### T9.2: Compile Weekly Context Data
*   **Task ID**: `T9.2`
*   **Objective**: Write query retrieving all database records for the week.
*   **Files or assets**: Context builder functions.
*   **Inputs**: Timestamp limits.
*   **Outputs**: Structured log text block.
*   **Dependencies**: `T9.1`, `T2.1`.
*   **Acceptance criteria**: Returns exact records matching dates query.
*   **Manual testing**: Query past week data and check output parameters.
*   **Common mistakes**: Timezone offsets omitting latest updates.

### T9.3: Define Weekly Digest prompt
*   **Task ID**: `T9.3`
*   **Objective**: Implement LLM instructions for weekly rollups.
*   **Files or assets**: Prompt strings in AI Service.
*   **Inputs**: Weekly context logs.
*   **Outputs**: Weekly narrative summary.
*   **Dependencies**: `T9.2`.
*   **Acceptance criteria**: Summary details decisions and actions cleanly in Markdown.
*   **Manual testing**: Run prompt test cases and verify section layouts.
*   **Common mistakes**: Prompt text exceeding token limits.

### T9.4: Implement Document Exporter
*   **Task ID**: `T9.4`
*   **Objective**: Write markdown-to-pdf or html converter scripts.
*   **Files or assets**: Exporter code utilities.
*   **Inputs**: Markdown content.
*   **Outputs**: PDF/HTML binary stream.
*   **Dependencies**: `T9.3`.
*   **Acceptance criteria**: Generates valid formatted document file.
*   **Manual testing**: Generate sample document and open in browser/viewer.
*   **Common mistakes**: Incomplete rendering of special characters.

### T9.5: Create Local Volume File Save
*   **Task ID**: `T9.5`
*   **Objective**: Save generated report in local file directories.
*   **Files or assets**: Write output operations.
*   **Inputs**: Document stream.
*   **Outputs**: Saved file path.
*   **Dependencies**: `T9.4`.
*   **Acceptance criteria**: File is stored in folder structure.
*   **Manual testing**: Run task and verify file is written to storage directory.
*   **Common mistakes**: Missing directory path permissions.

---

## Milestone 10: Downstream PM Agent Sync

### T10.1: OpenAPI Documentation
*   **Task ID**: `T10.1`
*   **Objective**: Document the Downstream PM Agent synchronization API contracts in OpenAPI format.
*   **Files or assets**: `backend/openapi.json`
*   **Inputs**: API sync requirements.
*   **Outputs**: OpenAPI sync specifications.
*   **Dependencies**: `T8.5`.
*   **Acceptance criteria**: Valid OpenAPI document detailing paths, status codes, and schema formats.
*   **Manual testing**: Verify OpenAPI schema renders correctly in Swagger docs.
*   **Common mistakes**: Out-of-sync schemas.

### T10.2: PM Sync Payload Schemas
*   **Task ID**: `T10.2`
*   **Objective**: Define validation schemas representing PM Agent payloads.
*   **Files or assets**: `backend/app/schemas/sync.py`
*   **Inputs**: Ingestion specifications.
*   **Outputs**: Pydantic validation models.
*   **Dependencies**: `T10.1`.
*   **Acceptance criteria**: Data schemas accurately parse and validate payload properties.
*   **Manual testing**: Run unit test checks on payload parsing.
*   **Common mistakes**: Missing optional fields or wrong datetime constraints.

### T10.3: Sync Service
*   **Task ID**: `T10.3`
*   **Objective**: Implement core sync service to compile meeting records and map database structures to sync payload.
*   **Files or assets**: `backend/app/services/sync_service.py`
*   **Inputs**: Meeting ID.
*   **Outputs**: Structured sync payload object.
*   **Dependencies**: `T10.2`.
*   **Acceptance criteria**: Correctly gathers meeting, transcript, action item, decision, and risk records.
*   **Manual testing**: Construct payload for a test meeting and verify nested JSON structures.
*   **Common mistakes**: Incomplete relationship loading leading to empty fields.

### T10.4: PM Webhook Dispatcher
*   **Task ID**: `T10.4`
*   **Objective**: Implement HTTP client handling outgoing webhook requests to external PM services.
*   **Files or assets**: `backend/app/services/webhook_service.py`
*   **Inputs**: Webhook URL, sync payload.
*   **Outputs**: Webhook dispatch status.
*   **Dependencies**: `T10.3`.
*   **Acceptance criteria**: Safely sends payloads over HTTP POST and handles connection/timeout failures.
*   **Manual testing**: Dispatch payload to mock endpoint and verify request headers and payload.
*   **Common mistakes**: Swallowing socket errors without returning structured results.

### T10.5: Meeting Sync API Endpoint
*   **Task ID**: `T10.5`
*   **Objective**: Expose API endpoint to orchestrate full meeting sync pipeline from retrieval to webhook dispatch.
*   **Files or assets**: `backend/app/api/v1/meetings.py` (sync endpoint)
*   **Inputs**: Meeting ID, custom HTTP response wrapper.
*   **Outputs**: HTTP response status and sync response schema.
*   **Dependencies**: `T10.4`.
*   **Acceptance criteria**: Synchronizes successfully and returns HTTP 200 on success or HTTP 503 on dispatch failure.
*   **Manual testing**: Call sync endpoint with valid/invalid meeting IDs and test endpoints.
*   **Common mistakes**: Hardcoding webhook configurations instead of reading settings.

### T10.6: Sync Audit Log & Idempotency
*   **Task ID**: `T10.6`
*   **Objective**: Prevent duplicate webhook dispatches and record every synchronization attempt.
*   **Files or assets**: `backend/app/models/sync_log.py`, `backend/app/services/sync_log_service.py`, Alembic schema migrations.
*   **Inputs**: Payload hash, status indicators.
*   **Outputs**: Idempotent checks and log database writes.
*   **Dependencies**: `T10.5`.
*   **Acceptance criteria**: Duplicate sync requests are skipped; every attempt is logged as pending and updated to success/failed.
*   **Manual testing**: Run multiple sync calls on same meeting content and confirm subsequent attempts are skipped.
*   **Common mistakes**: Generating hash on mutable payload fields (e.g. timestamp of request).

---

## Milestone 11: MCP Server Bridge

### T11.1: MCP Server Bootstrap
*   **Task ID**: `T11.1`
*   **Objective**: Initialize standalone Node.js project with stdio transport configurations.
*   **Files or assets**: `mcp-server/package.json`, `mcp-server/server.js`
*   **Inputs**: npm package settings, pinned dependencies.
*   **Outputs**: Operational baseline stdio transport server.
*   **Dependencies**: None.
*   **Acceptance criteria**: The server runs cleanly on stdio, communicating via JSON-RPC protocol.
*   **Manual testing**: Start server and verify that it accepts connection handshake.
*   **Common mistakes**: Standard output pollution by other packages.

### T11.2: PostgreSQL Connection Support
*   **Task ID**: `T11.2`
*   **Objective**: Implement reusable, production-ready PostgreSQL connection pool.
*   **Files or assets**: `mcp-server/database.js`
*   **Inputs**: DATABASE_URL configuration.
*   **Outputs**: Database query helper.
*   **Dependencies**: `T11.1`, `T1.2`.
*   **Acceptance criteria**: Singleton connection pool resolves queries and closes cleanly.
*   **Manual testing**: Run select query script and verify results.
*   **Common mistakes**: Missing statement/connection timeout configurations.

### T11.3: MCP Tool Registration
*   **Task ID**: `T11.3`
*   **Objective**: Register MCP tools (`list_meetings` and `search_transcripts`) with input schema validations.
*   **Files or assets**: `mcp-server/server.js`, `mcp-server/tools/` metadata stubs.
*   **Inputs**: Input schemas, metadata fields.
*   **Outputs**: Registered tool definitions.
*   **Dependencies**: `T11.2`.
*   **Acceptance criteria**: Exposes tools correctly to client requests without stdout pollution.
*   **Manual testing**: Query `tools/list` over stdio and inspect returned JSON-RPC body.
*   **Common mistakes**: Mismatch between SDK request handlers and input formats.

### T11.4: list_meetings Tool Implementation
*   **Task ID**: `T11.4`
*   **Objective**: Implement database execution logic for list_meetings tool.
*   **Files or assets**: `mcp-server/tools/list_meetings.js`
*   **Inputs**: limit, offset, status arguments.
*   **Outputs**: Paginated list of meetings.
*   **Dependencies**: `T11.3`.
*   **Acceptance criteria**: Correctly executes parameterized SQL queries and validates inputs.
*   **Manual testing**: Query tool via inspector and verify JSON result.
*   **Common mistakes**: Using non-sargable string concatenation queries.

### T11.5: search_transcripts Tool Implementation
*   **Task ID**: `T11.5`
*   **Objective**: Implement database execution logic for search_transcripts tool.
*   **Files or assets**: `mcp-server/tools/search_transcripts.js`
*   **Inputs**: query, limit arguments.
*   **Outputs**: Search results matching keyword.
*   **Dependencies**: `T11.3`.
*   **Acceptance criteria**: Performs case-insensitive search on transcript database content.
*   **Manual testing**: Query term via inspector and confirm relevancy and speaker context.
*   **Common mistakes**: Unvalidated parameters or unindexed search columns.
