# Implementation Plan: Platinum Tier Frontend

**Branch**: `001-platinum-tier-frontend` | **Date**: 2026-03-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-platinum-tier-frontend/spec.md`

## Summary

Upgrade the Gold-tier Next.js dashboard into a full AI Workforce Control Center with 6 new pages: Agent Control Panel, Goal Management, Memory Explorer, Cost Dashboard, Tool Execution Monitor, and System Intelligence Dashboard. Built on existing Next.js App Router + shadcn/ui + TanStack Query stack, adding WebSocket real-time updates, Recharts for visualizations, and Framer Motion animations.

## Technical Context

**Language/Version**: TypeScript 5.x, React 18, Next.js 14 (App Router)
**Primary Dependencies**: shadcn/ui, TanStack Query v5, Framer Motion, Recharts, Lucide React, next-themes, axios
**Storage**: N/A (frontend only — consumes backend REST + WebSocket APIs)
**Testing**: Jest + React Testing Library, Playwright for E2E
**Target Platform**: Web (modern browsers)
**Project Type**: Web application (frontend only for this feature)
**Performance Goals**: All pages load < 3s, real-time updates < 2s latency
**Constraints**: WCAG AA compliance, dark mode support, no auth
**Scale/Scope**: 6 new pages, ~30 new components, ~10 custom hooks

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Test-First | PASS | Jest + RTL for components, Playwright for E2E flows |
| II. CLI Interface | N/A | Frontend feature — backend already exposes endpoints |
| III. Observability | PASS | Connection status indicator, error boundaries, console logging |
| IV. Integration Testing | PASS | Playwright E2E covers user stories |
| V. Simplicity (YAGNI) | PASS | No extra abstractions — direct TanStack Query hooks per page |
| VI. Async-First | N/A | Frontend — all data fetching is inherently async via TanStack Query |
| VII. Idempotency | N/A | Frontend — handled by backend |

## Project Structure

### Documentation (this feature)

```text
specs/001-platinum-tier-frontend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── api-contracts.md
└── tasks.md
```

### Source Code (repository root)

```text
frontend/
├── src/
│   ├── app/
│   │   ├── agents/
│   │   │   └── page.tsx              # Agent Control Panel
│   │   ├── goals/
│   │   │   └── page.tsx              # Goal Management
│   │   ├── memory/
│   │   │   └── page.tsx              # Memory Explorer
│   │   ├── costs/
│   │   │   └── page.tsx              # Cost Dashboard
│   │   ├── tools/
│   │   │   └── page.tsx              # Tool Execution Monitor
│   │   └── intelligence/
│   │       └── page.tsx              # System Intelligence Dashboard
│   ├── components/
│   │   ├── agents/
│   │   │   ├── agent-list.tsx
│   │   │   ├── agent-card.tsx
│   │   │   ├── agent-log-viewer.tsx
│   │   │   └── agent-status-badge.tsx
│   │   ├── goals/
│   │   │   ├── goal-list.tsx
│   │   │   ├── goal-card.tsx
│   │   │   ├── goal-form.tsx
│   │   │   └── task-breakdown.tsx
│   │   ├── memory/
│   │   │   ├── memory-search.tsx
│   │   │   ├── memory-result-list.tsx
│   │   │   └── memory-detail.tsx
│   │   ├── costs/
│   │   │   ├── cost-summary.tsx
│   │   │   ├── cost-chart.tsx
│   │   │   └── cost-breakdown-table.tsx
│   │   ├── tools/
│   │   │   ├── tool-invocation-list.tsx
│   │   │   └── tool-invocation-detail.tsx
│   │   ├── intelligence/
│   │   │   ├── activity-heatmap.tsx
│   │   │   ├── execution-timeline.tsx
│   │   │   └── queue-health.tsx
│   │   └── shared/
│   │       ├── connection-status.tsx
│   │       ├── skeleton-loader.tsx
│   │       ├── empty-state.tsx
│   │       └── pagination.tsx
│   ├── hooks/
│   │   ├── use-agents.ts
│   │   ├── use-goals.ts
│   │   ├── use-memory.ts
│   │   ├── use-costs.ts
│   │   ├── use-tools.ts
│   │   ├── use-intelligence.ts
│   │   └── use-websocket.ts
│   └── lib/
│       ├── api-client.ts
│       └── websocket-client.ts
└── tests/
    ├── unit/
    └── e2e/
```

**Structure Decision**: Frontend-only addition to existing Next.js App Router project. Each feature gets its own route directory, component directory, and TanStack Query hook. Shared components (connection status, skeleton loader, empty state, pagination) are reusable across all pages.

## Implementation Phases

### Phase 1 — Layout Architecture & Shared Infrastructure

**Goal**: Navigation, shared components, WebSocket client, API client setup.

**Deliverables**:
- Updated sidebar with new navigation items (Agents, Goals, Memory, Costs, Tools, Intelligence)
- `websocket-client.ts` — WebSocket connection manager with exponential backoff (1s→2s→4s→8s…max 30s)
- `connection-status.tsx` — Banner showing connection state
- `skeleton-loader.tsx` — Reusable skeleton loader component
- `empty-state.tsx` — Contextual empty state with action prompts
- `pagination.tsx` — Reusable pagination with configurable page sizes
- `api-client.ts` — Axios wrapper for backend API base URL from env

**Done criteria**:
- [ ] Sidebar renders all 6 new nav items
- [ ] WebSocket connects and reconnects with exponential backoff
- [ ] Connection status banner shows/hides based on WebSocket state
- [ ] Skeleton loader, empty state, pagination components render correctly
- [ ] API client reads base URL from environment variable

---

### Phase 2 — Agent Control Panel

**Goal**: List agents, show status, start/stop, view logs.

**Deliverables**:
- `use-agents.ts` — TanStack Query hook for agents CRUD + WebSocket subscription
- `agent-list.tsx` — List of agents with status badges
- `agent-card.tsx` — Individual agent card with start/stop buttons
- `agent-status-badge.tsx` — Color-coded status indicator (running=green, stopped=gray, error=red)
- `agent-log-viewer.tsx` — Real-time log stream with severity filter (info/warn/error)
- `app/agents/page.tsx` — Page composition

**Done criteria**:
- [ ] Agent list loads with skeleton → data transition
- [ ] Status badges show correct colors per state
- [ ] Start/stop buttons trigger API calls and UI updates within 2s
- [ ] Log viewer streams entries in real time via WebSocket
- [ ] Severity filter works correctly
- [ ] Empty state shows when no agents registered

---

### Phase 3 — Goal Management

**Goal**: Create goals, track progress, visualize task breakdown.

**Deliverables**:
- `use-goals.ts` — TanStack Query hook for goals CRUD
- `goal-list.tsx` — Goals with status and progress bars
- `goal-card.tsx` — Goal detail with state transitions (Draft→Active→Completed, Cancel)
- `goal-form.tsx` — Create/edit goal form (title, description, priority)
- `task-breakdown.tsx` — Visual task tree with status indicators
- `app/goals/page.tsx` — Page composition

**Done criteria**:
- [ ] Goal creation form validates and submits
- [ ] Goal list shows progress percentage
- [ ] State transitions enforced: Draft→Active→Completed, Cancel from Draft/Active
- [ ] Task breakdown visualizes sub-tasks with statuses
- [ ] Empty state when no goals exist

---

### Phase 4 — Memory Explorer

**Goal**: Search AI memory, view entries, inspect similarity scores.

**Deliverables**:
- `use-memory.ts` — TanStack Query hook for memory search
- `memory-search.tsx` — Search input with debounced query
- `memory-result-list.tsx` — Results ranked by similarity with scores
- `memory-detail.tsx` — Full context view with metadata (source, timestamp, agent)
- `app/memory/page.tsx` — Page composition

**Done criteria**:
- [ ] Search returns results within 3s
- [ ] Results show similarity scores and are ranked
- [ ] Detail view shows full context and metadata
- [ ] Pagination at 20 items/page
- [ ] Empty state with suggestions when no results match

---

### Phase 5 — Cost Dashboard

**Goal**: Display AI usage, token consumption, cost trends.

**Deliverables**:
- `use-costs.ts` — TanStack Query hook for cost data with date range
- `cost-summary.tsx` — Total cost, tokens, request count cards
- `cost-chart.tsx` — Time-series Recharts line chart with day/week/month selector
- `cost-breakdown-table.tsx` — Per-agent and per-model cost table
- `app/costs/page.tsx` — Page composition

**Done criteria**:
- [ ] Summary cards show total cost, tokens, requests
- [ ] Chart renders with date range selection (day/week/month)
- [ ] Breakdown table shows per-agent and per-model costs
- [ ] Loads within 3s
- [ ] Handles missing data periods gracefully

---

### Phase 6 — Tool Execution Monitor

**Goal**: List tool invocations with status, expandable details, real-time updates.

**Deliverables**:
- `use-tools.ts` — TanStack Query hook + WebSocket subscription
- `tool-invocation-list.tsx` — List with status badges (success/failure/pending)
- `tool-invocation-detail.tsx` — Expandable detail with input, output, duration
- `app/tools/page.tsx` — Page composition

**Done criteria**:
- [ ] Invocation list loads with status badges
- [ ] Expandable rows show input params, output, duration
- [ ] New invocations appear in real time via WebSocket
- [ ] Pending invocations show spinner
- [ ] Pagination works for large result sets

---

### Phase 7 — System Intelligence Dashboard

**Goal**: Activity heatmap, execution timeline, queue health.

**Deliverables**:
- `use-intelligence.ts` — TanStack Query hook for system intelligence data
- `activity-heatmap.tsx` — Grid heatmap (agents x time) with color intensity
- `execution-timeline.tsx` — Horizontal timeline of task executions across agents
- `queue-health.tsx` — Queue cards with depth, rate, and status indicators
- `app/intelligence/page.tsx` — Page composition

**Done criteria**:
- [ ] Heatmap renders with agent rows and time columns
- [ ] Timeline shows chronological task executions
- [ ] Queue health shows depth, rate, and warning/critical states
- [ ] All render within 3s
- [ ] Dark mode compatible

---

### Phase 8 — UI Performance & Polish

**Goal**: Animations, transitions, accessibility, dark mode verification.

**Deliverables**:
- Framer Motion page transitions and list animations
- Loading state animations (skeleton shimmer)
- Focus management and keyboard navigation for all interactive elements
- WCAG AA contrast verification across all pages in light and dark mode
- Error boundaries for each page section

**Done criteria**:
- [ ] All pages have smooth enter/exit transitions
- [ ] Tab navigation works on all interactive elements
- [ ] Contrast ratios pass WCAG AA in both themes
- [ ] Error boundaries catch and display component errors gracefully
- [ ] No layout shift during loading transitions

## Complexity Tracking

No constitution violations. No complexity justifications needed.
