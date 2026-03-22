# Tasks: Gold Tier Backend - AI Orchestration Engine

**Input**: Design documents from `/specs/001-gold-tier-backend/`
**Prerequisites**: plan.md (✓), spec.md (✓), research.md (✓), data-model.md (✓), contracts/ (✓)
**Branch**: `001-gold-tier-backend`

**Tests**: Tests are OPTIONAL for this feature - included only for integration points and critical paths as specified in spec.md success criteria.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project structure with `src/`, `tests/` at repository root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per plan.md (src/api/, src/core/, src/models/, src/services/, src/workers/, src/events/, src/orchestration/, tests/)
- [ ] T002 Initialize Python 3.11+ project with requirements.txt (fastapi, celery, redis, sqlalchemy, psycopg2, pydantic, websockets, chromadb)
- [ ] T003 [P] Create .env.example with DATABASE_URL, REDIS_URL, JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS, LOG_LEVEL
- [ ] T004 [P] Setup .gitignore for Python project (venv/, __pycache__/, .env, *.pyc, .pytest_cache/)
- [ ] T005 [P] Create docker/ directory with .dockerignore
- [ ] T006 [P] Create scripts/ directory with run_worker.sh, run_api.sh, migrate.sh

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T007 [P] Create src/core/config.py with Pydantic settings class (database, redis, jwt, logging config)
- [ ] T008 [P] Create src/core/security.py with JWT token generation/validation functions
- [ ] T009 [P] Create src/core/exceptions.py with custom exceptions (JobNotFoundError, InvalidTransitionError, UnauthorizedError)
- [ ] T010 [P] Create src/utils/logging.py with structured JSON logging formatter
- [ ] T011 [P] Create src/utils/retry.py with exponential backoff utility (3 retries, 1min/5min/15min)
- [ ] T012 Create src/models/base.py with SQLAlchemy Base class and database session factory
- [ ] T013 Create database migration script src/models/migrate.py using Alembic
- [ ] T014 [P] Create src/middleware/auth.py with JWT authentication middleware and role-based dependencies
- [ ] T015 [P] Create src/middleware/logging.py with request/response logging middleware
- [ ] T016 Create src/api/main.py with FastAPI app initialization, CORS, middleware registration
- [ ] T017 [P] Create docker/docker-compose.yml with postgres, redis services (development)
- [ ] T018 [P] Create docker/Dockerfile for API and worker containers
- [ ] T019 Create src/events/event_bus.py with Redis pub/sub event bus implementation
- [ ] T020 Create src/events/types.py with event type enums (JobQueued, StageCompleted, PlanPendingApproval, etc.)
- [ ] T021 Create src/events/handlers.py with event handler registry

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Submit Task for AI Plan Generation (Priority: P1) 🎯 MVP

**Goal**: Users can submit tasks via API and receive job ID for tracking. Task enters async processing queue.

**Independent Test**: User can POST /api/v1/jobs with task_description and receive job_id, status=queued, submitted_at. Job is immediately visible via GET /api/v1/jobs/{job_id}.

### Models for User Story 1

- [ ] T022 [P] [US1] Create User model in src/models/user.py (id, email, role ENUM, created_at, last_login_at)
- [ ] T023 [P] [US1] Create Job model in src/models/job.py (id, task_description, status ENUM, progress_percentage, submitted_by FK, submitted_at, completed_at, parent_job_id FK self-ref)
- [ ] T024 [P] [US1] Create JobStatus and UserRole enums in src/models/enums.py

### Services for User Story 1

- [ ] T025 [US1] Create JobService in src/services/job_service.py (create_job, get_job, list_jobs, validate_task_description)
- [ ] T026 [US1] Create UserService in src/services/user_service.py (get_user_by_id, get_user_by_email, create_user)
- [ ] T027 [US1] Create idempotency check in src/services/idempotency_service.py (Redis-based deduplication with 24h TTL)

### API Routes for User Story 1

- [ ] T028 [P] [US1] Create Pydantic schemas in src/schemas/job.py (JobSubmission, JobQueuedResponse, JobDetail, JobSummary)
- [ ] T029 [US1] Implement POST /api/v1/jobs in src/api/routes/jobs.py (validate, create job, publish JobQueued event, return job_id)
- [ ] T030 [US1] Implement GET /api/v1/jobs/{job_id} in src/api/routes/jobs.py (return job status and details)
- [ ] T031 [US1] Implement GET /api/v1/jobs in src/api/routes/jobs.py (list user's jobs with pagination, filtering by status)
- [ ] T032 [US1] Add input validation (task_description min 10 chars, max 10000 chars)

### Celery Worker Setup for User Story 1

- [ ] T033 Create src/workers/celery_app.py with Celery configuration (Redis broker, task routes, retry config)
- [ ] T034 Create src/workers/tasks.py with base Celery task class (idempotency check, error handling)
- [ ] T035 [P] [US1] Create job submission task in src/workers/tasks.py (receive job_id, validate, start pipeline)

### Tests for User Story 1 (OPTIONAL - Critical Path Only)

- [ ] T036 [P] [US1] Create contract test for POST /api/v1/jobs in tests/contract/test_jobs_api.py (valid request, invalid request, auth required)
- [ ] T037 [US1] Create integration test for job submission flow in tests/integration/test_job_submission.py (submit → queued → processing)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently
- Users can submit tasks and receive job IDs
- Jobs are queued and status is trackable
- Idempotency prevents duplicate submissions

---

## Phase 4: User Story 2 - Monitor Real-Time Processing Progress (Priority: P2)

**Goal**: Users receive real-time updates as jobs progress through 4 pipeline stages via WebSocket.

**Independent Test**: User can connect to WS /api/v1/ws/jobs and receive push notifications for stage_completed, status_changed, progress_update events in real-time (<1s latency).

### Models for User Story 2

- [ ] T038 [P] [US2] Create PipelineStage model in src/models/pipeline_stage.py (id, job_id FK, stage_type ENUM, status ENUM, input_data JSONB, output_data JSONB, started_at, completed_at, error_message, retry_count, timeout_seconds)
- [ ] T039 [P] [US2] Create PipelineStageType and PipelineStageStatus enums in src/models/enums.py (extend existing)

### Pipeline Service for User Story 2

- [ ] T040 [US2] Create PipelineService in src/services/pipeline_service.py (start_pipeline, complete_stage, trigger_next_stage, handle_stage_failure)
- [ ] T041 [US2] Implement 4-stage pipeline orchestration (task_analysis → plan_creation → risk_assessment → final_output)
- [ ] T042 [US2] Implement stage timeout handling (30s timeout per stage, graceful degradation)
- [ ] T043 [US2] Implement retry logic with exponential backoff (max 3 retries, 1min/5min/15min)

### Celery Worker Stages for User Story 2

- [ ] T044 [P] [US2] Create task_analysis worker in src/workers/stages/task_analysis.py (parse task, extract requirements, publish progress)
- [ ] T045 [P] [US2] Create plan_creation worker in src/workers/stages/plan_creation.py (generate structured plan, publish progress)
- [ ] T046 [P] [US2] Create risk_assessment worker in src/workers/stages/risk_assessment.py (evaluate risks, severity scores, mitigations)
- [ ] T047 [P] [US2] Create final_output worker in src/workers/stages/final_output.py (assemble final deliverable, mark job completed)
- [ ] T048 [US2] Implement progress publishing to Redis pub/sub in each worker (job_id, stage_type, progress_percentage, timestamp)

### WebSocket for User Story 2

- [ ] T049 [P] [US2] Create WebSocket manager in src/api/routes/websocket.py (connection handler, authentication, broadcast)
- [ ] T050 [US2] Implement WS /api/v1/ws/jobs endpoint in src/api/routes/websocket.py (JWT auth, subscribe to Redis pub/sub, forward to client)
- [ ] T051 [US2] Implement event filtering by job_id (users only receive events for their jobs)
- [ ] T052 [US2] Implement reconnection support with last event tracking

### Event Handlers for User Story 2

- [ ] T053 [US2] Create StageStarted handler in src/events/handlers.py (update stage status to running, publish WebSocket event)
- [ ] T054 [US2] Create StageCompleted handler in src/events/handlers.py (update stage status, store output, trigger next stage, publish WebSocket event)
- [ ] T055 [US2] Create StageFailed handler in src/events/handlers.py (increment retry_count, schedule retry or mark failed, publish WebSocket event)

### Tests for User Story 2 (OPTIONAL - Critical Path Only)

- [ ] T056 [P] [US2] Create WebSocket integration test in tests/integration/test_websocket.py (connect, receive events, disconnect, reconnect)
- [ ] T057 [US2] Create pipeline stage test in tests/integration/test_pipeline.py (stage1 → stage2 → stage3 → stage4 completion flow)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently
- Users can submit tasks (US1)
- Users receive real-time progress updates through all 4 stages (US2)
- Pipeline handles retries and timeouts correctly

---

## Phase 5: User Story 3 - Review and Approve Generated Plans (Priority: P3)

**Goal**: Approvers can review AI-generated plans and approve/reject with comments. Rejected plans trigger regeneration.

**Independent Test**: Approver can GET /api/v1/plans/{plan_id} to view full plan, POST /api/v1/plans/{plan_id}/approve to approve, POST /api/v1/plans/{plan_id}/reject to reject with comments. Submitter role is denied approval actions.

### Models for User Story 3

- [ ] T058 [P] [US3] Create Plan model in src/models/plan.py (id, job_id FK unique, version, task_analysis JSONB, recommended_actions JSONB, risk_assessment JSONB, approval_status ENUM, created_at)
- [ ] T059 [P] [US3] Create ApprovalEvent model in src/models/approval_event.py (id, plan_id FK, decision ENUM, approver_id FK, decided_at, comments TEXT)
- [ ] T060 [P] [US3] Create ApprovalStatus and ApprovalDecision enums in src/models/enums.py (extend existing)

### Services for User Story 3

- [ ] T061 [US3] Create PlanService in src/services/plan_service.py (create_plan_from_pipeline, get_plan, update_approval_status)
- [ ] T062 [US3] Create ApprovalService in src/services/approval_service.py (approve_plan, reject_plan, validate_approver_role, log_approval_event)
- [ ] T063 [US3] Implement plan regeneration on rejection (create new job with parent_job_id link, copy feedback)
- [ ] T064 [US3] Create NotificationService in src/services/notification_service.py (send_email for approval required, completion, failures)
- [ ] T064b [P] [US3] Implement EmailService in src/services/email_service.py (SMTP/SendGrid integration, email templates for critical events)

### API Routes for User Story 3

- [ ] T065 [P] [US3] Create Pydantic schemas in src/schemas/plan.py (PlanDetail, ApprovalRequest, ApprovalResponse, RejectionRequest, RejectionResponse)
- [ ] T066 [US3] Implement GET /api/v1/plans/{plan_id} in src/api/routes/plans.py (return plan with approval status, role-based access)
- [ ] T067 [US3] Implement POST /api/v1/plans/{plan_id}/approve in src/api/routes/approvals.py (Approver role required, validate status, create ApprovalEvent, publish PlanApproved event)
- [ ] T068 [US3] Implement POST /api/v1/plans/{plan_id}/reject in src/api/routes/approvals.py (Approver role required, comments required, create ApprovalEvent, trigger regeneration, publish PlanRejected event)
- [ ] T069 [US3] Add role-based authorization (only Approver role can approve/reject, return 403 for Submitter)

### Event Handlers for User Story 3

- [ ] T070 [US3] Create PlanPendingApproval handler in src/events/handlers.py (update plan status, send email notification to approvers)
- [ ] T071 [US3] Create PlanApproved handler in src/events/handlers.py (log decision, notify submitter, enable execution)
- [ ] T072 [US3] Create PlanRejected handler in src/events/handlers.py (log decision, create regeneration job, notify submitter)

### Agent Execution Logging for User Story 3

- [ ] T073 [P] [US3] Create AgentExecutionLog model in src/models/agent_execution_log.py (id, agent_type ENUM, job_id FK, stage_id FK, input JSONB, output JSONB, duration_ms, status ENUM, executed_at)
- [ ] T074 [P] [US3] Create AgentType and AgentExecutionStatus enums in src/models/enums.py (extend existing)
- [ ] T075 [US3] Add agent execution logging in each worker stage (log input, output, duration, status)

### Tests for User Story 3 (OPTIONAL - Critical Path Only)

- [ ] T076 [P] [US3] Create approval workflow test in tests/integration/test_approval_workflow.py (submit → process → approve → verify status)
- [ ] T077 [US3] Create rejection and regeneration test in tests/integration/test_rejection.py (reject with comments → new job created → parent_job_id linked)
- [ ] T078 [US3] Create role-based access test in tests/contract/test_approvals_api.py (Approver can approve, Submitter gets 403)

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently
- Users can submit tasks and track progress (US1, US2)
- Approvers can review and approve/reject plans (US3)
- Rejected plans automatically regenerate with feedback linkage

---

## Phase 6: User Story 4 - Trace Complete Processing History (Priority: P4)

**Goal**: Users can view complete audit trail showing all pipeline stages, agent executions, and approval decisions.

**Independent Test**: User can GET /api/v1/jobs/{job_id}/history and receive complete job lineage with all stages (inputs/outputs), agent logs, approval events, and parent job reference.

### API Routes for User Story 4

- [ ] T079 [P] [US4] Create Pydantic schemas in src/schemas/history.py (JobHistory, PipelineStageDetail, AgentExecutionLog, ApprovalEvent)
- [ ] T080 [US4] Implement GET /api/v1/jobs/{job_id}/history in src/api/routes/jobs.py (aggregate job, stages, agent logs, approval events, parent job)
- [ ] T081 [US4] Add authorization check (user can only view their own job history)

### Audit Service for User Story 4

- [ ] T082 [US4] Create AuditService in src/services/audit_service.py (get_job_history, get_approval_history_by_user, get_retry_analysis)
- [ ] T083 [US4] Implement state transition logging (track all job status changes with timestamps)

### Metrics Endpoint (Approver Only)

- [ ] T084 [P] [US4] Create Pydantic schemas in src/schemas/metrics.py (QueueMetrics)
- [ ] T085 [US4] Implement GET /api/v1/metrics/queue in src/api/routes/metrics.py (queued_count, processing_count, completed_today, failed_today, avg_completion_time, pending_approval_count)
- [ ] T086 [US4] Add Approver role-only authorization for metrics endpoint

### Tests for User Story 4 (OPTIONAL - Critical Path Only)

- [ ] T087 [P] [US4] Create audit trail test in tests/integration/test_audit_trail.py (complete job → verify all stages logged → verify agent logs → verify approval events)
- [ ] T088 [US4] Create history API test in tests/contract/test_history_api.py (valid job returns complete history, unauthorized user gets 403)

**Checkpoint**: All 4 user stories should now be independently functional
- Complete audit trail accessible for any job
- All pipeline stages, agent executions, and approval decisions traceable

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories, production readiness

### Documentation

- [ ] T089 [P] Create quickstart.md with 5-minute setup guide, API testing examples, troubleshooting section
- [ ] T090 [P] Create README.md with feature overview, architecture diagram, deployment instructions
- [ ] T091 [P] Add API documentation via FastAPI Swagger UI (/docs) and ReDoc (/redoc)

### Production Deployment

- [ ] T092 [P] Create docker/docker-compose.prod.yml with api, worker, worker_beat, postgres, redis services (align with plan.md structure)
- [ ] T093 [P] Add health check endpoints (/health, /ready) in src/api/routes/health.py
- [ ] T094 [P] Create production deployment checklist in docs/deployment-checklist.md (security, observability, DR)
- [ ] T095 [P] Add environment-specific configuration (development, staging, production)

### Observability

- [ ] T096 [P] Add structured JSON logging for production in src/utils/logging.py
- [ ] T097 [P] Create Grafana dashboard configuration for queue depth, job completion rate, failure rate, retry success rate
- [ ] T098 [P] Add alert rules configuration (high failure rate >10%, queue backlog >50, approval timeout >24h)
- [ ] T113 [P] Create retry analytics endpoint in src/api/routes/analytics.py (track retry counts, success rates, failure patterns)

### Data Retention

- [ ] T099 [P] Create data retention script scripts/enforce_retention.py (delete jobs older than 90 days)
- [ ] T100 [P] Schedule retention job with Celery Beat (daily at 2 AM)

### Security Hardening

- [ ] T101 [P] Add rate limiting middleware in src/middleware/rate_limit.py (100 requests/minute per user)
- [ ] T102 [P] Add input sanitization for all API endpoints
- [ ] T103 [P] Configure CORS for allowed origins only
- [ ] T104 [P] Add SQL injection protection via SQLAlchemy parameterized queries

### Performance Optimization

- [ ] T105 [P] Add database indexes per data-model.md (job status, submitted_by, stage_type, approval_status)
- [ ] T106 [P] Add Redis caching for frequently accessed job status
- [ ] T107 [P] Optimize database queries with eager loading for job history endpoint
- [ ] T114 [P] Create load testing script tests/performance/test_load.py (validate SC-001: 2s submission, SC-002: 5min completion, SC-003: 1s updates, SC-008: 1s history)
- [ ] T115 [P] Add performance profiling middleware in src/middleware/profiling.py (track request latency, log slow queries)

### Final Validation

- [ ] T108 Run full integration test suite (pytest tests/integration/)
- [ ] T109 Run contract tests against OpenAPI spec (tests/contract/test_openapi.py)
- [ ] T110 Validate quickstart.md steps end-to-end
- [ ] T111 Performance test with 100 concurrent jobs
- [ ] T112 Security scan for vulnerabilities (pip audit, bandit)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 (pipeline processes jobs from US1)
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Depends on pipeline completion (US2) to have plans to approve
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Depends on all previous stories for complete audit trail

### Within Each User Story

1. Models (marked [P] can run in parallel)
2. Services (depend on models)
3. API routes (depend on services)
4. Integration (depends on all above)
5. Tests (if included, should fail before implementation)

### Critical Path (MVP - User Story 1 Only)

```
T001-T006 (Setup) → T007-T021 (Foundational) → T022-T037 (US1)
Total: 37 tasks for MVP
```

### Parallel Opportunities

**Setup Phase** (all [P] tasks):
- T003, T004, T005, T006 can run in parallel

**Foundational Phase**:
- T007, T008, T009, T010, T011, T014, T015, T017, T018 can run in parallel (utilities, middleware, Docker)
- T012, T013 must complete before user story models
- T016, T019, T020, T021 must complete before user story services

**User Story 1**:
- T022, T023, T024 (models) can run in parallel
- T028 (schemas) can run in parallel with models
- T036 (contract test) can run in parallel before implementation

**User Story 2**:
- T038, T039 (models) can run in parallel
- T044, T045, T046, T047 (worker stages) can run in parallel
- T049 (WebSocket manager) can run in parallel with workers

**User Story 3**:
- T058, T059, T060 (models) can run in parallel
- T073, T074, T075 (agent logging) can run in parallel
- T076, T077, T078 (tests) can run in parallel

**User Story 4**:
- T079, T084 (schemas) can run in parallel
- T087, T088 (tests) can run in parallel

**Cross-Story Parallel**:
- Once Foundational phase completes, US1, US2, US3, US4 can start in parallel with different developers

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "T022 [P] [US1] Create User model in src/models/user.py"
Task: "T023 [P] [US1] Create Job model in src/models/job.py"
Task: "T024 [P] [US1] Create JobStatus and UserRole enums in src/models/enums.py"
Task: "T028 [P] [US1] Create Pydantic schemas in src/schemas/job.py"

# Launch contract test in parallel:
Task: "T036 [P] [US1] Create contract test for POST /api/v1/jobs in tests/contract/test_jobs_api.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T021) **⚠️ CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T022-T037)
4. **STOP and VALIDATE**: 
   - Test: Submit task via POST /api/v1/jobs
   - Verify: Receive job_id, status=queued
   - Test: GET /api/v1/jobs/{job_id}
   - Verify: Status visible, idempotency works
5. Deploy/demo if ready

### Incremental Delivery

1. **Foundation** (T001-T021): Setup + Foundational → Foundation ready
2. **MVP** (T022-T037): Add User Story 1 → Test independently → Deploy/Demo
3. **Real-time** (T038-T057): Add User Story 2 → Test independently → Deploy/Demo
4. **Approval** (T058-T078): Add User Story 3 → Test independently → Deploy/Demo
5. **Audit** (T079-T088): Add User Story 4 → Test independently → Deploy/Demo
6. **Production** (T089-T112): Polish & hardening

Each phase adds value without breaking previous phases.

### Parallel Team Strategy

With 4 developers:

1. **All developers**: Complete Setup + Foundational together (T001-T021)
2. **Once Foundational is done**:
   - Developer A: User Story 1 (T022-T037) - Task submission
   - Developer B: User Story 2 (T038-T057) - Real-time monitoring
   - Developer C: User Story 3 (T058-T078) - Approval workflow
   - Developer D: User Story 4 (T079-T088) - Audit trail + metrics
3. **All developers**: Polish phase (T089-T112) together

Stories complete and integrate independently. Integration points:
- US2 integrates with US1 (pipeline processes jobs from US1)
- US3 integrates with US2 (approves plans from completed pipeline)
- US4 integrates with all (aggregates data from US1, US2, US3)

---

## Task Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 6 |
| Phase 2 | Foundational | 15 |
| Phase 3 | User Story 1 (MVP) | 16 |
| Phase 4 | User Story 2 | 20 |
| Phase 5 | User Story 3 | 22 (+1 EmailService) |
| Phase 6 | User Story 4 | 10 |
| Phase 7 | Polish | 28 (+4 new: T113 analytics, T114-T115 performance, T092 alignment) |
| **Total** | **All phases** | **117** |

### MVP Scope (User Story 1 Only)
- **Tasks**: T001-T037 (37 tasks)
- **Deliverable**: Task submission with async processing and status tracking
- **Independent Test**: POST /api/v1/jobs → GET /api/v1/jobs/{job_id}

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **CRITICAL**: Complete Foundational phase (T007-T021) before starting ANY user story
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Quick Reference: File Creation Order

**Foundation First**:
1. src/core/config.py, security.py, exceptions.py
2. src/utils/logging.py, retry.py
3. src/models/base.py, enums.py
4. src/middleware/auth.py, logging.py
5. src/events/event_bus.py, types.py, handlers.py
6. src/api/main.py

**Then User Story 1**:
1. src/models/user.py, job.py
2. src/services/job_service.py, user_service.py, idempotency_service.py
3. src/schemas/job.py
4. src/api/routes/jobs.py
5. src/workers/celery_app.py, tasks.py
