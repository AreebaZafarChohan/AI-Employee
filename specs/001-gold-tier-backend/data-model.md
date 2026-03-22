# Data Model: Gold Tier Backend

**Feature**: 001-gold-tier-backend  
**Date**: 2026-03-02  
**Database**: PostgreSQL 15+  
**ORM**: SQLAlchemy 2.0+

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│      User       │       │      Job        │
├─────────────────┤       ├─────────────────┤
│ id (UUID) PK    │       │ id (UUID) PK    │
│ email (TEXT)    │       │ task_description│
│ role (ENUM)     │       │ status (ENUM)   │
│ created_at      │       │ progress_%      │
│ last_login_at   │       │ submitted_by FK │◀──────┐
└────────┬────────┘       │ submitted_at    │       │
         │                │ completed_at    │       │
         │                │ parent_job_id FK│───────┤ (self-ref)
         │                └────────┬────────┘       │
         │                         │                │
         │                         │ 1              │
         │                         │                │
         │                         │ N              │
         │                ┌────────▼────────┐       │
         │                │  PipelineStage  │       │
         │                ├─────────────────┤       │
         │                │ id (UUID) PK    │       │
         │                │ job_id FK       │       │
         │                │ stage_type ENUM │       │
         │                │ status ENUM     │       │
         │                │ input_data JSONB│       │
         │                │ output_data JSONB       │
         │                │ started_at      │       │
         │                │ completed_at    │       │
         │                │ error_message   │       │
         │                │ retry_count     │       │
         │                │ timeout_seconds │       │
         │                └────────┬────────┘       │
         │                         │                │
         │                         │ 1              │
         │                         │                │
         │                         │ N              │
         │                ┌────────▼────────┐       │
         │                │ AgentExecutionLog│      │
         │                ├─────────────────┤       │
         │                │ id (UUID) PK    │       │
         │                │ agent_type ENUM │       │
         │                │ job_id FK       │───────┘
         │                │ stage_id FK     │
         │                │ input JSONB     │
         │                │ output JSONB    │
         │                │ duration_ms     │
         │                │ status ENUM     │
         │                │ executed_at     │
         │                └─────────────────┘
         │
         │                ┌─────────────────┐
         │                │      Plan       │
         │                ├─────────────────┤
         │                │ id (UUID) PK    │
         │                │ job_id FK       │
         │                │ version (INT)   │
         │                │ task_analysis   │
         │                │ recommended_act │
         │                │ risk_assessment │
         │                │ approval_status │
         │                │ created_at      │
         │                └────────┬────────┘
         │                         │
         │                         │ 1
         │                         │
         │                         │ N
         │                ┌────────▼────────┐
         │                │  ApprovalEvent  │
         │                ├─────────────────┤
         │                │ id (UUID) PK    │
         │                │ plan_id FK      │
         │                │ decision ENUM   │
         │                │ approver_id FK  │───────┘
         │                │ decided_at      │
         │                │ comments (TEXT) │
         │                └─────────────────┘
```

---

## Enumerations

```python
from enum import Enum

class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineStageType(str, Enum):
    TASK_ANALYSIS = "task_analysis"
    PLAN_CREATION = "plan_creation"
    RISK_ASSESSMENT = "risk_assessment"
    FINAL_OUTPUT = "final_output"

class PipelineStageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRIED = "retried"

class ApprovalStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"

class UserRole(str, Enum):
    SUBMITTER = "submitter"
    APPROVER = "approver"

class AgentType(str, Enum):
    TASK_ANALYZER = "task_analyzer"
    PLANNER_AGENT = "planner_agent"
    RISK_AGENT = "risk_agent"

class AgentExecutionStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
```

---

## Models

### User

```python
from sqlalchemy import Column, String, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class User(Base):
    """
    System user with role-based access control.
    
    Roles:
    - SUBMITTER: Can create tasks, view own jobs
    - APPROVER: Can submit + approve/reject plans
    """
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.SUBMITTER)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    submitted_jobs = relationship("Job", back_populates="submitter", foreign_keys="Job.submitted_by")
    approval_events = relationship("ApprovalEvent", back_populates="approver")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
```

**Validation Rules**:
- `email`: NOT NULL, UNIQUE, valid email format
- `role`: NOT NULL, must be SUBMITTER or APPROVER
- `created_at`: Auto-generated on insert
- `last_login_at`: Nullable, updated on login

---

### Job

```python
from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class Job(Base):
    """
    Represents a submitted task being processed through the AI pipeline.
    
    Lifecycle:
    QUEUED → PROCESSING → COMPLETED | FAILED
                 ↑              ↓
                 └────(retry)───┘
    
    Max retries: 3 (with exponential backoff)
    """
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_description = Column(Text, nullable=False)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.QUEUED, index=True)
    current_stage_id = Column(String(36), ForeignKey("pipeline_stages.id"), nullable=True)
    progress_percentage = Column(Integer, nullable=False, default=0)
    submitted_by = Column(String(36), ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    parent_job_id = Column(String(36), ForeignKey("jobs.id"), nullable=True, index=True)
    
    # Relationships
    submitter = relationship("User", back_populates="submitted_jobs", foreign_keys=[submitted_by])
    stages = relationship("PipelineStage", back_populates="job", cascade="all, delete-orphan")
    parent_job = relationship("Job", remote_side=[id], backref="child_jobs")
    plan = relationship("Plan", back_populates="job", uselist=False, cascade="all, delete-orphan")
    agent_logs = relationship("AgentExecutionLog", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, status={self.status.value}, progress={self.progress_percentage}%)>"
```

**Validation Rules**:
- `task_description`: NOT NULL, min length 10 characters
- `status`: NOT NULL, default QUEUED
- `progress_percentage`: 0-100 inclusive
- `submitted_by`: NOT NULL, FK to users.id
- `parent_job_id`: Nullable (set for regenerated jobs)

**Indexes**:
- `status`: For queue queries
- `submitted_by`: For user job history
- `parent_job_id`: For regeneration lineage queries

---

### PipelineStage

```python
from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class PipelineStage(Base):
    """
    Represents one stage in the 4-stage AI processing workflow.
    
    Stages (in order):
    1. TASK_ANALYSIS: Parse and understand the task
    2. PLAN_CREATION: Generate structured action plan
    3. RISK_ASSESSMENT: Evaluate risks and mitigations
    4. FINAL_OUTPUT: Assemble final deliverable
    
    Timeout: 30 seconds per stage (configurable)
    """
    __tablename__ = "pipeline_stages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    stage_type = Column(Enum(PipelineStageType), nullable=False, index=True)
    status = Column(Enum(PipelineStageStatus), nullable=False, default=PipelineStageStatus.PENDING)
    input_data = Column(JSON, nullable=True)  # JSONB in PostgreSQL
    output_data = Column(JSON, nullable=True)  # JSONB in PostgreSQL
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    timeout_seconds = Column(Integer, nullable=False, default=30)
    
    # Relationships
    job = relationship("Job", back_populates="stages")
    agent_logs = relationship("AgentExecutionLog", back_populates="stage", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PipelineStage(job_id={self.job_id}, type={self.stage_type.value}, status={self.status.value})>"
```

**Validation Rules**:
- `job_id`: NOT NULL, FK to jobs.id
- `stage_type`: NOT NULL, one of 4 stage types
- `status`: NOT NULL, default PENDING
- `input_data`: JSONB, nullable (stage-specific schema)
- `output_data`: JSONB, nullable (stage-specific schema)
- `timeout_seconds`: > 0, default 30
- `retry_count`: >= 0, max 3

**Indexes**:
- `job_id`: For job stage queries
- `stage_type`: For pipeline analytics
- `status`: For retry queries

---

### Plan

```python
from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class Plan(Base):
    """
    Structured output generated by the AI orchestration engine.
    
    Versioning:
    - Version 1: Initial plan from pipeline
    - Version 2+: Regenerated after rejection with feedback
    
    Approval workflow:
    DRAFT → PENDING_APPROVAL → APPROVED | REJECTED
    """
    __tablename__ = "plans"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), unique=True, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    task_analysis = Column(JSON, nullable=True)  # JSONB
    recommended_actions = Column(JSON, nullable=True)  # JSONB
    risk_assessment = Column(JSON, nullable=True)  # JSONB
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.DRAFT, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="plan")
    approval_events = relationship("ApprovalEvent", back_populates="plan", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint('job_id', 'version', name='uq_job_version'),
    )
    
    def __repr__(self):
        return f"<Plan(id={self.id}, job_id={self.job_id}, version={self.version}, status={self.approval_status.value})>"
```

**Validation Rules**:
- `job_id`: NOT NULL, UNIQUE (one plan per job)
- `version`: >= 1, increments on regeneration
- `task_analysis`: JSONB, structure from Task Analysis stage
- `recommended_actions`: JSONB, list of actions with priorities
- `risk_assessment`: JSONB, risks with severity scores
- `approval_status`: NOT NULL, default DRAFT

**Indexes**:
- `job_id`: For job-plan lookup
- `approval_status`: For approval queue queries

---

### ApprovalEvent

```python
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class ApprovalEvent(Base):
    """
    Records a human decision on a plan.
    
    Captures:
    - Decision (approve/reject)
    - Who made the decision
    - When it was made
    - Comments/feedback (especially for rejections)
    """
    __tablename__ = "approval_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    plan_id = Column(String(36), ForeignKey("plans.id"), nullable=False)
    decision = Column(Enum(ApprovalDecision), nullable=False)
    approver_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    decided_at = Column(DateTime(timezone=True), server_default=func.now())
    comments = Column(Text, nullable=True)
    
    # Relationships
    plan = relationship("Plan", back_populates="approval_events")
    approver = relationship("User", back_populates="approval_events")
    
    def __repr__(self):
        return f"<ApprovalEvent(plan_id={self.plan_id}, decision={self.decision.value}, by={self.approver_id})>"
```

**Validation Rules**:
- `plan_id`: NOT NULL, FK to plans.id
- `decision`: NOT NULL, APPROVE or REJECT
- `approver_id`: NOT NULL, FK to users.id (must be APPROVER role)
- `comments`: Required if decision = REJECT

---

### AgentExecutionLog

```python
from sqlalchemy import Column, String, Enum, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

class AgentExecutionLog(Base):
    """
    Records the execution of a specialized AI agent.
    
    Agents:
    - TASK_ANALYZER: Parses task, extracts requirements
    - PLANNER_AGENT: Generates structured action plan
    - RISK_AGENT: Evaluates risks and mitigations
    
    Used for:
    - Audit trail
    - Performance analysis
    - Debugging failures
    """
    __tablename__ = "agent_execution_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False)
    stage_id = Column(String(36), ForeignKey("pipeline_stages.id"), nullable=False)
    input_provided = Column(JSON, nullable=True)  # JSONB
    output_generated = Column(JSON, nullable=True)  # JSONB
    execution_duration_ms = Column(Integer, nullable=False)
    status = Column(Enum(AgentExecutionStatus), nullable=False, index=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="agent_logs")
    stage = relationship("PipelineStage", back_populates="agent_logs")
    
    def __repr__(self):
        return f"<AgentExecutionLog(agent={self.agent_type.value}, job={self.job_id}, status={self.status.value})>"
```

**Validation Rules**:
- `agent_type`: NOT NULL, one of 3 agent types
- `job_id`: NOT NULL, FK to jobs.id
- `stage_id`: NOT NULL, FK to pipeline_stages.id
- `input_provided`: JSONB, input to agent
- `output_generated`: JSONB, output from agent
- `execution_duration_ms`: >= 0
- `status`: NOT NULL, SUCCESS/FAILURE/TIMEOUT

**Indexes**:
- `agent_type`: For agent performance analytics
- `job_id`: For job audit trail
- `status`: For failure analysis

---

## Database Schema (SQL)

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enums
CREATE TYPE user_role AS ENUM ('submitter', 'approver');
CREATE TYPE job_status AS ENUM ('queued', 'processing', 'completed', 'failed');
CREATE TYPE pipeline_stage_type AS ENUM ('task_analysis', 'plan_creation', 'risk_assessment', 'final_output');
CREATE TYPE pipeline_stage_status AS ENUM ('pending', 'running', 'completed', 'failed', 'retried');
CREATE TYPE approval_status AS ENUM ('draft', 'pending_approval', 'approved', 'rejected');
CREATE TYPE approval_decision AS ENUM ('approve', 'reject');
CREATE TYPE agent_type AS ENUM ('task_analyzer', 'planner_agent', 'risk_agent');
CREATE TYPE agent_execution_status AS ENUM ('success', 'failure', 'timeout');

-- Users table
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'submitter',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Jobs table
CREATE TABLE jobs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_description TEXT NOT NULL,
    status job_status NOT NULL DEFAULT 'queued',
    current_stage_id VARCHAR(36),
    progress_percentage INTEGER NOT NULL DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    submitted_by VARCHAR(36) NOT NULL REFERENCES users(id),
    submitted_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    parent_job_id VARCHAR(36) REFERENCES jobs(id)
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_submitted_by ON jobs(submitted_by);
CREATE INDEX idx_jobs_parent_job_id ON jobs(parent_job_id);

-- Pipeline stages table
CREATE TABLE pipeline_stages (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    stage_type pipeline_stage_type NOT NULL,
    status pipeline_stage_status NOT NULL DEFAULT 'pending',
    input_data JSONB,
    output_data JSONB,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER NOT NULL DEFAULT 0 CHECK (retry_count >= 0),
    timeout_seconds INTEGER NOT NULL DEFAULT 30 CHECK (timeout_seconds > 0)
);

CREATE INDEX idx_pipeline_stages_job_id ON pipeline_stages(job_id);
CREATE INDEX idx_pipeline_stages_stage_type ON pipeline_stages(stage_type);
CREATE INDEX idx_pipeline_stages_status ON pipeline_stages(status);

-- Plans table
CREATE TABLE plans (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id VARCHAR(36) UNIQUE NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    version INTEGER NOT NULL DEFAULT 1 CHECK (version >= 1),
    task_analysis JSONB,
    recommended_actions JSONB,
    risk_assessment JSONB,
    approval_status approval_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_job_version UNIQUE (job_id, version)
);

CREATE INDEX idx_plans_job_id ON plans(job_id);
CREATE INDEX idx_plans_approval_status ON plans(approval_status);

-- Approval events table
CREATE TABLE approval_events (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id VARCHAR(36) NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
    decision approval_decision NOT NULL,
    approver_id VARCHAR(36) NOT NULL REFERENCES users(id),
    decided_at TIMESTAMPTZ DEFAULT NOW(),
    comments TEXT
);

CREATE INDEX idx_approval_events_plan_id ON approval_events(plan_id);
CREATE INDEX idx_approval_events_approver_id ON approval_events(approver_id);

-- Agent execution logs table
CREATE TABLE agent_execution_logs (
    id VARCHAR(36) PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type agent_type NOT NULL,
    job_id VARCHAR(36) NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    stage_id VARCHAR(36) NOT NULL REFERENCES pipeline_stages(id) ON DELETE CASCADE,
    input_provided JSONB,
    output_generated JSONB,
    execution_duration_ms INTEGER NOT NULL CHECK (execution_duration_ms >= 0),
    status agent_execution_status NOT NULL,
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_logs_agent_type ON agent_execution_logs(agent_type);
CREATE INDEX idx_agent_logs_job_id ON agent_execution_logs(job_id);
CREATE INDEX idx_agent_logs_stage_id ON agent_execution_logs(stage_id);
CREATE INDEX idx_agent_logs_status ON agent_execution_logs(status);
```

---

## Data Retention Policy

**Requirement**: 90-day retention (from spec FR-015)

```sql
-- Create retention function
CREATE OR REPLACE FUNCTION enforce_data_retention()
RETURNS void AS $$
BEGIN
    -- Delete jobs older than 90 days (cascade deletes related records)
    DELETE FROM jobs
    WHERE created_at < NOW() - INTERVAL '90 days'
    AND status IN ('completed', 'failed');
    
    -- Log deletion count
    RAISE NOTICE 'Data retention: Deleted jobs older than 90 days';
END;
$$ LANGUAGE plpgsql;

-- Schedule with pg_cron (or external scheduler)
SELECT cron.schedule(
    'daily-retention',
    '0 2 * * *',  -- Daily at 2 AM
    $$SELECT enforce_data_retention()$$
);
```

---

## Migration Strategy

**Tool**: Alembic (SQLAlchemy migration tool)

```bash
# Initialize Alembic
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial Gold Tier schema"

# Apply migration
alembic upgrade head
```

**Migration File Structure**:
```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   └── 002_add_indexes.py
├── env.py
└── script.py.mako
```

---

## Next Steps

1. ✅ Data model complete
2. Generate OpenAPI contracts in `contracts/`
3. Create `quickstart.md` for onboarding
4. Implement models in `src/models/`
