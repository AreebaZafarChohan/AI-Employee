# Research: Platinum Tier Frontend

## R1: Chart Library for Cost Dashboard & Heatmap

- **Decision**: Recharts
- **Rationale**: Already common in React/Next.js ecosystem, composable API, supports line/bar/area charts and custom heatmaps. SSR-compatible with dynamic imports.
- **Alternatives considered**: Chart.js (less React-native), D3 (too low-level for standard charts), Nivo (heavier bundle)

## R2: WebSocket Client Strategy

- **Decision**: Native WebSocket API with custom reconnection wrapper
- **Rationale**: No need for Socket.IO overhead since backend uses plain WebSocket. Custom wrapper handles exponential backoff (1s→30s max), connection state tracking, and event dispatch via React context.
- **Alternatives considered**: Socket.IO client (unnecessary overhead), SWR subscriptions (not real WebSocket)

## R3: Heatmap Visualization Approach

- **Decision**: Custom CSS Grid heatmap with Recharts for color scale
- **Rationale**: Agent activity heatmap is a simple grid (agents x time buckets) with color intensity. Custom CSS Grid is simpler and more performant than a full chart library for this use case.
- **Alternatives considered**: Recharts custom cell renderer (complex), D3 heatmap (overkill)

## R4: Real-time Log Streaming

- **Decision**: WebSocket subscription per agent with virtualized scroll
- **Rationale**: Logs can grow unbounded. Virtualized scroll (react-window or native CSS containment) keeps DOM lean. WebSocket sends new log entries as they arrive.
- **Alternatives considered**: SSE (less suitable for bidirectional needs like filtering), polling (wasteful)

## R5: Existing Backend API Coverage

- **Decision**: Backend already has models/services for goals, costs, memory, tools. Routes for agents need to be added in Platinum Tier Backend.
- **Rationale**: Checked `backend/src/models/` — goal_model.ts, cost_model.ts, memory_model.ts, tool_model.ts exist. Services exist for all. Agent-specific routes (start/stop/logs) pending.
- **Alternatives considered**: N/A — build on existing backend contracts.

## R6: State Management

- **Decision**: TanStack Query for server state, React useState/useReducer for local UI state
- **Rationale**: TanStack Query v5 already in the project. Handles caching, background refetch, optimistic updates. No need for Redux or Zustand.
- **Alternatives considered**: Zustand (unnecessary layer), Redux (too heavy for this scope)
