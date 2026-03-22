# Tasks: Platinum Tier Frontend – AI Workforce Control Center

**Input**: Design documents from `/specs/001-platinum-tier-frontend/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1–US7)
- Exact file paths included

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, environment config, shared utilities

- [x] T001 Configure environment variables `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL` in `frontend/.env.local` and update `frontend/.env.example`
- [x] T002 [P] Create API client wrapper in `frontend/src/lib/api-client.ts` using axios with base URL from `NEXT_PUBLIC_API_URL` env var
- [x] T003 [P] Create WebSocket client in `frontend/src/lib/websocket-client.ts` with exponential backoff reconnection (1s→2s→4s→8s…max 30s), connection state tracking, and event dispatch
- [x] T004 [P] Create `useWebSocket` hook in `frontend/src/hooks/use-websocket.ts` wrapping WebSocket client with React context, exposing connection status and subscribe/unsubscribe methods
- [x] T005 Install recharts dependency: `cd frontend && npm install recharts`

**Checkpoint**: API client and WebSocket infrastructure ready for all pages

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared UI components and navigation that ALL pages depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Update sidebar navigation in `frontend/src/components/shared/sidebar.tsx` to add 6 new nav items: Agents, Goals, Memory, Costs, Tools, Intelligence with lucide-react icons
- [x] T007 [P] Create `ConnectionStatus` banner component in `frontend/src/components/shared/connection-status.tsx` that shows/hides based on WebSocket connection state from `useWebSocket` hook
- [x] T008 [P] Create `SkeletonLoader` component in `frontend/src/components/shared/skeleton-loader.tsx` with variants for card, list, chart, and table layouts
- [x] T009 [P] Create `EmptyState` component in `frontend/src/components/shared/empty-state.tsx` accepting icon, title, description, and optional action button props
- [x] T010 [P] Create `Pagination` component in `frontend/src/components/shared/pagination.tsx` with page size selector (10/20/50), page navigation, and total count display
- [x] T011 Add `ConnectionStatus` to root layout in `frontend/src/app/layout.tsx` and wrap app with WebSocket provider

**Checkpoint**: Foundation ready — user story implementation can begin

---

## Phase 3: User Story 1 – View and Control AI Agents (Priority: P1) MVP

**Goal**: Operators can see all agents, their statuses, and start/stop them.

**Independent Test**: Navigate to /agents, see agent list with status badges, start/stop an agent and confirm UI updates within 2s.

### Implementation for User Story 1

- [x] T012 [P] [US1] Create `useAgents` hook in `frontend/src/hooks/use-agents.ts` with TanStack Query for `GET /api/agents`, mutations for `POST /api/agents/:id/start` and `POST /api/agents/:id/stop`, and WebSocket subscription for `agent:status` events that invalidate the query cache
- [x] T013 [P] [US1] Create `AgentStatusBadge` component in `frontend/src/components/agents/agent-status-badge.tsx` with color-coded badges: running=green, stopped=gray, error=red using shadcn Badge
- [x] T014 [US1] Create `AgentCard` component in `frontend/src/components/agents/agent-card.tsx` displaying agent name, type, status badge, error message (if error), and Start/Stop buttons that call mutations from `useAgents`
- [x] T015 [US1] Create `AgentList` component in `frontend/src/components/agents/agent-list.tsx` rendering a grid of `AgentCard` components with skeleton loader during loading and empty state when no agents
- [x] T016 [US1] Create agents page in `frontend/src/app/agents/page.tsx` composing `AgentList` with page title and description

**Checkpoint**: Agent list with start/stop controls fully functional

---

## Phase 4: User Story 2 – View Agent Logs (Priority: P1)

**Goal**: Operators can view real-time streaming logs for any selected agent.

**Independent Test**: Select an agent, open log viewer, confirm logs stream in real time and can be filtered by severity.

### Implementation for User Story 2

- [x] T017 [P] [US2] Create `useAgentLogs` hook in `frontend/src/hooks/use-agent-logs.ts` with TanStack Query for `GET /api/agents/:id/logs` (paginated), WebSocket subscription for `agent:log` events filtered by agent ID, and severity filter state
- [x] T018 [US2] Create `AgentLogViewer` component in `frontend/src/components/agents/agent-log-viewer.tsx` with severity filter buttons (All/Info/Warn/Error), auto-scrolling log list with timestamps, severity color coding, and virtualized scroll for performance
- [x] T019 [US2] Update `AgentCard` in `frontend/src/components/agents/agent-card.tsx` to add "View Logs" button that expands/opens the `AgentLogViewer` for that agent
- [x] T020 [US2] Update agents page `frontend/src/app/agents/page.tsx` to support agent selection and log panel display (side panel or expandable section)

**Checkpoint**: Real-time agent logs viewable with severity filtering

---

## Phase 5: User Story 3 – Manage Strategic Goals (Priority: P2)

**Goal**: Operators can create goals, track progress, and visualize task breakdowns.

**Independent Test**: Create a goal, see it listed with progress bar, view task breakdown with statuses.

### Implementation for User Story 3

- [x] T021 [P] [US3] Create `useGoals` hook in `frontend/src/hooks/use-goals.ts` with TanStack Query for goals CRUD: `GET /api/goals`, `POST /api/goals`, `GET /api/goals/:id`, `PATCH /api/goals/:id`, `DELETE /api/goals/:id`
- [x] T022 [P] [US3] Create `GoalForm` component in `frontend/src/components/goals/goal-form.tsx` with fields for title, description, priority (low/medium/high/critical) using shadcn form components with validation
- [x] T023 [US3] Create `GoalCard` component in `frontend/src/components/goals/goal-card.tsx` displaying title, priority badge, status badge (Draft/Active/Completed/Cancelled), progress bar, and state transition buttons enforcing valid transitions (Draft→Active→Completed, Cancel from Draft/Active)
- [x] T024 [US3] Create `TaskBreakdown` component in `frontend/src/components/goals/task-breakdown.tsx` showing visual tree/list of sub-tasks with status indicators (pending/in-progress/completed/failed) and overall progress
- [x] T025 [US3] Create `GoalList` component in `frontend/src/components/goals/goal-list.tsx` rendering goal cards with skeleton/empty states and a "Create Goal" button that opens `GoalForm`
- [x] T026 [US3] Create goals page in `frontend/src/app/goals/page.tsx` composing `GoalList` with goal detail panel showing `TaskBreakdown` when a goal is selected

**Checkpoint**: Goal CRUD with state transitions and task breakdown visualization working

---

## Phase 6: User Story 4 – Explore AI Memory (Priority: P2)

**Goal**: Operators can search AI memory, view entries with similarity scores, and inspect details.

**Independent Test**: Search for a term, see ranked results with similarity scores, click to view full context.

### Implementation for User Story 4

- [x] T027 [P] [US4] Create `useMemory` hook in `frontend/src/hooks/use-memory.ts` with TanStack Query for `GET /api/memory/search?q=&limit=&offset=` and `GET /api/memory/:id`, with debounced search (300ms)
- [x] T028 [P] [US4] Create `MemorySearch` component in `frontend/src/components/memory/memory-search.tsx` with search input, debounced query dispatch, and loading indicator
- [x] T029 [US4] Create `MemoryResultList` component in `frontend/src/components/memory/memory-result-list.tsx` displaying results ranked by similarity score with score badge, content preview, source, and agent name, paginated at 20/page
- [x] T030 [US4] Create `MemoryDetail` component in `frontend/src/components/memory/memory-detail.tsx` showing full content, metadata (source, timestamp, agent), and similarity score in a slide-over or modal panel
- [x] T031 [US4] Create memory page in `frontend/src/app/memory/page.tsx` composing `MemorySearch`, `MemoryResultList`, and `MemoryDetail` with empty state showing suggestions when no results

**Checkpoint**: Memory search with similarity scores and detail view working

---

## Phase 7: User Story 5 – Monitor AI Costs (Priority: P2)

**Goal**: Operators can see cost summaries, time-series charts, and per-agent/model breakdowns.

**Independent Test**: Navigate to /costs, see summary cards, chart with date range selector, and breakdown table.

### Implementation for User Story 5

- [x] T032 [P] [US5] Create `useCosts` hook in `frontend/src/hooks/use-costs.ts` with TanStack Query for `GET /api/costs/summary?period=` and `GET /api/costs/timeseries?period=&from=&to=` with period selector state (day/week/month)
- [x] T033 [P] [US5] Create `CostSummary` component in `frontend/src/components/costs/cost-summary.tsx` with 3 summary cards: Total Cost ($), Total Tokens, Total Requests using shadcn Card
- [x] T034 [US5] Create `CostChart` component in `frontend/src/components/costs/cost-chart.tsx` using Recharts LineChart with date range selector (day/week/month tabs), cost and token lines, tooltips, and responsive container. Handle missing data periods with gap indication
- [x] T035 [US5] Create `CostBreakdownTable` component in `frontend/src/components/costs/cost-breakdown-table.tsx` with tabs for "By Agent" and "By Model", showing agent/model name, cost, and token count in a sortable table
- [x] T036 [US5] Create costs page in `frontend/src/app/costs/page.tsx` composing `CostSummary`, `CostChart`, and `CostBreakdownTable` with skeleton loading states

**Checkpoint**: Cost dashboard with charts and breakdowns functional

---

## Phase 8: User Story 6 – Monitor Tool Executions (Priority: P3)

**Goal**: Operators can see tool invocations with status, expandable details, and real-time updates.

**Independent Test**: Navigate to /tools, see invocation list with status badges, expand a row for details, see new invocations appear in real time.

### Implementation for User Story 6

- [x] T037 [P] [US6] Create `useTools` hook in `frontend/src/hooks/use-tools.ts` with TanStack Query for `GET /api/tools/invocations` (paginated) and `GET /api/tools/invocations/:id`, plus WebSocket subscription for `tool:invocation` events that prepend new items to cache
- [x] T038 [US6] Create `ToolInvocationList` component in `frontend/src/components/tools/tool-invocation-list.tsx` displaying tool name, status badge (success=green/failure=red/pending=yellow with spinner), timestamp, and expandable row trigger. Paginated with `Pagination` component
- [x] T039 [US6] Create `ToolInvocationDetail` component in `frontend/src/components/tools/tool-invocation-detail.tsx` showing input parameters (JSON viewer), output/error details, execution duration, and agent name in an expandable accordion row
- [x] T040 [US6] Create tools page in `frontend/src/app/tools/page.tsx` composing `ToolInvocationList` with skeleton/empty states

**Checkpoint**: Tool execution monitor with real-time updates working

---

## Phase 9: User Story 7 – View System Intelligence (Priority: P3)

**Goal**: Operators can see agent activity heatmap, execution timeline, and queue health.

**Independent Test**: Navigate to /intelligence, see heatmap with agent rows, timeline with events, queue health cards.

### Implementation for User Story 7

- [x] T041 [P] [US7] Create `useIntelligence` hook in `frontend/src/hooks/use-intelligence.ts` with TanStack Query for `GET /api/intelligence/heatmap`, `GET /api/intelligence/timeline`, and `GET /api/intelligence/queues`
- [x] T042 [P] [US7] Create `ActivityHeatmap` component in `frontend/src/components/intelligence/activity-heatmap.tsx` using CSS Grid with agent names as rows, time buckets as columns, and color intensity (0.0–1.0) mapped to background opacity. Include period selector and tooltip on hover
- [x] T043 [P] [US7] Create `QueueHealth` component in `frontend/src/components/intelligence/queue-health.tsx` displaying queue cards with name, depth, processing rate (items/min), and status indicator (healthy=green, warning=yellow, critical=red)
- [x] T044 [US7] Create `ExecutionTimeline` component in `frontend/src/components/intelligence/execution-timeline.tsx` showing horizontal timeline bars per agent with task title, start/end time, and status color coding (running=blue, completed=green, failed=red)
- [x] T045 [US7] Create intelligence page in `frontend/src/app/intelligence/page.tsx` composing `ActivityHeatmap`, `ExecutionTimeline`, and `QueueHealth` in a dashboard grid layout with skeleton states

**Checkpoint**: System intelligence dashboard fully rendered

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Animations, accessibility, dark mode verification, error boundaries

- [x] T046 [P] Add Framer Motion page transitions to all 6 new pages using `motion.div` with fade+slide enter/exit in each page.tsx
- [x] T047 [P] Add Framer Motion list animations (staggered children) to `AgentList`, `GoalList`, `MemoryResultList`, `ToolInvocationList`
- [x] T048 [P] Add shimmer animation to `SkeletonLoader` component in `frontend/src/components/shared/skeleton-loader.tsx`
- [x] T049 [P] Create `ErrorBoundary` wrapper component in `frontend/src/components/shared/error-boundary.tsx` and wrap each page section with it
- [x] T050 Verify keyboard navigation (Tab/Enter/Escape) works on all interactive elements: buttons, form inputs, expandable rows, modals, pagination
- [x] T051 Verify WCAG AA contrast ratios across all pages in both light and dark mode, fix any violations
- [x] T052 Run quickstart.md validation: verify all 7 routes render correctly with skeleton→data transitions and empty states

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phases 3–9 (User Stories)**: All depend on Phase 2 completion
  - US1 + US2 (P1): Start first, can be parallel
  - US3 + US4 + US5 (P2): Start after or parallel with P1
  - US6 + US7 (P3): Start after or parallel with P2
- **Phase 10 (Polish)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 (Agents)**: Independent after Phase 2
- **US2 (Agent Logs)**: Depends on US1 (extends agent card and page)
- **US3 (Goals)**: Independent after Phase 2
- **US4 (Memory)**: Independent after Phase 2
- **US5 (Costs)**: Independent after Phase 2
- **US6 (Tools)**: Independent after Phase 2
- **US7 (Intelligence)**: Independent after Phase 2

### Parallel Opportunities

Within Phase 1: T002, T003, T004, T005 all parallel
Within Phase 2: T007, T008, T009, T010 all parallel
US1 || US3 || US4 || US5 (fully independent)
US6 || US7 (fully independent)
Within each story: hooks and simple components marked [P] can be parallel

---

## Parallel Example: User Story 1

```bash
# Launch hooks and simple components in parallel:
Task: "Create useAgents hook in frontend/src/hooks/use-agents.ts"
Task: "Create AgentStatusBadge in frontend/src/components/agents/agent-status-badge.tsx"

# Then sequential (depends on above):
Task: "Create AgentCard in frontend/src/components/agents/agent-card.tsx"
Task: "Create AgentList in frontend/src/components/agents/agent-list.tsx"
Task: "Create agents page in frontend/src/app/agents/page.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Agent list + control)
4. Complete Phase 4: US2 (Agent logs)
5. **STOP and VALIDATE**: /agents page fully functional with start/stop and logs
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Infrastructure ready
2. US1 + US2 → Agent Control Panel (MVP!)
3. US3 → Goal Management
4. US4 → Memory Explorer
5. US5 → Cost Dashboard
6. US6 → Tool Monitor
7. US7 → Intelligence Dashboard
8. Polish → Animations, accessibility, final QA

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to user story for traceability
- No hardcoded API URLs — all from environment variables
- All data fetching via TanStack Query with proper caching
- Real-time via WebSocket client with exponential backoff
- Commit after each task or logical group
