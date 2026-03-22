# Tasks: Platinum Tier Backend Upgrade

**Input**: Design documents from `specs/001-platinum-tier-backend/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/openapi.yaml

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure for agents, orchestrator, memory, and tools per plan.md
- [X] T002 Update `prisma/schema.prisma` with Goal, Task, AgentExecution, MemoryRecord, CostLog, and ToolInvocation entities
- [X] T003 [P] Configure `pgvector` extension and vector column for MemoryRecord in database
- [X] T004 Initialize BullMQ queues for decomposition and agent execution in `src/workers/queues.ts`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core agent architecture and orchestrator base that MUST be complete before ANY user story can be implemented

- [X] T005 Implement `BaseAgent` abstract class in `src/agents/base_agent.ts`
- [X] T006 [P] Create prompt templates for all specialized agents in `src/agents/prompts/`
- [X] T007 Implement basic `Orchestrator` class for agent coordination in `src/orchestrator/orchestrator.ts`
- [X] T008 [P] Setup centralized error handling and structured JSON logging in `src/lib/logger.ts` and `src/middleware/error_handler.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Autonomous Goal Planning (Priority: P1) 🎯 MVP

**Goal**: Decompose complex goals into actionable tasks autonomously after user approval.

**Independent Test**: Submit a goal, verify it decomposes into tasks, approve the plan, and verify tasks are ready for execution.

### Implementation for User Story 1

- [X] T009 [P] [US1] Implement `Goal` and `Task` repository logic in `src/models/goal_model.ts` and `src/models/task_model.ts`
- [X] T010 [US1] Implement `PlannerAgent` for task decomposition in `src/agents/planner_agent.ts`
- [X] T011 [US1] **[CONSTITUTION]** Write unit tests for `GoalService` in `tests/unit/test_goal_service.ts` (TDD)
- [X] T012 [US1] Implement `GoalService` with goal submission, idempotency, and plan retrieval in `src/services/goal_service.ts`
- [X] T013 [US1] **[CONSTITUTION]** Write unit tests for `DecompositionWorker` in `tests/unit/test_decomposition_worker.ts`
- [X] T014 [US1] Implement `DecompositionWorker` with idempotent job processing in `src/workers/decomposition_worker.ts`
- [X] T015 [US1] Implement `POST /api/goals` endpoint for goal submission in `src/api/goal_routes.ts`
- [X] T016 [US1] Implement `GET /api/goals/{goal_id}/plan` and `POST /api/goals/{goal_id}/plan` for plan review and approval in `src/api/goal_routes.ts`
- [X] T017 [US1] Add integration test for goal-to-plan approval workflow in `tests/integration/test_goal_planning.ts`

**Checkpoint**: User Story 1 is functional. The system can now plan tasks autonomously.

---

## Phase 4: User Story 2 - Memory-Informed Decision Making (Priority: P2)

**Goal**: Utilize global long-term memory to inform agent reasoning and planning.

**Independent Test**: Perform a task, store its result in memory, and verify a subsequent similar task references the previous context.

### Implementation for User Story 2

- [X] T018 [P] [US2] Implement `MemoryRecord` repository logic with vector search in `src/models/memory_model.ts`
- [ ] T019 [US2] **[CONSTITUTION]** Write unit tests for `MemoryService` in `tests/unit/test_memory_service.ts`
- [X] T020 [US2] Create `MemoryService` for semantic storage and retrieval in `src/services/memory_service.ts`
- [X] T021 [US2] Implement `MemoryAgent` for context injection into agent prompts in `src/agents/memory_agent.ts`
- [X] T022 [US2] Update `Orchestrator` to query `MemoryService` and inject context into `PlannerAgent` and execution agents in `src/orchestrator/orchestrator.ts`
- [X] T023 [US2] Add integration test for memory recall during planning in `tests/integration/test_memory_recall.ts`

**Checkpoint**: User Story 2 is functional. Agents now have long-term memory.

---

## Phase 5: User Story 3 - Cost Monitoring and Alerting (Priority: P2)

**Goal**: Track AI costs in real-time and pause execution when thresholds are reached.

**Independent Test**: Set a low cost threshold, run an agent task, and verify execution pauses once the threshold is exceeded.

### Implementation for User Story 3

- [X] T024 [P] [US3] Implement `CostLog` repository logic in `src/models/cost_model.ts`
- [ ] T025 [US3] **[CONSTITUTION]** Write unit tests for `CostMonitoringService` in `tests/unit/test_cost_service.ts`
- [X] T026 [US3] Implement `CostMonitoringService` with `js-tiktoken` for real-time estimation in `src/services/cost_service.ts`
- [X] T027 [US3] Implement `GET /api/cost/threshold` and `POST /api/cost/threshold` endpoints in `src/api/cost_routes.ts`
- [X] T028 [US3] Update agent execution loop to log costs and check thresholds in `src/orchestrator/orchestrator.ts`
- [X] T029 [US3] Implement execution pausing logic in `src/services/goal_service.ts` when a threshold alert is triggered
- [X] T030 [US3] Add integration test for cost threshold enforcement in `tests/integration/test_cost_monitoring.ts`

**Checkpoint**: User Story 3 is functional. AI spending is now controlled.

---

## Phase 6: User Story 4 - Secure External Tool Invocation (Priority: P3)

**Goal**: Execute external tools securely with dynamic risk assessment and human-in-the-loop.

**Independent Test**: Agent requests a tool, RiskAssessmentAgent scores it, and it executes only after required approvals (threshold score > 0.7).

### Implementation for User Story 4

- [X] T031 [P] [US4] Implement `ToolInvocation` repository logic in `src/models/tool_model.ts`
- [ ] T032 [US4] **[CONSTITUTION]** Write unit tests for `ToolManager` and `RiskAssessmentAgent` in `tests/unit/test_tool_logic.ts`
- [X] T033 [US4] Implement `RiskAssessmentAgent` for dynamic risk scoring of tool calls in `src/agents/risk_agent.ts`
- [X] T034 [US4] Create `ToolManager` and `MCPBridge` for secure tool execution in `src/services/tool_service.ts` and `src/tools/mcp_bridge.ts`
- [X] T035 [US4] Implement `GET /api/tools/approvals` and `POST /api/tools/approvals` for human-in-the-loop tool review in `src/api/tool_routes.ts`
- [X] T036 [US4] Update `Orchestrator` to route tool calls through `RiskAssessmentAgent` and `SupervisorAgent` in `src/orchestrator/orchestrator.ts`
- [X] T037 [US4] Add integration test for high-risk tool approval workflow (score > 0.7) in `tests/integration/test_tool_security.ts`

**Checkpoint**: User Story 4 is functional. External tools are executed securely.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Reliability, self-improvement, and observability.

- [ ] T038 Implement `SelfImprovementEngine` to analyze failures and suggest optimizations in `src/orchestrator/self_improvement.ts`
- [ ] T039 [P] Configure BullMQ retry policies and Dead Letter Queue handling in `src/workers/dlq_handler.ts`
- [X] T040 [P] Implement `/api/metrics` endpoint for real-time execution statistics in `src/api/metrics_routes.ts`
- [ ] T041 **[MEASURABLE]** Implement success criteria validation tasks: Verify cost estimate accuracy (SC-004) and memory recall relevance (SC-003) in `tests/qa/benchmark_metrics.ts`
- [ ] T042 Final audit of all logs for PII and sensitive data leakage per constitution
- [ ] T043 Run validation of `quickstart.md` scenarios against the final implementation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately.
- **Foundational (Phase 2)**: Depends on Setup (T001-T004) - BLOCKS all user stories.
- **User Stories (Phase 3-6)**: All depend on Foundational completion (T005-T008).
  - US1 (Phase 3) is the MVP and should be completed first.
  - US2, US3, and US4 can proceed in parallel once Phase 2 is done.
- **Polish (Phase 7)**: Depends on all user stories being complete.

### User Story Dependencies

- **US1 (P1)**: Foundation for all autonomous behavior.
- **US2 (P2)**: Enhances US1 with memory.
- **US3 (P2)**: Adds guardrails to US1 execution.
- **US4 (P3)**: Adds tool capabilities to US1 execution.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (US1) - ENSURE unit tests and idempotency logic are prioritized.
3. **STOP and VALIDATE**: Test that a goal can be decomposed into a plan and approved.

### Incremental Delivery

1. Foundation -> Planning (US1) -> Memory (US2) -> Costs (US3) -> Tools (US4) -> Reliability (Polish).
2. Each step adds a core "Platinum" capability.

---

## Notes

- **[CONSTITUTION]** tasks = mandated unit tests and idempotency requirements.
- **[MEASURABLE]** tasks = verification of success criteria defined in `spec.md`.
- All tool calls MUST be logged and risk-scored.
- Cost monitoring MUST be real-time.
- All failed background jobs MUST be recoverable from DLQ.
