# Implementation Plan: Platinum Tier Backend Upgrade

**Branch**: `001-platinum-tier-backend` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification for autonomous multi-agent platform.

## Summary
The Platinum Tier Upgrade transforms the system from a task executor into an autonomous AI workforce. This is achieved through a hierarchical planning engine, a global vector-based memory system, and a multi-agent collaboration layer that leverages specialized agents (Planner, RiskAssessment, etc.) coordinated via an orchestrator. All operations are governed by cost monitoring and human-in-the-loop approvals.

## Technical Context

**Language/Version**: Node.js v20 LTS + TypeScript  
**Primary Dependencies**: Prisma, BullMQ, `js-tiktoken`, `pgvector`  
**Storage**: PostgreSQL (with `pgvector` extension), Redis  
**Testing**: Jest (Unit & Integration)  
**Target Platform**: Linux (Docker)
**Project Type**: Single Backend Service
**Performance Goals**: 
  - Goal decomposition < 30 seconds (P95)
  - Memory recall < 500ms (P95)
  - Cost tracking latency < 1 second
**Constraints**: 
  - Mandatory plan approval before execution
  - Real-time cost threshold alerts
  - Full auditability of tool invocations
**Scale/Scope**: Support for complex goals with up to 50 sub-tasks and 10+ concurrent agents.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Test-First**: TDD mandatory for Agents and Orchestrator. [PASS]
- **II. CLI Interface**: `quickstart.md` provides curl examples for all goal operations. [PASS]
- **III. Observability**: Structured JSON logging for all agent reasoning and tool calls. [PASS]
- **V. Simplicity (YAGNI)**: Using `pgvector` instead of a separate vector DB. [PASS]
- **VI. Async-First**: All planning and execution handled via BullMQ workers. [PASS]

## Project Structure

### Documentation (this feature)

```text
specs/001-platinum-tier-backend/
├── plan.md              # This file
├── research.md          # Research findings (pgvector, planning strategy)
├── data-model.md        # DB schema (Goal, Task, AgentExecution, etc.)
├── quickstart.md        # Curl examples for Platinum Tier
├── contracts/           
│   └── openapi.yaml     # API definitions
└── tasks.md             # Implementation tasks
```

### Source Code

```text
src/
├── agents/             # Specialized Agent definitions
├── orchestrator/       # Agent collaboration and planning logic
├── memory/             # Vector retrieval and context injection
├── cost/               # Token accounting and threshold monitoring
├── tools/              # MCP-compatible tool shims
├── models/             # Prisma schema and types
├── services/           # Business logic (GoalService, TaskService)
├── workers/            # BullMQ job processors
└── api/                # REST endpoints
```

## Phases

### Phase 1 – Agent Architecture
- **Goal**: Define and implement the specialized agent roles.
- **Components**: `BaseAgent`, `TaskAnalyzerAgent`, `PlannerAgent`, `RiskAssessmentAgent`, `MemoryAgent`, `SupervisorAgent`.
- **Expected Artifacts**: Agent class definitions, prompt templates for each role.
- **Done Criteria**: Each agent can be instantiated and respond to a test prompt within its domain.

### Phase 2 – Autonomous Planning Engine
- **Goal**: Implement high-level goal creation and task decomposition.
- **Components**: `GoalService`, `DecompositionWorker`, `PlannerAgent`.
- **Expected Artifacts**: Recursive task decomposition logic, plan approval workflow.
- **Done Criteria**: A high-level goal is successfully broken into actionable tasks and stored in `PENDING_APPROVAL` state.

### Phase 3 – Memory System
- **Goal**: Implement vector-based context retrieval.
- **Components**: `MemoryService`, `pgvector` integration, `MemoryAgent`.
- **Expected Artifacts**: Vector embedding generation logic, semantic search queries.
- **Done Criteria**: Agents can retrieve relevant historical context for a new task via semantic search.

### Phase 4 – Agent Collaboration
- **Goal**: Coordinate work between agents through the Orchestrator.
- **Components**: `Orchestrator`, `AgentCommunicationBus` (BullMQ-based).
- **Expected Artifacts**: Multi-stage agent reasoning loops, state management for concurrent agents.
- **Done Criteria**: The `SupervisorAgent` successfully reviews and approves/rejects an execution proposal from another agent.

### Phase 5 – Tool Execution Framework
- **Goal**: Implement safe external tool invocation.
- **Components**: `ToolManager`, `MCPBridge`, `RiskAssessmentAgent`.
- **Expected Artifacts**: Tool registry, dynamic risk scoring logic, tool invocation logging.
- **Done Criteria**: A tool is executed only after passing risk assessment and (if high risk) human approval.

### Phase 6 – Cost Monitoring
- **Goal**: Track token usage and AI cost metrics.
- **Components**: `CostMonitoringService`, `TiktokenEstimator`.
- **Expected Artifacts**: Real-time cost logging, threshold alert triggers, pause execution logic.
- **Done Criteria**: System automatically pauses execution when the cumulative cost exceeds the user-defined threshold.

### Phase 7 – Reliability Layer
- **Goal**: Implement retry logic and failure recovery.
- **Components**: BullMQ retry policies, `DeadLetterQueueHandler`, `SelfImprovementEngine`.
- **Expected Artifacts**: Job recovery logic, error analysis prompts for self-improvement.
- **Done Criteria**: Failed tasks are analyzed for optimizations and moved to a DLQ for human review if retries fail.

### Phase 8 – Observability
- **Goal**: Implement execution logs and performance metrics.
- **Components**: `ExecutionLogger`, `MetricsService`.
- **Expected Artifacts**: JSON trace logs for goal lifecycles, performance dashboards.
- **Done Criteria**: A full trace of a goal's journey from submission to completion is available via logs.
