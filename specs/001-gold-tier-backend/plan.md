# Implementation Plan: Gold Tier Backend - AI Orchestration Engine

**Branch**: `001-gold-tier-backend` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Transform Silver tier backend into Gold tier with background processing, multi-stage AI pipelines, real-time updates, human approval workflow, and multi-agent orchestration

## Summary

Build a semi-autonomous AI orchestration engine with event-driven architecture using FastAPI, Redis event queue, Celery workers, and PostgreSQL. The system processes tasks through a 4-stage AI pipeline (Task Analysis → Plan Creation → Risk Assessment → Final Output), requires human approval before execution, provides real-time progress updates via WebSocket, and maintains complete audit trails. Implements role-based access control (Submitter/Approver) with 90-day retention.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Celery, Redis, PostgreSQL, SQLAlchemy, Pydantic, WebSockets
**Storage**: PostgreSQL (persistent data), Redis (event queue, caching), Chroma (vector memory)
**Testing**: pytest, pytest-asyncio, pytest-cov
**Target Platform**: Linux server, Docker containerized
**Project Type**: Backend API with background workers
**Performance Goals**: 100 concurrent users, 95% tasks complete within 5 minutes, <2s submission response, <1s real-time updates
**Constraints**: <30s AI timeout per stage, 3 retries with exponential backoff, non-blocking HTTP threads, idempotent job processing
**Scale/Scope**: 100 concurrent job processing sessions, 90-day data retention, multi-channel integrations (Gmail, WhatsApp, Local Files)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Justification |
|-----------|--------|---------------|
| Test-First (TDD) | ✅ PASS | All components will have unit tests before implementation |
| CLI Interface | ✅ PASS | System exposes health checks, job submission via CLI-compatible endpoints |
| Observability | ✅ PASS | Structured logging, job metrics, queue monitoring endpoints |
| Simplicity (YAGNI) | ✅ PASS | Single-tenant, no Kubernetes, focused on core orchestration |
| Integration Testing | ✅ PASS | Contract tests for API, pipeline integration tests |

**GATE RESULT**: ✅ PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/001-gold-tier-backend/
├── plan.md              # This file
├── research.md          # Phase 0 output (completed)
├── data-model.md        # Phase 1 output (completed)
├── quickstart.md        # Phase 1 output (completed)
├── contracts/           # Phase 1 output (completed)
│   └── openapi.yaml
└── tasks.md             # Phase 2 output (pending)
```

### Source Code (repository root)

```text
src/
├── api/
│   ├── routes/
│   │   ├── jobs.py
│   │   ├── plans.py
│   │   ├── approvals.py
│   │   └── websocket.py
│   ├── schemas/
│   │   ├── job.py
│   │   ├── plan.py
│   │   └── approval.py
│   └── middleware/
│       ├── auth.py
│       └── logging.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── exceptions.py
├── models/
│   ├── job.py
│   ├── pipeline_stage.py
│   ├── plan.py
│   ├── approval_event.py
│   ├── agent_execution_log.py
│   └── user.py
├── services/
│   ├── job_service.py
│   ├── pipeline_service.py
│   ├── approval_service.py
│   ├── notification_service.py
│   └── memory_service.py
├── workers/
│   ├── celery_app.py
│   ├── tasks.py
│   └── stages/
│       ├── task_analysis.py
│       ├── plan_creation.py
│       ├── risk_assessment.py
│       └── final_output.py
├── events/
│   ├── event_bus.py
│   ├── handlers.py
│   └── types.py
├── orchestration/
│   ├── orchestrator.py
│   ├── agents/
│   │   ├── task_analyzer.py
│   │   ├── planner_agent.py
│   │   └── risk_agent.py
│   └── state_machine.py
└── utils/
    ├── logging.py
    └── retry.py

tests/
├── contract/
│   └── api_contracts_test.py
├── integration/
│   ├── pipeline_test.py
│   ├── approval_workflow_test.py
│   └── websocket_test.py
├── unit/
│   ├── services/
│   ├── workers/
│   └── models/
└── conftest.py

docker/
├── Dockerfile
├── docker-compose.yml
└── docker-compose.prod.yml

scripts/
├── run_worker.sh
├── run_api.sh
├── migrate.sh
└── create_user.py
```

**Structure Decision**: Single project with clean architecture separation (api/, core/, models/, services/, workers/, events/, orchestration/, utils/). Background workers in dedicated workers/ module using Celery. Event-driven communication via events/ module.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Event bus + Celery | Decoupled real-time updates + background processing | Direct calls would block HTTP threads and prevent real-time progress |
| State machine | Complex approval workflow with multiple states | Simple status field insufficient for audit trail and transitions |
| Multi-agent orchestration | Specialized AI processing per pipeline stage | Single AI call cannot provide traceable, stage-specific outputs |

---

## Phase 0: Research & Discovery

### Unknowns to Resolve

1. **FastAPI WebSocket integration with Celery workers**
   - Research: Best practices for pushing Celery task progress to WebSocket clients
   - Pattern: Celery signals → Redis pub/sub → WebSocket broadcast

2. **Multi-stage pipeline state persistence**
   - Research: Efficient storage of intermediate pipeline stage outputs
   - Pattern: JSONB columns for stage outputs, foreign keys for lineage

3. **Idempotent job processing with Celery**
   - Research: Preventing duplicate job execution on retry
   - Pattern: Task idempotency keys, Redis-based deduplication

4. **Role-based access control in FastAPI**
   - Research: Implementing Submitter/Approver roles
   - Pattern: JWT claims with role-based dependencies

5. **Vector memory integration for AI context**
   - Research: Chroma vs Supabase Vector for persistent AI memory
   - Pattern: Embedding storage for task-plan relationships

6. **Multi-channel watcher architecture (Gmail, WhatsApp, Local Files)**
   - Research: Always-on watchers integration with event bus
   - Pattern: Separate watcher services publishing to Redis event queue

### Research Dispatch

**Task 1**: Research FastAPI WebSocket + Celery progress reporting patterns  
**Task 2**: Research idempotent task execution strategies in Celery  
**Task 3**: Research pipeline state machine implementations for audit trails  
**Task 4**: Research RBAC patterns in FastAPI with JWT  
**Task 5**: Research Chroma vs Supabase Vector for AI memory persistence  
**Task 6**: Research event-driven watcher architecture for Gmail/WhatsApp/FileSystem

**Status**: ✅ Complete - See `research.md` for detailed findings

---

## Phase 1: Design & Contracts

### Data Model Design

**Status**: ✅ Complete - See `data-model.md`

**Entities** (6 total):
1. **Job** - Task submission with status tracking and parent linkage for regenerations
2. **PipelineStage** - 4-stage pipeline with JSONB inputs/outputs, timeout tracking
3. **Plan** - Versioned AI output with approval status
4. **ApprovalEvent** - Human decision logging with comments
5. **AgentExecutionLog** - Agent execution audit trail
6. **User** - Role-based access (Submitter/Approver)

**Key Relationships**:
- Job → PipelineStage (1:N)
- Job → Plan (1:1)
- Plan → ApprovalEvent (1:N)
- User → Job (1:N submissions)
- User → ApprovalEvent (1:N decisions)
- Job → Job (self-referential for regenerations)

### API Contracts

**Status**: ✅ Complete - See `contracts/openapi.yaml`

**REST Endpoints** (7 total):
1. `POST /api/v1/jobs` - Submit task
2. `GET /api/v1/jobs/{job_id}` - Get job status
3. `GET /api/v1/jobs/{job_id}/history` - Get audit trail
4. `GET /api/v1/plans/{plan_id}` - Get plan details
5. `POST /api/v1/plans/{plan_id}/approve` - Approve plan
6. `POST /api/v1/plans/{plan_id}/reject` - Reject plan
7. `GET /api/v1/metrics/queue` - Queue metrics

**WebSocket Endpoint**:
- `WS /api/v1/ws/jobs` - Real-time job progress updates

**Authentication**: JWT Bearer token with role claims

### Quickstart Guide

**Status**: ✅ Complete - See `quickstart.md`

**Contents**:
- Prerequisites and installation
- 5-minute quick start guide
- Development workflow (tests, code style, migrations)
- API testing guide with examples
- Troubleshooting common issues
- Production deployment checklist

---

## Phase 2: Background Worker Design

### Celery Worker Architecture

**Worker Pools**:
- **Default Pool**: Handles task analysis, plan creation (CPU-intensive)
- **IO Pool**: Handles notifications, external API calls
- **Risk Assessment Pool**: Handles security-sensitive operations

**Task Routing**:
```python
task_routes = {
    'src.workers.stages.task_analysis': {'queue': 'default'},
    'src.workers.stages.plan_creation': {'queue': 'default'},
    'src.workers.stages.risk_assessment': {'queue': 'risk'},
    'src.workers.stages.final_output': {'queue': 'default'},
    'src.services.notification_service.send_email': {'queue': 'io'},
}
```

**Retry Configuration**:
```python
task_annotations = {
    '*': {
        'max_retries': 3,
        'exponential_backoff': [60, 300, 900],  # 1min, 5min, 15min
        'autoretry_for': (ConnectionError, TimeoutError),
    }
}
```

### Worker Lifecycle

1. **Startup**:
   - Connect to Redis broker
   - Register task handlers
   - Initialize database connections
   - Load AI model contexts

2. **Task Execution**:
   - Receive task from queue
   - Validate idempotency key (prevent duplicates)
   - Execute stage logic with 30s timeout
   - Publish progress events to Redis pub/sub
   - Persist stage output to PostgreSQL
   - Trigger next stage or complete job

3. **Shutdown**:
   - Complete in-progress tasks (warm shutdown)
   - Close database connections
   - Disconnect from Redis

---

## Phase 3: Event Orchestration Design

### Event Bus Architecture

**Event Types**:
- `JobQueued`: Job submitted, entered queue
- `StageStarted`: Pipeline stage began execution
- `StageCompleted`: Pipeline stage finished successfully
- `StageFailed`: Pipeline stage failed (with retry info)
- `JobCompleted`: All stages complete
- `JobFailed`: Job permanently failed after retries
- `PlanPendingApproval`: Plan ready for human review
- `PlanApproved`: Plan approved by approver
- `PlanRejected`: Plan rejected by approver
- `ApprovalTimeout`: Approval not received within SLA

**Event Flow**:
```
Job Submission → JobQueued → [Redis Event Bus] → Celery Worker
Celery Worker → StageStarted → StageCompleted → [Redis Pub/Sub] → WebSocket
Celery Worker → JobCompleted → PlanPendingApproval → [Redis Event Bus] → Notification Service
Notification Service → Email → Approver
Approver → PlanApproved → [Redis Event Bus] → Audit Log
```

### Event Handlers

```python
event_handlers = {
    JobQueued: handle_job_queued,      # Log, notify user
    StageCompleted: handle_stage_complete,  # Update progress, trigger next stage
    StageFailed: handle_stage_failed,   # Retry logic, escalate if max retries
    PlanPendingApproval: handle_approval_required,  # Send email notification
    PlanApproved: handle_plan_approved, # Log, enable execution
    PlanRejected: handle_plan_rejected, # Log, create regeneration job
}
```

---

## Phase 4: Approval Workflow Architecture

### Approval State Machine

```
┌─────────────┐
│   DRAFT     │  (Plan being generated)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│PENDING_     │  (Waiting for human decision)
│APPROVAL     │
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       │              │              │
       ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│  APPROVED   │ │  REJECTED   │ │  TIMEOUT    │
└─────────────┘ └──────┬──────┘ └─────────────┘
                       │
                       ▼
                ┌─────────────┐
                │REGENERATION │  (New job created with feedback)
                └─────────────┘
```

**State Transition Rules**:
- DRAFT → PENDING_APPROVAL: Automatic when all 4 stages complete
- PENDING_APPROVAL → APPROVED: Approver decision
- PENDING_APPROVAL → REJECTED: Approver decision with comments
- PENDING_APPROVAL → TIMEOUT: Configurable SLA (e.g., 24 hours)
- REJECTED → REGENERATION: Automatic, creates new job with parent_job_id link

### Approval Service

**Responsibilities**:
- Track pending approvals and SLA deadlines
- Send reminder notifications (e.g., 1 hour before timeout)
- Enforce role-based approval (only Approver role)
- Log all approval events with comments
- Trigger regeneration on rejection

---

## Phase 5: Memory Layer Design

### Vector Memory Architecture

**Purpose**: Store embeddings of task-plan pairs for contextual AI processing

**Implementation** (Chroma):
```python
# Collection structure
collections = {
    'task_embeddings': 'Embeddings of task descriptions',
    'plan_embeddings': 'Embeddings of generated plans',
    'feedback_embeddings': 'Embeddings of approval feedback',
}

# Metadata stored with embeddings
metadata = {
    'job_id': UUID,
    'user_id': UUID,
    'timestamp': datetime,
    'approval_status': str,
    'domain': str,  # e.g., 'sales', 'engineering', 'marketing'
}
```

**Query Patterns**:
- Similarity search: "Find plans similar to this task"
- Context retrieval: "Get historical feedback for similar tasks"
- Pattern recognition: "What tasks led to rejected plans?"

---

## Phase 6: Logging & Audit Architecture

### Structured Logging

**Log Format** (JSON):
```json
{
  "timestamp": "2026-03-02T10:00:00Z",
  "level": "INFO",
  "service": "api|worker|watcher",
  "job_id": "uuid",
  "stage_id": "uuid",
  "event": "stage_completed",
  "duration_ms": 1234,
  "user_id": "uuid",
  "correlation_id": "uuid"
}
```

**Log Aggregation**:
- Development: Console output with color
- Production: Structured JSON → Log aggregator (e.g., ELK, Datadog)

### Audit Trail

**What is Audited**:
- All job submissions (who, what, when)
- All pipeline stage transitions (timestamps, outputs)
- All approval decisions (who, decision, comments)
- All retry attempts (reason, backoff duration)
- All role-based access denials

**Audit Query API**:
- `GET /api/v1/jobs/{job_id}/history` - Complete job lineage
- `GET /api/v1/audit/approvals?user_id={}` - Approval history by user
- `GET /api/v1/audit/retries?status=failed` - Failed retry analysis

---

## Phase 7: Production Deployment Strategy

### Docker Compose (Production)

```yaml
version: '3.8'
services:
  api:
    build: .
    command: uvicorn src.api.main:app --host 0.0.0.0 --workers 4
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/gold_tier
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - redis
    ports:
      - "8000:8000"
    restart: unless-stopped

  worker:
    build: .
    command: celery -A src.workers.celery_app worker --loglevel=info --pool=solo --concurrency=4
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/gold_tier
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  worker_beat:
    build: .
    command: celery -A src.workers.celery_app beat --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/gold_tier
      - REDIS_URL=redis://redis:6379/0
    restart: unless-stopped

  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=gold_tier
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

### Deployment Checklist

**Pre-Deployment**:
- [ ] Environment variables configured (DATABASE_URL, REDIS_URL, JWT_SECRET)
- [ ] Database migrations tested on staging
- [ ] Celery worker concurrency tuned for CPU/memory
- [ ] Rate limiting configured for API endpoints
- [ ] SSL/TLS certificates for WebSocket connections
- [ ] Monitoring dashboards configured (queue depth, job completion rate)
- [ ] Alert rules configured (high failure rate, queue backlog)

**Security**:
- [ ] JWT secrets rotated and stored in secrets manager
- [ ] Database credentials use least-privilege roles
- [ ] Redis requires authentication
- [ ] API rate limiting enabled (prevent DoS)
- [ ] CORS configured for allowed origins
- [ ] Input validation on all endpoints (Pydantic)

**Observability**:
- [ ] Structured logging enabled (JSON format)
- [ ] Log aggregation pipeline configured
- [ ] Metrics exported (Prometheus/Datadog)
- [ ] Distributed tracing enabled (OpenTelemetry)
- [ ] Health check endpoints functional (/health, /ready)

**Disaster Recovery**:
- [ ] Database backups scheduled (daily full, hourly incremental)
- [ ] Redis persistence enabled (RDB snapshots)
- [ ] Runbook documented for common failures
- [ ] Rollback procedure tested
- [ ] On-call escalation path defined

---

## Constitution Check (Post-Design)

*Re-evaluate after Phase 1 design completion*

| Principle | Status | Notes |
|-----------|--------|-------|
| Test-First (TDD) | ✅ PASS | Unit tests planned for all services, workers, models |
| CLI Interface | ✅ PASS | Health checks, job submission via curl-compatible endpoints |
| Observability | ✅ PASS | Structured logging, metrics, tracing, queue monitoring |
| Simplicity (YAGNI) | ✅ PASS | Single-tenant, focused scope, no Kubernetes |
| Integration Testing | ✅ PASS | Contract tests for API, pipeline integration tests |

**GATE RESULT**: ✅ PASS - Proceed to task creation

---

## Phase 0 & 1 Artifacts Status

| Artifact | Path | Status |
|----------|------|--------|
| Research | `research.md` | ✅ Complete |
| Data Model | `data-model.md` | ✅ Complete |
| API Contracts | `contracts/openapi.yaml` | ✅ Complete |
| Quickstart | `quickstart.md` | ✅ Complete |
| Tasks | `tasks.md` | ⏳ Pending (`/sp.tasks`) |

---

## Next Steps

1. ✅ Run `/sp.tasks` to break this plan into testable implementation tasks
2. ✅ Created `research.md` with detailed findings from Phase 0 research
3. ✅ Created `data-model.md` with complete SQLAlchemy models
4. ✅ Created `contracts/openapi.yaml` with OpenAPI specifications
5. ✅ Created `quickstart.md` with developer onboarding guide
