# Research & Discovery: Gold Tier Backend

**Feature**: 001-gold-tier-backend  
**Date**: 2026-03-02  
**Purpose**: Resolve technical unknowns from implementation plan

---

## Research Task 1: FastAPI WebSocket + Celery Progress Reporting

### Decision
Use **Redis pub/sub as bridge between Celery signals and FastAPI WebSocket**

### Rationale
- Celery workers publish progress events to Redis pub/sub channels
- FastAPI WebSocket manager subscribes to Redis channels
- WebSocket broadcasts to connected clients in real-time
- Decouples workers from HTTP layer (workers don't need WebSocket awareness)

### Implementation Pattern
```python
# Worker side
from celery.signals import task_postrun

@task_postrun.connect
def publish_progress(sender=None, task_id=None, **kwargs):
    redis_client.publish('job_progress', json.dumps({
        'task_id': task_id,
        'status': 'completed',
        'timestamp': datetime.utcnow().isoformat()
    }))

# FastAPI side
from redis.asyncio import Redis

@app.websocket("/ws/jobs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    pubsub = redis.pubsub()
    await pubsub.psubscribe('job_progress:*')
    
    async for message in pubsub.listen():
        await websocket.send_json(message['data'])
```

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Celery backend with polling | Simple, no extra infra | High latency, inefficient | Real-time requirement (<1s) |
| WebSocket direct from worker | Low latency | Workers need connection state, complex | Violates separation of concerns |
| Server-Sent Events (SSE) | Simpler than WebSocket | Unidirectional only | Need bidirectional for future features |

---

## Research Task 2: Idempotent Task Execution in Celery

### Decision
**Redis-based idempotency keys with TTL + database unique constraints**

### Rationale
- Generate idempotency key from task content hash
- Store key in Redis with 24-hour TTL (prevents infinite storage growth)
- Check key before task execution
- Database unique constraint as second line of defense

### Implementation Pattern
```python
from celery import Task
import hashlib

class IdempotentTask(Task):
    def __call__(self, *args, **kwargs):
        idempotency_key = self.generate_key(*args, **kwargs)
        
        # Check Redis
        if redis_client.exists(f"idempotency:{idempotency_key}"):
            return {'status': 'duplicate', 'key': idempotency_key}
        
        # Set key with TTL
        redis_client.setex(f"idempotency:{idempotency_key}", 86400, "processing")
        
        try:
            result = self.run(*args, **kwargs)
            redis_client.setex(f"idempotency:{idempotency_key}", 86400, "completed")
            return result
        except Exception as e:
            redis_client.delete(f"idempotency:{idempotency_key}")
            raise
    
    def generate_key(self, *args, **kwargs):
        content = f"{args}:{kwargs}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
```

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Database-only deduplication | Single source of truth | Race conditions possible | Need atomic check |
| Celery once plugin | Built-in solution | Less flexible, extra dependency | Custom solution gives more control |
| No idempotency | Simplest | Duplicate jobs on retry | Violates spec requirement |

---

## Research Task 3: Pipeline State Machine for Audit Trails

### Decision
**State pattern with event sourcing for state transitions**

### Rationale
- Each state transition emits an event
- Events stored in `audit_events` table
- Current state materialized in `jobs.status` column
- Full history reconstructable from events

### Implementation Pattern
```python
from enum import Enum
from dataclasses import dataclass

class JobStatus(Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class StateTransition:
    job_id: UUID
    from_state: JobStatus
    to_state: JobStatus
    timestamp: datetime
    metadata: dict  # stage_id, error_message, retry_count

# State machine
class JobStateMachine:
    transitions = {
        JobStatus.QUEUED: [JobStatus.PROCESSING, JobStatus.FAILED],
        JobStatus.PROCESSING: [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.QUEUED],  # queued for retry
        JobStatus.COMPLETED: [],  # terminal
        JobStatus.FAILED: [JobStatus.QUEUED],  # retry
    }
    
    def transition(self, job: Job, new_state: JobStatus, metadata: dict):
        if new_state not in self.transitions[job.status]:
            raise InvalidTransitionError(...)
        
        # Emit event
        event = StateTransition(
            job_id=job.id,
            from_state=job.status,
            to_state=new_state,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        audit_repository.save(event)
        
        # Update current state
        job.status = new_state
        job_repository.save(job)
```

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Status column only | Simple | No history, can't audit | Spec requires complete audit trail |
| Full event sourcing | Complete history | Complex queries for current state | Hybrid approach better |
| State table with versioning | Track changes | Verbose, harder to query | Event sourcing cleaner |

---

## Research Task 4: RBAC in FastAPI with JWT

### Decision
**JWT with custom claims for roles + FastAPI dependencies for authorization**

### Rationale
- JWT token contains `role` claim (submitter/approver)
- FastAPI dependencies extract and validate role
- Role-based dependency injection in route handlers
- Stateless authentication (no session storage)

### Implementation Pattern
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

class Role(Enum):
    SUBMITTER = "submitter"
    APPROVER = "approver"

async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=["HS256"])
        return {
            'user_id': payload['sub'],
            'role': payload['role'],
            'email': payload['email']
        }
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_role(*allowed_roles: Role):
    async def checker(user: dict = Depends(get_current_user)):
        if user['role'] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return checker

# Usage
@app.post("/plans/{plan_id}/approve")
async def approve_plan(
    plan_id: UUID,
    user: dict = Depends(require_role(Role.APPROVER))
):
    # Only approvers can access
    ...
```

### Alternatives Considered
| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| Session-based auth | Server control | Requires session storage | Stateless preferred for scale |
| API keys | Simple | No user context, no roles | Need user-specific permissions |
| OAuth2 with scopes | Standard | Overkill for internal system | JWT simpler for this use case |

---

## Research Task 5: Chroma vs Supabase Vector for AI Memory

### Decision
**Chroma (self-hosted) for development, Chroma Cloud for production**

### Rationale
- Chroma provides simple API for embedding storage
- Self-hosted option for full data control
- Metadata filtering built-in (filter by job_id, user_id, approval_status)
- No additional infrastructure beyond Docker container

### Comparison

| Criteria | Chroma | Supabase Vector |
|----------|--------|------------------|
| Setup | Docker container | PostgreSQL extension |
| Query API | Simple Python client | SQL with pgvector |
| Metadata filtering | ✅ Native | ✅ Via SQL WHERE |
| Scalability | Moderate (100Ks vectors) | High (millions) |
| Cost | Free (self-hosted) | Free tier + paid |
| Integration | Separate service | Same DB as app |

**Why Chroma**: Simpler API, dedicated vector DB features, easier to swap if needed

### Implementation Pattern
```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))

# Create collections
task_collection = client.create_collection("task_embeddings")
plan_collection = client.create_collection("plan_embeddings")

# Store embedding with metadata
task_collection.add(
    embeddings=[embedding],
    documents=[task_description],
    metadatas=[{
        'job_id': str(job_id),
        'user_id': str(user_id),
        'timestamp': datetime.utcnow().isoformat(),
        'domain': 'sales'
    }],
    ids=[str(job_id)]
)

# Query with filtering
results = task_collection.query(
    query_embeddings=[query_embedding],
    n_results=5,
    where={
        'approval_status': 'approved',
        'domain': 'sales'
    }
)
```

---

## Research Task 6: Event-Driven Watcher Architecture

### Decision
**Separate watcher services per channel, publishing to Redis event queue**

### Rationale
- Gmail watcher: Uses Gmail API push notifications
- WhatsApp watcher: Uses WhatsApp Business API webhooks
- Local file watcher: Uses watchdog library for filesystem events
- All watchers publish normalized events to Redis
- Main application consumes from Redis, decoupled from watcher implementation

### Architecture
```
┌─────────────────┐
│ Gmail Watcher   │──┐
│ (OAuth2 + IMAP) │  │
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌─────────────┐
│ WhatsApp Watcher│──┼───▶│ Redis Event │
│ (Webhooks)      │  │    │   Bus       │
└─────────────────┘  │    └──────┬──────┘
                     │           │
┌─────────────────┐  │           ▼
│ File Watcher    │──┘    ┌─────────────┐
│ (watchdog)      │       │ Celery      │
└─────────────────┘       │ Workers     │
                          └─────────────┘
```

### Event Schema
```python
from pydantic import BaseModel
from enum import Enum

class EventType(Enum):
    EMAIL_RECEIVED = "email_received"
    WHATSAPP_MESSAGE = "whatsapp_message"
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"

class WatcherEvent(BaseModel):
    event_type: EventType
    channel: str  # "gmail", "whatsapp", "filesystem"
    source_id: str  # email_id, phone_number, file_path
    payload: dict  # channel-specific data
    timestamp: datetime
    metadata: dict  # user_id (if known), priority
```

### Implementation Pattern
```python
# Gmail Watcher
import googleapiclient.discovery

class GmailWatcher:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.gmail = googleapiclient.discovery.build('gmail', 'v1')
    
    def watch_inbox(self):
        # Set up push notification to Pub/Sub
        self.gmail.users().watch(
            userId='me',
            body={
                'labelIds': ['INBOX'],
                'topicName': 'projects/.../topics/gmail_watch'
            }
        ).execute()
    
    def on_new_email(self, message_id: str):
        email = self.fetch_email(message_id)
        event = WatcherEvent(
            event_type=EventType.EMAIL_RECEIVED,
            channel='gmail',
            source_id=message_id,
            payload={'from': email['from'], 'subject': email['subject'], 'body': email['body']},
            timestamp=datetime.utcnow()
        )
        self.redis.publish('watcher_events', event.json())

# File Watcher
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class FileWatcherHandler(FileSystemEventHandler):
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def on_created(self, event):
        watcher_event = WatcherEvent(
            event_type=EventType.FILE_CREATED,
            channel='filesystem',
            source_id=event.src_path,
            payload={'path': event.src_path, 'is_directory': event.is_directory},
            timestamp=datetime.utcnow()
        )
        self.redis.publish('watcher_events', watcher_event.json())
```

---

## Summary of Decisions

| Unknown | Decision | Impact |
|---------|----------|--------|
| WebSocket + Celery | Redis pub/sub bridge | Real-time updates without coupling |
| Idempotency | Redis keys + DB constraints | Safe retries, no duplicates |
| Pipeline state | Event sourcing hybrid | Full audit trail + simple queries |
| RBAC | JWT with role claims | Stateless, scalable authorization |
| Vector memory | Chroma (self-hosted) | Simple API, metadata filtering |
| Watcher architecture | Separate services → Redis | Decoupled, extensible design |

---

## Next Steps

1. ✅ Research complete - all unknowns resolved
2. Proceed to data-model.md with entity definitions
3. Generate OpenAPI contracts in contracts/
4. Create quickstart.md for developer onboarding
