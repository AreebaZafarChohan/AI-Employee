# Data Model: Silver Tier Backend

**Date**: 2026-02-22
**Feature**: Silver Tier Backend
**Branch**: 001-silver-tier-backend

## Overview

This document defines the database schema and data models for the Silver Tier Backend system. All entities are designed for PostgreSQL with Prisma ORM.

---

## Entity Definitions

### Task

Represents a unit of work to be completed.

**Table**: `tasks`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | String (UUID) | Primary Key | Unique identifier |
| title | String | NOT NULL, max 200 chars | Task title (required) |
| description | String | Nullable | Task description (optional) |
| status | Enum | NOT NULL, default 'Pending' | Current status (Pending/In Progress/Done) |
| createdAt | DateTime | NOT NULL, default now() | Creation timestamp |
| updatedAt | DateTime | NOT NULL, default now() | Last update timestamp |
| completedAt | DateTime | Nullable | Completion timestamp (set when status = Done) |

**Status Enum**: `TaskStatus`
- `Pending` (default)
- `In Progress`
- `Done`

**Indexes**:
- `idx_tasks_status` - Filter by status
- `idx_tasks_createdAt` - Sort by creation date

**Constraints**:
- Status transitions must follow linear progression: Pending → In Progress → Done
- `completedAt` must be set when status changes to Done
- `completedAt` must be NULL when status is Pending or In Progress

---

### Plan

Represents an AI-generated action plan for completing a task.

**Table**: `plans`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | String (UUID) | Primary Key | Unique identifier |
| taskId | String (UUID) | Foreign Key → tasks.id | Reference to source task |
| status | Enum | NOT NULL, default 'Draft' | Plan status |
| createdAt | DateTime | NOT NULL, default now() | Creation timestamp |
| updatedAt | DateTime | NOT NULL, default now() | Last update timestamp |

**Status Enum**: `PlanStatus`
- `Draft` (default)
- `Active`
- `Completed`
- `Archived`

**Indexes**:
- `idx_plans_taskId` - Lookup by task
- `idx_plans_status` - Filter by status

**Constraints**:
- One-to-one relationship with Task (one plan per task)
- Cascade delete: if task is deleted, associated plan is deleted

---

### Plan Step

Individual steps within a plan (stored as related table for queryability).

**Table**: `plan_steps`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | String (UUID) | Primary Key | Unique identifier |
| planId | String (UUID) | Foreign Key → plans.id | Reference to parent plan |
| order | Int | NOT NULL | Step order in sequence |
| title | String | NOT NULL, max 200 chars | Step title |
| description | String | NOT NULL | Step description |
| estimatedDuration | Int | Nullable | Estimated minutes to complete |
| completed | Boolean | NOT NULL, default false | Completion flag |
| createdAt | DateTime | NOT NULL, default now() | Creation timestamp |

**Indexes**:
- `idx_plan_steps_planId` - Lookup steps by plan
- `idx_plan_steps_order` - Order steps within plan

**Constraints**:
- Steps are ordered sequentially (order field determines sequence)
- Cascade delete: if plan is deleted, all steps are deleted

---

### ActivityLog

Represents a record of a system action.

**Table**: `activity_logs`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | String (UUID) | Primary Key | Unique identifier |
| type | String | NOT NULL, max 50 chars | Action type (e.g., 'task.created', 'state.changed') |
| description | String | NOT NULL, max 500 chars | Human-readable description |
| timestamp | DateTime | NOT NULL, default now() | When the action occurred |
| metadata | Json | Nullable | Additional structured data |

**Indexes**:
- `idx_activity_logs_timestamp` - Sort/filter by time
- `idx_activity_logs_type` - Filter by action type

**Constraints**:
- Append-only (no updates or deletes via API)
- Metadata stored as JSON for flexibility

**Activity Types**:
- User actions: `task.created`, `task.updated`, `task.deleted`, `plan.generated`, `plan.updated`, `plan.deleted`
- System events: `ai.invoked`, `ai.completed`, `ai.failed`, `state.changed`, `error.occurred`

---

### SystemState

Represents the current operational state of the AI system (singleton table).

**Table**: `system_state`

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | String (UUID) | Primary Key | Always single row (use fixed ID) |
| state | Enum | NOT NULL | Current system state |
| lastActivity | DateTime | NOT NULL | Timestamp of last activity |
| updatedAt | DateTime | NOT NULL, default now() | Last update timestamp |

**State Enum**: `SystemStateEnum`
- `Idle` (default)
- `Thinking`
- `Planning`

**Constraints**:
- Singleton table (only one row exists)
- ID is fixed value: 'system-state-singleton'

**State Transition Triggers**:
- `Idle` → `Thinking`: Task received for processing
- `Thinking` → `Planning`: Task analysis complete, ready to generate plan
- `Planning` → `Idle`: Plan delivered to user

---

## Relationships

```
┌─────────────┐         ┌──────────────┐         ┌────────────────┐
│    Task     │ 1────1  │     Plan     │ 1─────* │   PlanStep     │
├─────────────┤         ├──────────────┤         ├────────────────┤
│ id (PK)     │         │ id (PK)      │         │ id (PK)        │
│ title       │         │ taskId (FK)  │         │ planId (FK)    │
│ description │         │ status       │         │ order          │
│ status      │         │ createdAt    │         │ title          │
│ createdAt   │         │ updatedAt    │         │ description    │
│ completedAt │         └──────────────┘         │ estimatedDur.  │
└─────────────┘                                  │ completed      │
                                                 │ createdAt      │
                                                 └────────────────┘

┌──────────────────┐
│   ActivityLog    │
├──────────────────┤
│ id (PK)          │
│ type             │
│ description      │
│ timestamp        │
│ metadata (JSON)  │
└──────────────────┘

┌──────────────────┐
│   SystemState    │
├──────────────────┤
│ id (PK, fixed)   │
│ state            │
│ lastActivity     │
│ updatedAt        │
└──────────────────┘
```

---

## Prisma Schema

```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum TaskStatus {
  Pending
  InProgress
  Done
}

enum PlanStatus {
  Draft
  Active
  Completed
  Archived
}

enum SystemStateEnum {
  Idle
  Thinking
  Planning
}

model Task {
  id          String    @id @default(uuid())
  title       String    @db.VarChar(200)
  description String?
  status      TaskStatus @default(Pending)
  createdAt   DateTime  @default(now())
  updatedAt   DateTime  @updatedAt
  completedAt DateTime?
  
  plan        Plan?

  @@index([status])
  @@index([createdAt])
}

model Plan {
  id        String   @id @default(uuid())
  taskId    String   @unique
  status    PlanStatus @default(Draft)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
  
  task  Task       @relation(fields: [taskId], references: [id], onDelete: Cascade)
  steps PlanStep[]

  @@index([status])
}

model PlanStep {
  id                String   @id @default(uuid())
  planId            String
  order             Int
  title             String   @db.VarChar(200)
  description       String
  estimatedDuration Int?
  completed         Boolean  @default(false)
  createdAt         DateTime @default(now())
  
  plan Plan @relation(fields: [planId], references: [id], onDelete: Cascade)

  @@index([planId])
  @@index([order])
}

model ActivityLog {
  id          String   @id @default(uuid())
  type        String   @db.VarChar(50)
  description String   @db.VarChar(500)
  timestamp   DateTime @default(now())
  metadata    Json?

  @@index([timestamp])
  @@index([type])
}

model SystemState {
  id           String         @id
  state        SystemStateEnum
  lastActivity DateTime
  updatedAt    DateTime       @updatedAt

  @@map("system_state")
}
```

---

## Validation Rules

### Task Validation

```typescript
const TaskSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().max(1000).optional().or(z.literal('')),
  status: z.enum(['Pending', 'In Progress', 'Done']).optional()
});

const TaskStatusTransitionSchema = z.object({
  currentStatus: z.enum(['Pending', 'In Progress', 'Done']),
  newStatus: z.enum(['Pending', 'In Progress', 'Done'])
}).refine(data => {
  const transitions = {
    'Pending': ['In Progress'],
    'In Progress': ['Done'],
    'Done': []
  };
  return transitions[data.currentStatus].includes(data.newStatus);
}, { message: 'Invalid status transition' });
```

### Plan Validation

```typescript
const PlanStepSchema = z.object({
  title: z.string().min(1).max(200),
  description: z.string().min(1),
  estimatedDuration: z.number().int().positive().optional().or(z.null())
});

const PlanCreateSchema = z.object({
  taskId: z.string().uuid(),
  steps: z.array(PlanStepSchema).min(1)
});
```

### Activity Log Validation

```typescript
const ActivityLogSchema = z.object({
  type: z.string().max(50),
  description: z.string().max(500),
  metadata: z.record(z.unknown()).optional()
});
```

---

## State Machines

### Task Status State Machine

```
┌─────────┐
│ Pending │
└────┬────┘
     │ (update to In Progress)
     ▼
┌─────────────┐
│ In Progress │
└─────┬───────┘
      │ (update to Done)
      ▼
┌──────────┐
│   Done   │
└──────────┘

No backward transitions allowed.
```

### System State State Machine

```
┌────────┐
│  Idle  │◄────────────────────┐
└───┬────┘                     │
    │ (task received)          │ (plan delivered)
    ▼                          │
┌──────────┐                   │
│ Thinking │───────────┐       │
└────┬─────┘           │       │
     │ (analysis       │       │
     │  complete)      │       │
     ▼                 │       │
┌──────────┐           │       │
│ Planning │───────────┘       │
└──────────┘  (state machine)
```

---

## Migration Strategy

### Initial Migration

1. Create all tables in dependency order:
   - Tasks (no dependencies)
   - Plans (depends on Tasks)
   - PlanSteps (depends on Plans)
   - ActivityLogs (no dependencies)
   - SystemState (singleton)

2. Seed SystemState with initial row:
   ```sql
   INSERT INTO system_state (id, state, lastActivity)
   VALUES ('system-state-singleton', 'Idle', NOW());
   ```

### Future Migrations

- All schema changes require new migration files
- Backward compatibility maintained where possible
- Rollback scripts generated for each migration

---

## Query Patterns

### Common Task Queries

```typescript
// Get all tasks
prisma.task.findMany({ orderBy: { createdAt: 'desc' } })

// Get tasks by status
prisma.task.findMany({ where: { status: 'Pending' } })

// Get task with plan
prisma.task.findUnique({
  where: { id: taskId },
  include: { plan: { include: { steps: true } } }
})
```

### Common Plan Queries

```typescript
// Get all plans
prisma.plan.findMany({
  include: { steps: { orderBy: { order: 'asc' } } },
  orderBy: { createdAt: 'desc' }
})

// Get plan by task
prisma.plan.findUnique({ where: { taskId } })
```

### Activity Log Queries

```typescript
// Get recent activity
prisma.activityLog.findMany({
  orderBy: { timestamp: 'desc' },
  take: 100
})

// Get activity by time range
prisma.activityLog.findMany({
  where: {
    timestamp: {
      gte: startDate,
      lte: endDate
    }
  },
  orderBy: { timestamp: 'desc' }
})

// Get activity by type
prisma.activityLog.findMany({
  where: { type: 'task.created' }
})
```

### System State Queries

```typescript
// Get current state
prisma.systemState.findUnique({
  where: { id: 'system-state-singleton' }
})
```
