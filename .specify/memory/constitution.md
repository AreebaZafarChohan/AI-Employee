# Gold Tier Backend Constitution

**Version**: 1.0.0  
**Ratified**: 2026-03-02  
**Last Amended**: 2026-03-02

## Core Principles

### I. Test-First (NON-NEGOTIABLE)

TDD mandatory for all core components: Services, Workers, API routes. Tests written → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced.

**Exceptions**: Utility modules (config, logging) may use post-implementation testing.

**Verification**: All PRs must include passing tests for new functionality. Coverage gate: 80% minimum for services/, workers/, api/routes/.

---

### II. CLI Interface

Every major feature exposes functionality via CLI or curl-compatible endpoints. Health checks, job submission, and status queries must work via simple HTTP commands.

**Text I/O**: JSON request/response protocol. Errors return structured JSON with error_code, message, details.

**Verification**: quickstart.md must include curl examples for all major operations.

---

### III. Observability

Structured logging mandatory for all services. JSON format in production with correlation IDs. Every job, stage, and approval decision must be traceable.

**Three Signals Required**:
- Logs: Structured JSON with job_id, user_id, correlation_id
- Metrics: Queue depth, completion rate, failure rate, latency percentiles
- Traces: Job lifecycle from submission to completion

**Verification**: /health and /ready endpoints functional. Metrics endpoint exposes queue statistics.

---

### IV. Integration Testing

Focus areas requiring integration tests:
- API contract tests (all endpoints)
- Pipeline workflow (4-stage completion)
- Approval workflow (approve/reject/regenerate)
- WebSocket real-time updates
- Database migrations

**Verification**: tests/integration/ must cover all user stories. CI runs integration tests on every PR.

---

### V. Simplicity (YAGNI)

Start simple. Single-tenant architecture. No Kubernetes. No microservices. No premature optimization.

**Decision Framework**:
- Can it run in a single Docker Compose? → Yes
- Do we need distributed tracing? → No (add when we have 10+ services)
- Do we need multi-tenant isolation? → No (single-tenant per spec)
- Do we need message schema versioning? → No (add when we have breaking changes)

**Verification**: Architecture fits in docker-compose.yml with ≤7 services.

---

### VI. Async-First

No blocking AI calls in HTTP request cycle. All AI processing happens asynchronously via Celery workers. HTTP requests return immediately with job ID.

**Verification**: No direct AI model calls in api/routes/. All processing via Celery tasks.

---

### VII. Idempotency

All job submissions must be idempotent. Duplicate submissions with same content return existing job ID. Retry operations must not create duplicate work.

**Verification**: IdempotencyService validates duplicate submissions. Tests verify no duplicate jobs on retry.

---

## Security Requirements

### Authentication & Authorization

- JWT-based authentication for all API endpoints
- Role-based access control (Submitter vs Approver)
- WebSocket authentication via JWT in connection handshake
- No API keys or session cookies

### Data Protection

- No secrets in code or .env files committed to git
- Database credentials use least-privilege roles
- Redis requires authentication in production
- Input validation on all endpoints (Pydantic schemas)

### Audit & Compliance

- All approval decisions logged with approver identity
- All job state transitions logged with timestamps
- 90-day data retention enforced
- Unauthorized access attempts logged

---

## Performance Standards

### Latency Targets

- Job submission: <2 seconds (P95)
- Real-time updates: <1 second (P95)
- History query: <1 second (P95)
- Plan approval: <3 minutes user time (UX target)

### Throughput Targets

- 100 concurrent job processing sessions
- 95% of jobs complete within 5 minutes
- Queue depth monitoring with alerts at 80% capacity

### Reliability Targets

- 90% job success rate (automatic retries)
- Graceful degradation on AI timeout (30s limit)
- No data loss on worker failure (persisted state)

---

## Development Workflow

### Code Review Requirements

- All PRs require 1 approval before merge
- Tests must pass in CI
- Constitution compliance verified by reviewer
- Migration scripts reviewed by team lead

### Quality Gates

- **Pre-commit**: Black formatting, isort imports, flake8 linting
- **CI**: pytest with 80% coverage gate, mypy type checking
- **Pre-merge**: Integration tests pass, manual QA on staging

### Deployment Process

1. **Development**: Direct push to main branch, auto-deploy to dev
2. **Staging**: Tagged release, manual QA, performance validation
3. **Production**: Tagged release, change approval, rollback plan documented

---

## Governance

**Constitution Supersedes**: This constitution supersedes all other practices and guidelines. Any conflicting requirement must be resolved by amending the constitution.

**Amendment Process**:
1. Propose change via PR to `.specify/memory/constitution.md`
2. Team review and approval (unanimous consent required)
3. Document migration plan if breaking change
4. Update version and amendment date

**Verification**: All PRs/reviews must verify constitution compliance. Use `/sp.analyze` to detect violations before implementation.

---

**Acknowledged By**: Development Team  
**Next Review Date**: 2026-06-02 (quarterly review)
