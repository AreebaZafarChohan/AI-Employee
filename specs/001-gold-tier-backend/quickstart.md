# Quickstart: Gold Tier Backend

**Feature**: 001-gold-tier-backend  
**Last Updated**: 2026-03-02  
**Status**: Ready for development

---

## Overview

Gold Tier Backend is an AI orchestration engine that processes tasks through a 4-stage AI pipeline with human approval workflow. Built with FastAPI, Celery, Redis, and PostgreSQL.

**Key Features**:
- 🚀 Asynchronous job processing via Celery workers
- 🔄 4-stage AI pipeline (Task Analysis → Plan Creation → Risk Assessment → Final Output)
- 👥 Role-based access (Submitter / Approver)
- ⚡ Real-time progress updates via WebSocket
- ✅ Human approval workflow with audit trail
- 🔍 Complete job history and traceability

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Runtime |
| Docker | 24+ | Containerization |
| Docker Compose | 2.20+ | Multi-container orchestration |
| Redis | 7+ | Message broker, caching |
| PostgreSQL | 15+ | Primary database |

### Installation Checks

```bash
# Verify Python version
python --version  # Should be 3.11+

# Verify Docker
docker --version  # Should be 24+
docker-compose --version  # Should be 2.20+

# Verify Redis (if running locally)
redis-cli --version  # Should be 7+

# Verify PostgreSQL (if running locally)
psql --version  # Should be 15+
```

---

## Quick Start (5 Minutes)

### Step 1: Clone and Setup

```bash
# Navigate to project root
cd /path/to/AI-Employee

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Start Infrastructure (Docker)

```bash
# Start Redis and PostgreSQL
docker-compose up -d redis postgres

# Verify containers are running
docker-compose ps
# Should show: redis and postgres as "Up"
```

### Step 3: Initialize Database

```bash
# Run database migrations
python -m src.models migrate

# Output should show:
# - Creating tables: users, jobs, pipeline_stages, plans, approval_events, agent_execution_logs
# - Creating indexes
# - Migration complete
```

### Step 4: Create Initial User

```bash
# Create an approver user (for testing)
python scripts/create_user.py --email admin@localhost --role approver

# Create a submitter user
python scripts/create_user.py --email user@localhost --role submitter

# Note: Save the JWT tokens returned for API testing
```

### Step 5: Start API Server

```bash
# Terminal 1: Start FastAPI
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Output should show:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete.
```

### Step 6: Start Celery Worker

```bash
# Terminal 2: Start Celery worker
celery -A src.workers.celery_app worker --loglevel=info --pool=solo

# Output should show:
# [tasks]
#   src.workers.stages.task_analysis.run_task_analysis
#   src.workers.stages.plan_creation.create_plan
#   src.workers.stages.risk_assessment.assess_risks
#   src.workers.stages.final_output.generate_final_output
#
# [2026-03-02 10:00:00,000: INFO/MainProcess] Connected to redis://localhost:6379/0
# [2026-03-02 10:00:00,001: INFO/MainProcess] celery@hostname ready.
```

### Step 7: Test the API

```bash
# Set your JWT token (from create_user step)
export JWT_TOKEN="your_jwt_token_here"

# Submit a test job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Analyze Q4 2025 sales data for North America. Identify top 3 growth opportunities and recommend action items for Q1 2026."
  }'

# Expected response:
# {
#   "job_id": "550e8400-e29b-41d4-a716-446655440000",
#   "status": "queued",
#   "submitted_at": "2026-03-02T10:00:00Z",
#   "message": "Job queued successfully"
# }

# Check job status
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get job history (audit trail)
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/history \
  -H "Authorization: Bearer $JWT_TOKEN"
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test category
pytest tests/unit  # Unit tests only
pytest tests/integration  # Integration tests only
pytest tests/contract  # API contract tests only

# Run with verbose output
pytest -v
```

### Code Style

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Type checking
mypy src

# Linting
flake8 src tests
```

### Database Operations

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

---

## API Testing Guide

### Authentication

All API endpoints require JWT authentication. Obtain a token:

```bash
# Login (example endpoint)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@localhost",
    "password": "your_password"
  }'

# Response:
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "role": "approver"
# }
```

### Submit Task

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Your task description here (min 10 characters)"
  }'
```

### Monitor Progress (WebSocket)

```python
import asyncio
import websockets

async def monitor_job(job_id: str, token: str):
    uri = f"ws://localhost:8000/api/v1/ws/jobs"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        while True:
            message = await ws.recv()
            data = json.loads(message)
            
            if data['job_id'] == job_id:
                print(f"Event: {data['event_type']}")
                print(f"Progress: {data['data'].get('progress_percentage', 0)}%")
                
                if data['event_type'] in ['job_completed', 'job_failed']:
                    break

# Usage
asyncio.run(monitor_job("your-job-id", "your-jwt-token"))
```

### Approve Plan

```bash
curl -X POST http://localhost:8000/api/v1/plans/PLAN_ID/approve \
  -H "Authorization: Bearer APPROVER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": "Approved. Excellent analysis."
  }'
```

### Reject Plan

```bash
curl -X POST http://localhost:8000/api/v1/plans/PLAN_ID/reject \
  -H "Authorization: Bearer APPROVER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "comments": "The risk assessment needs more detail on mitigation strategies."
  }'
```

### Get Queue Metrics (Approvers Only)

```bash
curl http://localhost:8000/api/v1/metrics/queue \
  -H "Authorization: Bearer APPROVER_JWT_TOKEN"

# Response:
# {
#   "queued_count": 5,
#   "processing_count": 3,
#   "completed_today": 42,
#   "failed_today": 2,
#   "avg_completion_time_seconds": 145.5,
#   "pending_approval_count": 7,
#   "retry_queue_depth": 1
# }
```

---

## Troubleshooting

### Issue: Worker Not Processing Jobs

**Symptoms**: Jobs stay in "queued" status indefinitely

**Diagnosis**:
```bash
# Check if Celery worker is running
docker-compose ps worker

# Check worker logs
docker-compose logs worker

# Check Redis connection
redis-cli ping  # Should return: PONG
```

**Solution**:
```bash
# Restart worker
docker-compose restart worker

# Or run worker locally
celery -A src.workers.celery_app worker --loglevel=debug
```

### Issue: WebSocket Connection Fails

**Symptoms**: WebSocket connection rejected with 401

**Diagnosis**:
- Check JWT token is valid and not expired
- Verify token is passed in Authorization header during handshake

**Solution**:
```python
# Ensure token is passed correctly
headers = {"Authorization": f"Bearer {token}"}
async with websockets.connect(uri, extra_headers=headers) as ws:
    ...
```

### Issue: Database Connection Error

**Symptoms**: `could not connect to server`

**Diagnosis**:
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# Check database URL
echo $DATABASE_URL
```

**Solution**:
```bash
# Restart PostgreSQL
docker-compose restart postgres

# Verify connection
psql $DATABASE_URL -c "SELECT 1"
```

### Issue: Migration Failures

**Symptoms**: `alembic upgrade head` fails

**Diagnosis**:
```bash
# Check current migration state
alembic current

# Check for pending migrations
alembic history
```

**Solution**:
```bash
# If database is empty, stamp with initial revision
alembic stamp head

# Then upgrade
alembic upgrade head
```

---

## Production Deployment

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:password@postgres:5432/gold_tier
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Optional
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
CORS_ORIGINS=https://app.goldtier.local
RATE_LIMIT_PER_MINUTE=100
```

### Docker Compose (Production)

```bash
# Start all services
docker-compose -f docker/docker-compose.prod.yml up -d

# Check service health
docker-compose -f docker/docker-compose.prod.yml ps

# View logs
docker-compose -f docker/docker-compose.prod.yml logs -f api
docker-compose -f docker/docker-compose.prod.yml logs -f worker
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Response: {"status": "healthy", "database": "connected", "redis": "connected"}

# Readiness probe
curl http://localhost:8000/ready

# Response: {"ready": true}
```

---

## Next Steps

1. ✅ Environment setup complete
2. ✅ API tested successfully
3. Review `data-model.md` for database schema details
4. Review `contracts/openapi.yaml` for full API specification
5. Review `research.md` for architectural decisions
6. Proceed to implementation tasks

---

## Useful Commands Reference

```bash
# Infrastructure
docker-compose up -d                    # Start all containers
docker-compose down                     # Stop all containers
docker-compose logs -f                  # Follow all logs
docker-compose restart worker           # Restart worker only

# Database
python -m src.models migrate            # Run migrations
alembic revision --autogenerate -m ""   # Create migration
alembic upgrade head                    # Apply migrations
alembic downgrade -1                    # Rollback one migration

# Testing
pytest                                  # Run all tests
pytest -v --tb=short                    # Verbose output
pytest --cov=src                        # With coverage
pytest tests/unit/test_jobs.py          # Specific test file

# Development
black src tests                         # Format code
isort src tests                         # Sort imports
mypy src                                # Type check
flake8 src tests                        # Lint

# Monitoring
redis-cli                               # Redis CLI
redis-cli MONITOR                       # Monitor Redis commands
psql $DATABASE_URL                      # PostgreSQL CLI
```

---

## Support

- **Documentation**: `/specs/001-gold-tier-backend/`
- **API Spec**: `/specs/001-gold-tier-backend/contracts/openapi.yaml`
- **Issues**: GitHub Issues
- **Chat**: #gold-tier-backend
