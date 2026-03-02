# Implementation Plan: Silver Tier Backend

**Branch**: `001-silver-tier-backend` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-silver-tier-backend/spec.md`

## Summary

The Silver Tier Backend implementation will create a production-grade Node.js/TypeScript backend service that exposes REST APIs for task management, plan generation, agent state tracking, and activity logging. The system uses PostgreSQL for persistent storage with Prisma ORM for database operations, Express for the API layer, and Zod for runtime validation. The backend will be Docker-ready with environment-based configuration and will serve as the foundation for Silver-tier frontend integration.

## Technical Context

**Language/Version**: Node.js (latest LTS - 20.x), TypeScript 5.x
**Primary Dependencies**: Express (or Fastify), Prisma ORM, Zod validation library
**Storage**: PostgreSQL (relational database for Tasks, Plans, ActivityLogs, SystemState)
**Testing**: Jest (unit tests), Supertest (integration/API tests)
**Target Platform**: Linux server / Docker container - backend API service
**Project Type**: Backend API (single project with service-layer architecture)
**Performance Goals**: 
- Task CRUD operations: <2s response time under normal load
- List operations (100 items): <1s response time
- Health/state queries: <500ms response time
- Activity log queries (1000 entries): <2s response time
**Constraints**:
- No hardcoded secrets (all config via environment variables)
- CORS configurable via environment
- No localhost assumptions (production-ready configuration)
- Docker-ready but not full cloud automation
- Silver-tier scope only (no auth, no WebSockets, no background queues)
**Scale/Scope**:
- Single-user system (no authentication required)
- Single instance deployment (no distributed state)
- Local/development to production-ready progression

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Compliance Verification

**Test-First**: ✅ Confirmed - Unit and integration tests required for all services and endpoints
**Observability**: ✅ Confirmed - Structured logging, activity logging, health endpoints planned
**Simplicity**: ✅ Confirmed - Silver-tier scope only, YAGNI principles applied (no auth, no multi-tenant)
**CLI Interface**: N/A - Backend API service (not a CLI tool)
**Library-First**: N/A - Service-based backend architecture

### Post-Design Compliance Verification

**Test-First**: ✅ Confirmed - Test directories planned (tests/unit/, tests/integration/) with Jest + Supertest
**Observability**: ✅ Confirmed - ActivityLog entity for system actions, health endpoints, structured logging middleware
**Simplicity**: ✅ Confirmed - Service-layer architecture is standard pattern, no over-engineering detected
**CLI Interface**: N/A - Maintained as backend API service
**Library-First**: N/A - Maintained as service-based architecture

### Gate Status: PASSED
All constitutional requirements satisfied for Silver tier backend implementation.

## Project Structure

### Documentation (this feature)

```text
specs/001-silver-tier-backend/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Generated Artifacts

The following artifacts have been generated during the planning phase:

- `research.md` - Technology decisions (Express, Prisma, Zod, Jest) and implementation patterns
- `data-model.md` - Complete Prisma schema with Task, Plan, PlanStep, ActivityLog, SystemState entities
- `quickstart.md` - Setup guide with installation, configuration, and troubleshooting
- `contracts/api-contract.md` - Full REST API specification with all endpoints and error codes
- Agent context updated in `QWEN.md` with Silver tier technologies (Node.js, TypeScript, Express, Prisma, PostgreSQL, Zod)

### Source Code (repository root)

```text
backend/
├── src/
│   ├── index.ts                    # Application entry point
│   ├── app.ts                      # Express app configuration
│   ├── config/
│   │   ├── index.ts                # Configuration loader
│   │   ├── env.ts                  # Environment variable schema (Zod)
│   │   └── cors.ts                 # CORS configuration
│   ├── services/
│   │   ├── task.service.ts         # Task domain logic
│   │   ├── plan.service.ts         # Plan domain logic
│   │   ├── activity-log.service.ts # Activity logging
│   │   └── system-state.service.ts # System state management
│   ├── controllers/
│   │   ├── task.controller.ts      # Task HTTP handlers
│   │   ├── plan.controller.ts      # Plan HTTP handlers
│   │   ├── activity.controller.ts  # Activity log HTTP handlers
│   │   └── system.controller.ts    # System state/health handlers
│   ├── routes/
│   │   ├── index.ts                # Route aggregator
│   │   ├── task.routes.ts          # Task endpoints
│   │   ├── plan.routes.ts          # Plan endpoints
│   │   ├── activity.routes.ts      # Activity log endpoints
│   │   └── system.routes.ts        # System endpoints
│   ├── middleware/
│   │   ├── error.handler.ts        # Global error handling
│   │   ├── validation.ts           # Zod validation middleware
│   │   └── logger.ts               # Request logging
│   ├── models/
│   │   ├── index.ts                # Prisma client export
│   │   ├── task.model.ts           # Task type definitions
│   │   ├── plan.model.ts           # Plan type definitions
│   │   ├── activity-log.model.ts   # ActivityLog type definitions
│   │   └── system-state.model.ts   # SystemState type definitions
│   ├── ai/
│   │   ├── provider.ts             # Abstract AI provider interface
│   │   ├── factory.ts              # AI provider factory
│   │   └── types.ts                # AI provider types
│   └── utils/
│       ├── logger.ts               # Structured logging utility
│       └── errors.ts               # Custom error classes
├── prisma/
│   ├── schema.prisma               # Database schema
│   ├── migrations/                 # Database migrations
│   └── seed.ts                     # Optional seed data
├── tests/
│   ├── unit/
│   │   ├── services/               # Service layer tests
│   │   └── middleware/             # Middleware tests
│   ├── integration/
│   │   ├── tasks.test.ts           # Task API tests
│   │   ├── plans.test.ts           # Plan API tests
│   │   ├── activity.test.ts        # Activity log API tests
│   │   └── system.test.ts          # System endpoint tests
│   └── setup.ts                    # Test configuration
├── Dockerfile                      # Docker container definition
├── docker-compose.yml              # Local development stack
├── .env.example                    # Environment template
├── tsconfig.json                   # TypeScript configuration
├── jest.config.js                  # Jest test configuration
└── package.json                    # Dependencies and scripts
```

**Structure Decision**: Backend API structure with service-layer architecture chosen to enforce clear separation of concerns (controllers → services → models) and support Silver-tier requirements.

## Implementation Phases

### Phase 0: Research & Technology Decisions

**Goal**: Resolve all technology choices and establish best practices

**Tasks**:
- Research Express vs Fastify for Silver-tier requirements
- Define Prisma schema patterns for Task/Plan/ActivityLog/SystemState
- Establish AI provider abstraction pattern
- Define Docker configuration for development and production

**Output**: `research.md` with all technology decisions documented

---

### Phase 1: Project Initialization & Database Layer

**Goal**: Establish project foundation with database connectivity

**Deliverables**:
- Node.js/TypeScript project structure
- Prisma schema with all entities
- Database migrations
- Environment configuration loader

**Done Criteria**:
- [ ] `npm install` succeeds
- [ ] TypeScript compiles without errors
- [ ] Prisma schema validates
- [ ] Database migrations run successfully
- [ ] Environment variables load correctly

---

### Phase 2: Core Domain Services

**Goal**: Implement business logic for all four domains

**Deliverables**:
- Task service (CRUD + status transitions)
- Plan service (CRUD + structured steps)
- Activity log service (logging + querying)
- System state service (state machine + health)

**Done Criteria**:
- [ ] All services have unit tests
- [ ] Task status transitions enforce linear progression
- [ ] Plans store structured steps correctly
- [ ] Activity logging captures required events
- [ ] System state machine transitions correctly

---

### Phase 3: API Layer & Controllers

**Goal**: Expose services via REST endpoints

**Deliverables**:
- REST routes for all entities
- Controllers with Zod validation
- Error handling middleware
- Request logging

**Done Criteria**:
- [ ] All endpoints return correct HTTP status codes
- [ ] Validation errors return 400 with clear messages
- [ ] Not found returns 404
- [ ] Server errors return 500 without leaking internals
- [ ] Integration tests pass for all endpoints

---

### Phase 4: AI Integration Layer

**Goal**: Abstract AI provider for configurable AI access

**Deliverables**:
- Abstract AI provider interface
- Environment-driven provider selection
- Safe API key handling (runtime only)
- AI invocation for plan generation

**Done Criteria**:
- [ ] AI provider configurable via environment
- [ ] No API keys in source code
- [ ] Plan generation endpoint triggers AI correctly
- [ ] AI unavailability handled gracefully

---

### Phase 5: System Health & CORS

**Goal**: Production readiness with monitoring and security

**Deliverables**:
- `/health` endpoint
- `/system-state` endpoint
- Configurable CORS middleware
- Environment-based behavior

**Done Criteria**:
- [ ] Health endpoint responds in <500ms
- [ ] System state reflects actual state accurately
- [ ] CORS configured via environment variables
- [ ] No localhost assumptions in configuration

---

### Phase 6: Validation & Hardening

**Goal**: Ensure production readiness

**Deliverables**:
- Error handling review
- Environment safety verification
- Docker build verification
- Production readiness checklist

**Done Criteria**:
- [ ] No secrets in source code (verified by scan)
- [ ] All environment variables documented
- [ ] Docker build succeeds
- [ ] All integration tests pass
- [ ] Performance targets met

---

## Complexity Tracking

No complexity violations detected. Silver-tier scope maintained with:
- Single-user mode (no auth complexity)
- Single instance (no distributed state)
- Service-layer architecture (standard pattern)
- REST API (standard approach)
