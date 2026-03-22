# Gold Tier Backend - AI Orchestration Engine

A semi-autonomous AI orchestration engine with event-driven architecture, background processing, multi-stage AI pipelines, real-time updates, and human approval workflow.

## Features

- **4-Stage AI Pipeline**: Task Analysis → Plan Creation → Risk Assessment → Final Output
- **Real-time Progress Updates**: WebSocket-based live progress tracking
- **Human Approval Workflow**: Role-based approval/rejection with regeneration
- **Complete Audit Trail**: Full history of all pipeline stages, agent executions, and decisions
- **Background Processing**: Celery workers with Redis message queue
- **Role-Based Access Control**: Submitter and Approver roles with JWT authentication
- **90-Day Data Retention**: Automatic cleanup of old jobs

## Tech Stack

- **Language**: Python 3.11+
- **API Framework**: FastAPI
- **Background Workers**: Celery + Redis
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic 2.0
- **Real-time**: WebSockets
- **Containerization**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (optional, for containerized deployment)
- PostgreSQL 15+ (if running locally)
- Redis 7+ (if running locally)

### Option 1: Docker Compose (Recommended)

```bash
# Start all services (API, Worker, PostgreSQL, Redis)
cd docker
docker-compose up -d

# Check logs
docker-compose logs -f api
docker-compose logs -f worker

# Stop all services
docker-compose down
```

### Option 2: Local Development

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 3. Start PostgreSQL and Redis (use Docker or local installation)
docker-compose up -d postgres redis

# 4. Run database migrations
python src/models/migrate.py upgrade

# 5. Start the API server
./scripts/run_api.sh dev

# 6. Start the Celery worker (in a new terminal)
./scripts/run_worker.sh dev
```

## API Documentation

Once running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/jobs` | Submit a new task |
| GET | `/api/v1/jobs/{job_id}` | Get job status |
| GET | `/api/v1/jobs` | List user's jobs (paginated) |
| GET | `/api/v1/jobs/{job_id}/history` | Get complete audit trail |

### Plans & Approvals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/plans/{plan_id}` | Get plan details |
| POST | `/api/v1/plans/{plan_id}/approve` | Approve plan (Approver only) |
| POST | `/api/v1/plans/{plan_id}/reject` | Reject plan with comments (Approver only) |

### Real-time Updates

| Endpoint | Description |
|----------|-------------|
| WS `/api/v1/ws/jobs` | WebSocket for real-time job progress |

### Metrics & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/ready` | Readiness check |
| GET | `/api/v1/metrics/queue` | Queue metrics (Approver only) |
| GET | `/api/v1/analytics/retries` | Retry analytics |

## Authentication

All API endpoints require JWT authentication.

### Get a Token

For development, you can create a token using the security module:

```python
from src.core.security import create_access_token

token = create_access_token(data={"sub": "your-user-id", "role": "submitter"})
```

### Use the Token

Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/jobs
```

## Example Usage

### Submit a Task

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Create a sales email template for our new AI product launch"}'
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued",
  "submitted_at": "2026-03-02T10:00:00Z"
}
```

### Check Job Status

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <token>"
```

### Get Job History

```bash
curl http://localhost:8000/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/history \
  -H "Authorization: Bearer <token>"
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI     │────▶│  PostgreSQL │
│  (Browser/  │     │    API       │     │  Database   │
│   Mobile)   │◀────│              │◀────│             │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                           │ WebSocket
                           │
                    ┌──────▼───────┐     ┌─────────────┐
                    │    Redis     │────▶│   Celery    │
                    │  Event Bus   │     │   Workers   │
                    └──────────────┘     └─────────────┘
```

### Pipeline Stages

1. **Task Analysis**: Parse task description, extract requirements, identify domain
2. **Plan Creation**: Generate structured plan with recommended actions
3. **Risk Assessment**: Evaluate risks, assign severity scores, suggest mitigations
4. **Final Output**: Assemble complete deliverable, mark job complete

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest -v --cov=src --cov-report=html

# Run specific test category
pytest tests/contract/       # API contract tests
pytest tests/integration/    # Integration tests
pytest tests/unit/           # Unit tests
```

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `REDIS_URL` | Redis connection string | - |
| `JWT_SECRET_KEY` | Secret key for JWT signing | - |
| `LOG_LEVEL` | Logging level | `INFO` |
| `STAGE_TIMEOUT_SECONDS` | Timeout per pipeline stage | `30` |
| `MAX_RETRIES` | Max retry attempts per stage | `3` |
| `RETENTION_DAYS` | Data retention period | `90` |

## Production Deployment

See `docker/docker-compose.prod.yml` for production configuration.

### Pre-deployment Checklist

- [ ] Set strong `JWT_SECRET_KEY`
- [ ] Configure database credentials
- [ ] Set up SSL/TLS certificates
- [ ] Configure CORS for allowed origins
- [ ] Set up monitoring and alerting
- [ ] Configure log aggregation
- [ ] Set up database backups
- [ ] Test health check endpoints

## Troubleshooting

### Common Issues

**Worker not processing jobs:**
- Check Redis connection: `redis-cli ping`
- Verify worker is running: `docker-compose ps`
- Check worker logs: `docker-compose logs worker`

**Database connection errors:**
- Verify PostgreSQL is running: `docker-compose ps postgres`
- Check connection string in `.env`
- Ensure database exists: `psql -U user -d gold_tier`

**WebSocket connection fails:**
- Verify JWT token is valid
- Check CORS configuration
- Ensure WebSocket endpoint is accessible

## License

Internal use only.

## Support

For issues or questions, contact the development team.
