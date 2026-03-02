# Implementation Plan: Silver Tier Frontend Upgrade

**Branch**: `001-silver-tier-frontend` | **Date**: 2026-02-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-silver-tier-frontend/spec.md`

## Summary

Upgrade the Bronze tier frontend (mock-based) to a fully functional API-connected dashboard that integrates with the Silver tier backend. The implementation replaces all mock data with live API calls using TanStack Query for state management, introduces a centralized API client with environment-based configuration, and delivers real-time task management, AI plan generation, agent status monitoring, and activity feed visualization.

## Technical Context

**Language/Version**: TypeScript 5.9+, React 18.3+, Next.js 14.2+
**Primary Dependencies**: TanStack Query (for API state management), Zod (client validation), shadcn/ui, Aceternity UI, Tailwind CSS
**Storage**: N/A (frontend only; backend uses PostgreSQL via Prisma)
**Testing**: Jest (unit), Playwright (E2E)
**Target Platform**: Web browser (desktop, tablet, mobile)
**Project Type**: frontend (Next.js App Router)
**Performance Goals**: Dashboard load <2s, task operations reflect <1s, p95 API response <500ms
**Constraints**: No hardcoded localhost URLs, no mock data in production, environment-based API configuration
**Scale/Scope**: Single-user dashboard, ~50 API calls/minute during active usage

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The constitution file is a template with placeholders and does not contain active principles for this project. The following gates are derived from the spec requirements and industry best practices:

| Gate | Requirement | Pass Criteria |
|------|-------------|---------------|
| G1: Test-First | All new hooks and API client must have unit tests | Jest tests exist for `useTasks`, `usePlans`, `useSystemState`, `useActivityLog`, and API client utilities |
| G2: Environment Safety | No hardcoded localhost URLs | All API URLs resolved from `NEXT_PUBLIC_API_URL` environment variable |
| G3: Separation of Concerns | UI components separate from data hooks | No `fetch` calls in UI components; all data fetching in `hooks/` directory |
| G4: Error Handling | All API operations have error boundaries | Toast notifications on errors; graceful fallback UI for failed states |
| G5: Accessibility | WCAG 2.1 AA compliance | Keyboard navigation works; ARIA labels present; screen reader compatible |
| G6: Responsive Design | Mobile, tablet, desktop support | Layout adapts to 3 breakpoints; no horizontal scroll; touch-friendly targets |
| G7: Dark Mode | Full dark mode compatibility | All components render correctly in dark mode; no hardcoded colors |

**Constitution Check Status**: ✅ PASS (all gates defined and testable)

## Project Structure

### Documentation (this feature)

```text
specs/001-silver-tier-frontend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── tasks.yaml       # OpenAPI spec for tasks endpoints
│   ├── plans.yaml       # OpenAPI spec for plan generation
│   ├── system-state.yaml # OpenAPI spec for agent status
│   └── activity.yaml    # OpenAPI spec for activity logs
└── tasks.md             # Phase 2 output (created by /sp.tasks)
```

### Source Code (frontend directory)

```text
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout with providers
│   │   ├── page.tsx             # Dashboard page
│   │   └── globals.css          # Global styles with dark mode
│   ├── components/
│   │   ├── ui/                  # shadcn/ui base components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── skeleton.tsx
│   │   │   └── toast.tsx
│   │   ├── dashboard/
│   │   │   ├── task-list.tsx    # Task list with status updates
│   │   │   ├── task-card.tsx    # Individual task display
│   │   │   ├── create-task-form.tsx
│   │   │   ├── plan-generator.tsx
│   │   │   ├── agent-status.tsx
│   │   │   └── activity-feed.tsx
│   │   └── shared/
│   │       ├── error-boundary.tsx
│   │       ├── loading-skeleton.tsx
│   │       └── theme-toggle.tsx
│   ├── hooks/
│   │   ├── use-tasks.ts         # Task CRUD operations
│   │   ├── use-plans.ts         # Plan generation
│   │   ├── use-system-state.ts  # Agent status polling
│   │   ├── use-activity-log.ts  # Activity feed
│   │   └── use-api-client.ts    # Base API client
│   ├── lib/
│   │   ├── api-client.ts        # Centralized API client
│   │   ├── api-config.ts        # Environment configuration
│   │   ├── constants.ts         # App-wide constants
│   │   └── utils.ts             # Utility functions (cn, etc.)
│   ├── types/
│   │   ├── task.ts              # Task entity types
│   │   ├── plan.ts              # Plan entity types
│   │   ├── system-state.ts      # Agent status types
│   │   └── activity.ts          # Activity log types
│   └── styles/
│       └── globals.css          # Tailwind + custom styles
├── tests/
│   ├── unit/
│   │   ├── hooks/
│   │   │   ├── use-tasks.test.ts
│   │   │   ├── use-plans.test.ts
│   │   │   ├── use-system-state.test.ts
│   │   │   └── use-activity-log.test.ts
│   │   ├── lib/
│   │   │   └── api-client.test.ts
│   │   └── components/
│   │       └── task-card.test.ts
│   └── e2e/
│       └── dashboard.spec.ts    # Playwright E2E tests
├── .env.local                   # Local environment variables
├── .env.example                 # Environment template
└── package.json
```

**Structure Decision**: Option 2 (Web application) - frontend directory selected. The backend already exists separately; this plan focuses solely on frontend implementation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| TanStack Query | Required for API state management, caching, and background refetching | Direct fetch would require manual caching, loading states, and refetch logic |
| Centralized API client | Single source of truth for API configuration and error handling | Scattered fetch calls would duplicate error handling and config logic |
| Polling for agent status | NFR-001 requires 30-second auto-refresh | WebSocket rejected as out of scope (Gold tier feature) |

## Phase 0: Outline & Research

### Unknowns from Technical Context

| Unknown | Context | Research Task |
|---------|---------|---------------|
| Backend API base URL format | Environment variable configuration | Document expected format and fallback behavior |
| TanStack Query v4 vs v5 | Version compatibility with Next.js 14 | Select version and document setup |
| Error response structure | Backend error format for toast messages | Define error handling pattern |
| Task status values | Valid status options for tasks | Enumerate allowed statuses |
| Plan structure format | AI-generated plan schema | Define expected plan response structure |

### Research Dispatch

**Task 1**: Research backend API endpoint structure and response formats
**Task 2**: Research TanStack Query best practices for Next.js App Router
**Task 3**: Research environment variable patterns for Next.js API configuration
**Task 4**: Research error handling patterns for API-driven dashboards
**Task 5**: Research accessibility patterns for dynamic content updates

---

## research.md

### Decision 1: Backend API Base URL

**Chosen**: `NEXT_PUBLIC_API_URL` environment variable (e.g., `http://localhost:8000/api/v1` or production URL)

**Rationale**: Next.js requires `NEXT_PUBLIC_` prefix for client-side exposure. Allows different URLs per environment (dev, staging, production).

**Alternatives Considered**:
- Hardcoded `localhost:8000` - Rejected: violates FR-014 (no hardcoded localhost)
- Server-side proxy - Rejected: adds unnecessary complexity for Silver tier

---

### Decision 2: TanStack Query Version

**Chosen**: TanStack Query v5 (latest stable)

**Rationale**: Better TypeScript support, improved devtools, smaller bundle size. Compatible with Next.js 14 and React 18.

**Alternatives Considered**:
- v4 - Rejected: v5 has better DX and is stable since late 2023
- SWR - Rejected: team familiarity with TanStack Query; richer feature set for complex state

---

### Decision 3: Error Response Structure

**Chosen**: Standard REST error format:
```json
{
  "error": {
    "code": "TASK_NOT_FOUND",
    "message": "Task with ID 123 not found",
    "details": {}
  }
}
```

**Rationale**: Consistent structure allows centralized error parsing. `code` enables programmatic handling; `message` for user display.

**Alternatives Considered**:
- Plain string errors - Rejected: no programmatic handling
- HTTP status only - Rejected: insufficient context for user-friendly messages

---

### Decision 4: Task Status Values

**Chosen**: `["pending", "in-progress", "completed", "cancelled"]`

**Rationale**: Standard workflow states covering common task lifecycle. Matches backend enum values.

**Alternatives Considered**:
- Simpler: `["open", "done"]` - Rejected: insufficient granularity for AI Employee workflow
- More complex with sub-states - Rejected: YAGNI for Silver tier

---

### Decision 5: Plan Structure Format

**Chosen**: Structured plan with sections:
```json
{
  "id": "plan-uuid",
  "taskId": "task-uuid",
  "createdAt": "ISO-8601",
  "sections": [
    {
      "title": "Section Title",
      "steps": ["Step 1", "Step 2"]
    }
  ],
  "summary": "Overall plan summary"
}
```

**Rationale**: Flexible structure supports various AI output formats while maintaining renderable consistency.

**Alternatives Considered**:
- Free-form markdown - Rejected: harder to style and interact with
- Flat list - Rejected: loses hierarchical organization AI may provide

---

### Decision 6: Polling Strategy for Agent Status

**Chosen**: TanStack Query `refetchInterval: 30000` (30 seconds)

**Rationale**: Meets NFR-001 requirement. TanStack Query handles background refetch, stale-while-revalidate caching, and automatic cleanup on unmount.

**Alternatives Considered**:
- `setInterval` manual polling - Rejected: requires manual cleanup, no caching
- WebSocket - Rejected: out of scope (Gold tier)
- Longer interval (60s) - Rejected: 30s provides better UX per spec

---

## Phase 1: Design & Contracts

### Data Model (from spec entities)

See `data-model.md` for full details. Summary:

| Entity | Key Fields | Relationships |
|--------|-----------|---------------|
| Task | id, title, description, status, createdAt, updatedAt | None (standalone) |
| Plan | id, taskId, sections[], summary, createdAt | References Task by taskId |
| SystemState | status, lastActivityAt, currentTaskId | References Task optionally |
| ActivityLog | id, timestamp, eventType, message, metadata | References Task optionally |

---

### API Contracts

#### Tasks API

```yaml
openapi: 3.0.0
info:
  title: Tasks API
  version: 1.0.0
paths:
  /tasks:
    get:
      summary: List all tasks
      operationId: listTasks
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Task'
    post:
      summary: Create a new task
      operationId: createTask
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateTaskInput'
      responses:
        '201':
          description: Task created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'
  /tasks/{id}:
    patch:
      summary: Update task status
      operationId: updateTask
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateTaskInput'
      responses:
        '200':
          description: Task updated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Task'

components:
  schemas:
    Task:
      type: object
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
        description:
          type: string
        status:
          type: string
          enum: [pending, in-progress, completed, cancelled]
        createdAt:
          type: string
          format: date-time
        updatedAt:
          type: string
          format: date-time
    CreateTaskInput:
      type: object
      required: [title]
      properties:
        title:
          type: string
        description:
          type: string
    UpdateTaskInput:
      type: object
      properties:
        status:
          type: string
          enum: [pending, in-progress, completed, cancelled]
```

#### Plans API

```yaml
openapi: 3.0.0
info:
  title: Plans API
  version: 1.0.0
paths:
  /plans:
    post:
      summary: Generate AI plan for tasks
      operationId: generatePlan
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                taskIds:
                  type: array
                  items:
                    type: string
      responses:
        '200':
          description: Plan generated
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Plan'
        '202':
          description: Plan generation in progress
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    enum: [processing]
                  estimatedCompletion:
                    type: string
                    format: date-time

components:
  schemas:
    Plan:
      type: object
      properties:
        id:
          type: string
          format: uuid
        taskId:
          type: string
          format: uuid
        sections:
          type: array
          items:
            type: object
            properties:
              title:
                type: string
              steps:
                type: array
                items:
                  type: string
        summary:
          type: string
        createdAt:
          type: string
          format: date-time
```

#### System State API

```yaml
openapi: 3.0.0
info:
  title: System State API
  version: 1.0.0
paths:
  /system/state:
    get:
      summary: Get current agent status
      operationId: getSystemState
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SystemState'

components:
  schemas:
    SystemState:
      type: object
      properties:
        status:
          type: string
          enum: [idle, processing, working, error]
        lastActivityAt:
          type: string
          format: date-time
        currentTaskId:
          type: string
          format: uuid
          nullable: true
```

#### Activity Log API

```yaml
openapi: 3.0.0
info:
  title: Activity Log API
  version: 1.0.0
paths:
  /activity:
    get:
      summary: Get activity logs
      operationId: getActivityLogs
      parameters:
        - name: limit
          in: query
          required: false
          schema:
            type: integer
            default: 50
        - name: offset
          in: query
          required: false
          schema:
            type: integer
            default: 0
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ActivityLog'

components:
  schemas:
    ActivityLog:
      type: object
      properties:
        id:
          type: string
          format: uuid
        timestamp:
          type: string
          format: date-time
        eventType:
          type: string
          enum: [task_created, task_updated, plan_generated
          generated, system_started, system_error]
        message:
          type: string
        metadata:
          type: object
          additionalProperties: true
```

---

### quickstart.md

```markdown
# Quickstart: Silver Tier Frontend

## Prerequisites

- Node.js 18+ installed
- Backend running at accessible URL
- `.env.local` configured with `NEXT_PUBLIC_API_URL`

## Setup

1. **Install dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local and set NEXT_PUBLIC_API_URL
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

3. **Install TanStack Query**:
   ```bash
   npm install @tanstack/react-query
   ```

4. **Run development server**:
   ```bash
   npm run dev
   ```

5. **Open browser**: Navigate to `http://localhost:3000`

## Verify Connection

- Dashboard should load with tasks from backend (no mock data)
- Agent status should show current state
- Activity feed should display recent logs
- Creating a task should persist to backend

## Troubleshooting

- **API errors**: Check `NEXT_PUBLIC_API_URL` matches backend
- **CORS errors**: Ensure backend allows origin `http://localhost:3000`
- **Empty data**: Verify backend has data; check network tab for failed requests
```

---

## Phase 2: Implementation Phases

### Phase 2.1: API Client Layer

**Goal**: Establish centralized API configuration and client

**Tasks**:
1. Create `lib/api-config.ts` with environment-based URL resolution
2. Create `lib/api-client.ts` with typed fetch wrapper
3. Add error handling middleware for consistent error parsing
4. Configure TypeScript types for API responses

**Artifacts**:
- `src/lib/api-config.ts`
- `src/lib/api-client.ts`
- `src/types/api.ts`

**Done Criteria**:
- [ ] `NEXT_PUBLIC_API_URL` properly read with fallback to `/api/v1`
- [ ] API client handles GET, POST, PATCH with proper headers
- [ ] Errors parsed into consistent format with code and message
- [ ] Unit tests for API client (success and error paths)

---

### Phase 2.2: Data Hooks Layer

**Goal**: Create reusable hooks for all API operations

**Tasks**:
1. Create `hooks/use-api-client.ts` base hook with TanStack Query provider
2. Create `hooks/use-tasks.ts` for task CRUD operations
3. Create `hooks/use-plans.ts` for plan generation
4. Create `hooks/use-system-state.ts` with 30s polling interval
5. Create `hooks/use-activity-log.ts` for activity feed

**Artifacts**:
- `src/hooks/use-tasks.ts`
- `src/hooks/use-plans.ts`
- `src/hooks/use-system-state.ts`
- `src/hooks/use-activity-log.ts`
- `src/hooks/use-api-client.ts`

**Done Criteria**:
- [ ] `useTasks` returns `{ tasks, isLoading, error, createTask, updateTask, refetch }`
- [ ] `usePlans` returns `{ generatePlan, isGenerating, error }`
- [ ] `useSystemState` polls every 30s per NFR-001
- [ ] `useActivityLog` returns paginated logs with loading state
- [ ] All hooks have unit tests with mocked API responses

---

### Phase 2.3: Dashboard Integration

**Goal**: Replace mock data with live API integration

**Tasks**:
1. Update `app/page.tsx` to use hooks instead of mock data
2. Wrap app with TanStack Query provider in `layout.tsx`
3. Connect task list to `useTasks` hook
4. Add loading skeletons for initial data fetch
5. Add error boundary for API failures

**Artifacts**:
- `src/app/layout.tsx` (updated with QueryClientProvider)
- `src/app/page.tsx` (updated with live data)
- `src/components/shared/error-boundary.tsx`

**Done Criteria**:
- [ ] Dashboard loads and displays tasks from backend
- [ ] Loading skeleton shows during initial fetch
- [ ] Error boundary catches and displays API errors
- [ ] No mock data imports remain in dashboard components

---

### Phase 2.4: Needs Action Integration

**Goal**: Enable task creation and status updates via API

**Tasks**:
1. Create `components/dashboard/create-task-form.tsx`
2. Wire form submission to `useTasks.createTask`
3. Add status dropdown to `components/dashboard/task-card.tsx`
4. Wire status changes to `useTasks.updateTask`
5. Add optimistic updates for instant UI feedback
6. Handle rollback on API failure

**Artifacts**:
- `src/components/dashboard/create-task-form.tsx`
- `src/components/dashboard/task-card.tsx` (updated)

**Done Criteria**:
- [ ] Users can create tasks via form; appears in list immediately
- [ ] Status dropdown updates task; change reflects instantly
- [ ] Failed operations show toast and revert UI
- [ ] Unit tests for form validation and submission

---

### Phase 2.5: Plan Generation Flow

**Goal**: Implement AI plan generation with loading state

**Tasks**:
1. Create `components/dashboard/plan-generator.tsx`
2. Add "Generate Plan" button wired to `usePlans.generatePlan`
3. Display "Thinking..." loading state during generation
4. Render structured plan sections on success
5. Show retry option on failure

**Artifacts**:
- `src/components/dashboard/plan-generator.tsx`
- `src/components/dashboard/plan-display.tsx`

**Done Criteria**:
- [ ] Clicking "Generate Plan" triggers API call
- [ ] "Thinking..." indicator displays during processing
- [ ] Structured plan renders with sections and steps
- [ ] Error shows friendly message with retry button
- [ ] E2E test for complete plan generation flow

---

### Phase 2.6: Activity Feed Integration

**Goal**: Display chronological activity timeline

**Tasks**:
1. Create `components/dashboard/activity-feed.tsx`
2. Connect to `useActivityLog` hook
3. Render timeline view with timestamps
4. Add loading skeleton for feed
5. Implement infinite scroll or pagination if needed

**Artifacts**:
- `src/components/dashboard/activity-feed.tsx`

**Done Criteria**:
- [ ] Activity feed displays logs in chronological order
- [ ] Timestamps formatted in user-friendly format
- [ ] Loading skeleton shows during fetch
- [ ] New activities appear after refetch

---

### Phase 2.7: UX Hardening

**Goal**: Polish user experience with proper states and feedback

**Tasks**:
1. Add skeleton loaders to all data-fetching components
2. Implement toast notifications for success/error states
3. Add disabled states during loading operations
4. Ensure all interactive elements have focus states
5. Test keyboard navigation across dashboard
6. Verify dark mode compatibility

**Artifacts**:
- `src/components/ui/toast.tsx` (updated)
- `src/components/shared/loading-skeleton.tsx` (updated)
- Global toast context/provider

**Done Criteria**:
- [ ] All loading states show skeletons (not spinners)
- [ ] Toast notifications appear for all API operations
- [ ] Buttons disabled during async operations
- [ ] Keyboard tab order logical; all elements focusable
- [ ] Dark mode renders correctly; no contrast issues

---

### Phase 2.8: Structural Cleanup

**Goal**: Finalize code quality and remove technical debt

**Tasks**:
1. Remove all mock data files from `src/data/`
2. Extract reusable components to `components/shared/`
3. Validate folder structure matches plan
4. Run TypeScript strict mode; fix all errors
5. Run ESLint; fix all warnings
6. Update `.env.example` with all required variables
7. Document hook usage patterns

**Artifacts**:
- Updated folder structure
- Removed: `src/data/mock-tasks.ts`, `src/data/mock-activity.ts`
- `src/components/shared/` with extracted components

**Done Criteria**:
- [ ] Zero mock data files remain
- [ ] All components follow consistent naming
- [ ] TypeScript compiles with zero errors
- [ ] ESLint passes with zero warnings
- [ ] `.env.example` documents all environment variables
- [ ] README updated with setup instructions

---

## Phase 3: Validation & Handoff

**Goal**: Verify all gates pass and prepare for `/sp.tasks`

**Validation Checklist**:

| Gate | Validation Method | Status |
|------|------------------|--------|
| G1: Test-First | Run `npm test`; verify >80% coverage | ⏳ Pending |
| G2: Environment Safety | Grep for `localhost`; verify `.env.local` usage | ⏳ Pending |
| G3: Separation of Concerns | Audit components for fetch calls | ⏳ Pending |
| G4: Error Handling | Manual testing; trigger API errors | ⏳ Pending |
| G5: Accessibility | Run axe-core; keyboard navigation test | ⏳ Pending |
| G6: Responsive Design | Test at 3 breakpoints (mobile, tablet, desktop) | ⏳ Pending |
| G7: Dark Mode | Toggle theme; verify all components | ⏳ Pending |

**Handoff Artifacts**:
- [ ] `plan.md` complete with all phases
- [ ] `research.md` with all decisions documented
- [ ] `data-model.md` with entity definitions
- [ ] `contracts/` with OpenAPI specs
- [ ] `quickstart.md` with setup instructions
- [ ] All Phase 2 tasks completed and validated

**Next Command**: `/sp.tasks` to break implementation into actionable tasks with acceptance criteria

---

## Constitution Check (Post-Design)

*Re-evaluation after Phase 1 design completion*

All gates remain valid after design. No violations detected. Design aligns with:
- Separation of concerns (G3) via hooks layer
- Environment safety (G2) via centralized config
- Error handling (G4) via API client middleware
- Accessibility (G5) via component library patterns

**Status**: ✅ PASS - Ready for Phase 2 implementation
