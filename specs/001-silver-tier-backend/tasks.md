# Tasks: Silver Tier Backend

**Input**: Design documents from `/specs/001-silver-tier-backend/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are INCLUDED in this task list following Test-First principles from the constitution.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3], [US4])
- Include exact file paths in descriptions

## Path Conventions

Backend API project structure:
- Source: `backend/src/`
- Tests: `backend/tests/`
- Prisma: `backend/prisma/`
- Config: `backend/.env`, `backend/tsconfig.json`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create backend project structure per implementation plan (backend/, backend/src/, backend/tests/, backend/prisma/)
- [ ] T002 Initialize Node.js project with TypeScript dependencies (backend/package.json, backend/tsconfig.json)
- [ ] T003 [P] Configure ESLint and Prettier (backend/.eslintrc.json, backend/.prettierrc)
- [ ] T004 [P] Create environment configuration template (backend/.env.example)
- [ ] T005 [P] Setup Jest test configuration (backend/jest.config.js, backend/tests/setup.ts)
- [ ] T006 [P] Create Dockerfile for production build (backend/Dockerfile)
- [ ] T007 [P] Create docker-compose.yml for local development (backend/docker-compose.yml with PostgreSQL)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Create Prisma schema with all entities (backend/prisma/schema.prisma) - Task, Plan, PlanStep, ActivityLog, SystemState
- [ ] T009 Create initial database migration (backend/prisma/migrations/)
- [ ] T010 Create database seed script for SystemState singleton (backend/prisma/seed.ts)
- [ ] T011 Setup environment configuration loader with Zod validation (backend/src/config/env.ts)
- [ ] T012 Create Express app configuration module (backend/src/app.ts)
- [ ] T013 Create application entry point (backend/src/index.ts)
- [ ] T014 [P] Create structured logging utility (backend/src/utils/logger.ts)
- [ ] T015 [P] Create custom error classes (backend/src/utils/errors.ts)
- [ ] T016 Create global error handling middleware (backend/src/middleware/error.handler.ts)
- [ ] T017 Create request logging middleware (backend/src/middleware/logger.ts)
- [ ] T018 Create Zod validation middleware (backend/src/middleware/validation.ts)
- [ ] T019 Create Prisma client export (backend/src/models/index.ts)
- [ ] T020 Create route aggregator (backend/src/routes/index.ts)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Task Management (Priority: P1) 🎯 MVP

**Goal**: Implement complete task CRUD with status transitions

**Independent Test**: Can be fully tested by creating a task via API, retrieving the task list, updating task status, and marking a task as complete. Each operation should persist and return correct data.

### Tests for User Story 1 ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T021 [P] [US1] Integration test for task creation in backend/tests/integration/tasks.test.ts (test POST /api/v1/tasks)
- [ ] T022 [P] [US1] Integration test for task listing in backend/tests/integration/tasks.test.ts (test GET /api/v1/tasks)
- [ ] T023 [P] [US1] Integration test for task status update in backend/tests/integration/tasks.test.ts (test PATCH /api/v1/tasks/:id/status)
- [ ] T024 [P] [US1] Unit test for TaskService in backend/tests/unit/services/task.service.test.ts

### Implementation for User Story 1

- [ ] T025 [P] [US1] Create Task type definitions (backend/src/models/task.model.ts)
- [ ] T026 [US1] Implement TaskService with CRUD operations (backend/src/services/task.service.ts)
- [ ] T027 [US1] Implement TaskService status transition validation (Pending → In Progress → Done only)
- [ ] T028 [P] [US1] Create task routes definition (backend/src/routes/task.routes.ts)
- [ ] T029 [US1] Create task controller with request/response handling (backend/src/controllers/task.controller.ts)
- [ ] T030 [US1] Create Zod schema for task validation (backend/src/config/env.ts or backend/src/validators/task.validator.ts)
- [ ] T031 [US1] Register task routes in route aggregator (backend/src/routes/index.ts)
- [ ] T032 [US1] Add activity logging for task operations (task.created, task.updated, task.deleted)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently
**MVP Validation**: Run integration tests in T021-T023, verify all pass

---

## Phase 4: User Story 2 - Plan Generation and Management (Priority: P2)

**Goal**: Implement AI-powered plan generation and plan management

**Independent Test**: Can be fully tested by triggering plan generation for an existing task, retrieving the generated plan, viewing plan lists, and updating plan status.

### Tests for User Story 2 ⚠️

- [ ] T033 [P] [US2] Integration test for plan generation in backend/tests/integration/plans.test.ts (test POST /api/v1/tasks/:taskId/plans)
- [ ] T034 [P] [US2] Integration test for plan retrieval in backend/tests/integration/plans.test.ts (test GET /api/v1/plans and GET /api/v1/plans/:id)
- [ ] T035 [P] [US2] Unit test for PlanService in backend/tests/unit/services/plan.service.test.ts
- [ ] T036 [P] [US2] Unit test for AI provider abstraction in backend/tests/unit/ai/provider.test.ts

### Implementation for User Story 2

- [ ] T037 [P] [US2] Create Plan and PlanStep type definitions (backend/src/models/plan.model.ts)
- [ ] T038 [US2] Implement PlanService with CRUD operations (backend/src/services/plan.service.ts)
- [ ] T039 [US2] Implement PlanService structured steps handling (ordered array with title, description, estimatedDuration)
- [ ] T040 [P] [US2] Create AI provider interface (backend/src/ai/provider.ts)
- [ ] T041 [P] [US2] Create AI provider factory (backend/src/ai/factory.ts)
- [ ] T042 [P] [US2] Create AI provider types (backend/src/ai/types.ts)
- [ ] T043 [US2] Implement plan generation via AI provider (integrates with TaskService)
- [ ] T044 [P] [US2] Create plan routes definition (backend/src/routes/plan.routes.ts)
- [ ] T045 [US2] Create plan controller with request/response handling (backend/src/controllers/plan.controller.ts)
- [ ] T046 [US2] Create Zod schema for plan validation (backend/src/validators/plan.validator.ts)
- [ ] T047 [US2] Register plan routes in route aggregator (backend/src/routes/index.ts)
- [ ] T048 [US2] Add activity logging for plan operations (plan.generated, plan.updated, plan.deleted)
- [ ] T049 [US2] Implement AI service unavailable error handling (503 response)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - System State Visibility (Priority: P3)

**Goal**: Implement system state tracking and health monitoring

**Independent Test**: Can be fully tested by querying the system state endpoint and verifying it returns accurate current state and recent activity timestamp.

### Tests for User Story 3 ⚠️

- [ ] T050 [P] [US3] Integration test for system state endpoint in backend/tests/integration/system.test.ts (test GET /api/v1/system/state)
- [ ] T051 [P] [US3] Integration test for health endpoint in backend/tests/integration/system.test.ts (test GET /api/v1/system/health)
- [ ] T052 [P] [US3] Unit test for SystemStateService in backend/tests/unit/services/system-state.service.test.ts

### Implementation for User Story 3

- [ ] T053 [P] [US3] Create SystemState type definition (backend/src/models/system-state.model.ts)
- [ ] T054 [US3] Implement SystemStateService with state machine (backend/src/services/system-state.service.ts)
- [ ] T055 [US3] Implement explicit state transitions (Idle → Thinking → Planning → Idle)
- [ ] T056 [P] [US3] Create system routes definition (backend/src/routes/system.routes.ts)
- [ ] T057 [US3] Create system controller for state and health endpoints (backend/src/controllers/system.controller.ts)
- [ ] T058 [US3] Register system routes in route aggregator (backend/src/routes/index.ts)
- [ ] T059 [US3] Add activity logging for state changes (state.changed events)
- [ ] T060 [US3] Integrate state machine triggers with TaskService and PlanService

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - Activity Log Access (Priority: P4)

**Goal**: Implement activity logging and queryable history

**Independent Test**: Can be fully tested by performing system actions, then querying the activity log to verify entries are created with accurate timestamps and action details.

### Tests for User Story 4 ⚠️

- [ ] T061 [P] [US4] Integration test for activity log query in backend/tests/integration/activity.test.ts (test GET /api/v1/activity-logs)
- [ ] T062 [P] [US4] Unit test for ActivityLogService in backend/tests/unit/services/activity-log.service.test.ts

### Implementation for User Story 4

- [ ] T063 [P] [US4] Create ActivityLog type definition (backend/src/models/activity-log.model.ts)
- [ ] T064 [US4] Implement ActivityLogService with logging and querying (backend/src/services/activity-log.service.ts)
- [ ] T065 [US4] Implement ActivityLogService time-range filtering and pagination
- [ ] T066 [P] [US4] Create activity log routes definition (backend/src/routes/activity.routes.ts)
- [ ] T067 [US4] Create activity log controller with request/response handling (backend/src/controllers/activity.controller.ts)
- [ ] T068 [US4] Register activity routes in route aggregator (backend/src/routes/index.ts)
- [ ] T069 [US4] Integrate ActivityLogService with all other services (TaskService, PlanService, SystemStateService, AI provider)

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and production readiness

- [ ] T070 [P] Implement CORS configuration via environment variables (backend/src/config/cors.ts, backend/src/app.ts)
- [ ] T071 [P] Verify NODE_ENV behavior (development vs production error handling)
- [ ] T072 [P] Remove localhost assumptions (verify CORS_ORIGIN, DATABASE_URL work with any host)
- [ ] T073 [P] Ensure no secrets in logs (audit logging statements, mask sensitive data)
- [ ] T074 [P] Create API documentation (backend/README.md or OpenAPI spec)
- [ ] T075 [P] Update quickstart.md with final setup instructions (backend/QUICKSTART.md or specs/001-silver-tier-backend/quickstart.md)
- [ ] T076 [P] Run all integration tests and verify pass rate (npm test)
- [ ] T077 [P] Build Docker image and verify it runs (docker build, docker run)
- [ ] T078 [P] Code cleanup and refactoring (remove unused code, improve error messages)
- [ ] T079 [P] Performance optimization (database indexes, query optimization)
- [ ] T080 [P] Security review (input validation, error message sanitization)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 - Task Management (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 - Plan Generation (P2)**: Can start after Foundational (Phase 2) - Depends on Task entity existing, independently testable
- **User Story 3 - System State (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 - Activity Log (P4)**: Can start after Foundational (Phase 2) - Integrates with all services but independently testable

### Within Each User Story

1. Tests (TDD) MUST be written and FAIL before implementation
2. Models before services
3. Services before controllers/routes
4. Core implementation before integration
5. Story complete before moving to next priority

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004, T005, T006, T007 can all run in parallel (different files)

**Phase 2 (Foundational)**:
- T014, T015 can run in parallel (different utility files)
- T008-T013, T016-T020 have sequential dependencies

**Phase 3-6 (User Stories)**:
- Once Phase 2 completes, all user story phases can run in parallel with different developers
- Within each story:
  - All test tasks marked [P] can run in parallel
  - All model tasks marked [P] can run in parallel
  - Routes can be created in parallel with services (different files)

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
# Developer A works on T021-T024 (tests)
Task: "Integration test for task creation in backend/tests/integration/tasks.test.ts"
Task: "Integration test for task listing in backend/tests/integration/tasks.test.ts"
Task: "Integration test for task status update in backend/tests/integration/tasks.test.ts"
Task: "Unit test for TaskService in backend/tests/unit/services/task.service.test.ts"

# Developer B works on T025 (models) - can start after tests are written
Task: "Create Task type definitions in backend/src/models/task.model.ts"

# Developer C works on T028 (routes) - can start in parallel with service implementation
Task: "Create task routes definition in backend/src/routes/task.routes.ts"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T007)
2. Complete Phase 2: Foundational (T008-T020)
3. Complete Phase 3: User Story 1 (T021-T032)
4. **STOP and VALIDATE**: Run integration tests T021-T023
5. Deploy/demo MVP: Task CRUD API is production-ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Task Management) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Plan Generation) → Test independently → Deploy/Demo
4. Add User Story 3 (System State) → Test independently → Deploy/Demo
5. Add User Story 4 (Activity Log) → Test independently → Deploy/Demo
6. Complete Phase 7 (Polish) → Production hardening

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T020)
2. Once Foundational is done:
   - Developer A: User Story 1 - Task Management (T021-T032)
   - Developer B: User Story 2 - Plan Generation (T033-T049)
   - Developer C: User Story 3 - System State (T050-T060)
   - Developer D: User Story 4 - Activity Log (T061-T069)
3. All stories complete and integrate independently
4. Team reconvenes for Phase 7 (Polish)

---

## Task Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 7 tasks |
| Phase 2 | Foundational | 13 tasks |
| Phase 3 | User Story 1 (Task Management) | 12 tasks (4 tests + 8 implementation) |
| Phase 4 | User Story 2 (Plan Generation) | 17 tasks (4 tests + 13 implementation) |
| Phase 5 | User Story 3 (System State) | 11 tasks (3 tests + 8 implementation) |
| Phase 6 | User Story 4 (Activity Log) | 9 tasks (2 tests + 7 implementation) |
| Phase 7 | Polish & Cross-Cutting | 11 tasks |
| **Total** | **All phases** | **80 tasks** |

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing (TDD)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP scope: Phases 1-3 (32 tasks) delivers working Task Management API
