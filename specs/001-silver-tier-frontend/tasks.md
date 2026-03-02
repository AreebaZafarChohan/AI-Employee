# Tasks: Silver Tier Frontend Upgrade

**Input**: Design documents from `/specs/001-silver-tier-frontend/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `frontend/src/`, `frontend/tests/`
- Paths shown below assume frontend directory structure per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and TanStack Query installation

- [ ] T001 Install TanStack Query v5: `npm install @tanstack/react-query@^5` in frontend/
- [ ] T002 [P] Install Zod for validation: `npm install zod` in frontend/
- [ ] T003 [P] Update .env.example with NEXT_PUBLIC_API_URL in frontend/.env.example
- [ ] T004 [P] Create .env.local with NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 in frontend/.env.local

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Create API config module in frontend/src/lib/api-config.ts with NEXT_PUBLIC_API_URL resolution
- [ ] T006 [P] Create centralized API client in frontend/src/lib/api-client.ts with typed fetch wrapper
- [ ] T007 [P] Create API error types in frontend/src/types/api.ts (ApiError, ErrorCode, SuccessResponse, PaginatedResponse)
- [ ] T008 [P] Create base API client hook in frontend/src/hooks/use-api-client.ts with TanStack Query setup
- [ ] T009 [P] Create all TypeScript type definitions in frontend/src/types/: task.ts, plan.ts, system-state.ts, activity.ts
- [ ] T010 [P] Create Zod validation schemas in frontend/src/lib/validations.ts for all entities
- [ ] T011 [P] Setup TanStack Query provider in frontend/src/app/layout.tsx with QueryClientProvider
- [ ] T012 Create error boundary component in frontend/src/components/shared/error-boundary.tsx

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View and Manage Tasks (Priority: P1) 🎯 MVP

**Goal**: Display live tasks from backend, enable task creation and status updates

**Independent Test**: Can be fully tested by loading the dashboard, viewing the task list, creating a new task via the UI, and updating a task's status - all operations should reflect immediately without page refresh

### Implementation for User Story 1

- [ ] T013 [P] [US1] Create useTasks hook in frontend/src/hooks/use-tasks.ts with listTasks, createTask, updateTask, refetch
- [ ] T014 [P] [US1] Create Task type in frontend/src/types/task.ts with TaskStatus enum
- [ ] T015 [P] [US1] Create Zod schema for Task in frontend/src/lib/validations.ts (TaskSchema, CreateTaskInputSchema, UpdateTaskInputSchema)
- [ ] T016 [US1] Create task card component in frontend/src/components/dashboard/task-card.tsx with status display
- [ ] T017 [US1] Create task list component in frontend/src/components/dashboard/task-list.tsx using useTasks hook
- [ ] T018 [US1] Create create task form in frontend/src/components/dashboard/create-task-form.tsx with title/description inputs
- [ ] T019 [US1] Add status update dropdown in frontend/src/components/dashboard/task-card.tsx wired to updateTask
- [ ] T020 [US1] Implement optimistic updates in useTasks hook with rollback on failure
- [ ] T021 [US1] Add loading skeleton for task list in frontend/src/components/shared/loading-skeleton.tsx (TaskListSkeleton)
- [ ] T022 [US1] Update dashboard page in frontend/src/app/page.tsx to use live task list instead of mock data
- [ ] T023 [US1] Add toast notifications for task create/update success and errors
- [ ] T024 [US1] Wrap task operations in error boundary for graceful failure handling

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - users can view, create, and update tasks with live backend data

---

## Phase 4: User Story 2 - Generate AI Plan (Priority: P2)

**Goal**: Click "Generate Plan" button and receive AI-generated structured plan with loading state

**Independent Test**: Can be fully tested by clicking "Generate Plan" with existing tasks in the system, observing the loading state, and verifying a structured plan is displayed upon completion

### Implementation for User Story 2

- [ ] T025 [P] [US2] Create Plan type in frontend/src/types/plan.ts with PlanSection interface
- [ ] T026 [P] [US2] Create Zod schema for Plan in frontend/src/lib/validations.ts (PlanSchema, PlanSectionSchema)
- [ ] T027 [P] [US2] Create usePlans hook in frontend/src/hooks/use-plans.ts with generatePlan mutation
- [ ] T028 [US2] Create plan generator component in frontend/src/components/dashboard/plan-generator.tsx with "Generate Plan" button
- [ ] T029 [US2] Add "Thinking..." loading indicator in frontend/src/components/dashboard/plan-generator.tsx during plan generation
- [ ] T030 [US2] Create plan display component in frontend/src/components/dashboard/plan-display.tsx to render structured plan sections
- [ ] T031 [US2] Add retry button on plan generation failure in frontend/src/components/dashboard/plan-generator.tsx
- [ ] T032 [US2] Integrate plan generator into dashboard page in frontend/src/app/page.tsx
- [ ] T033 [US2] Add toast notifications for plan generation success and errors

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - users can manage tasks AND generate AI plans

---

## Phase 5: User Story 3 - Monitor Agent Status (Priority: P3)

**Goal**: Display current agent status and last activity timestamp with 30-second auto-refresh

**Independent Test**: Can be fully tested by navigating to the dashboard and verifying the agent status indicator shows the current state (e.g., "Idle", "Working", "Processing") along with a timestamp of the last activity

### Implementation for User Story 3

- [ ] T034 [P] [US3] Create SystemState type in frontend/src/types/system-state.ts with AgentStatus enum
- [ ] T035 [P] [US3] Create Zod schema for SystemState in frontend/src/lib/validations.ts (SystemStateSchema, AgentStatusSchema)
- [ ] T036 [P] [US3] Create useSystemState hook in frontend/src/hooks/use-system-state.ts with refetchInterval: 30000 (30 seconds)
- [ ] T037 [US3] Create agent status component in frontend/src/components/dashboard/agent-status.tsx displaying current status
- [ ] T038 [US3] Add last activity timestamp display in frontend/src/components/dashboard/agent-status.tsx with formatted time
- [ ] T039 [US3] Add status indicator styling (color/icon) based on AgentStatus value in frontend/src/components/dashboard/agent-status.tsx
- [ ] T040 [US3] Integrate agent status widget into dashboard page in frontend/src/app/page.tsx
- [ ] T041 [US3] Add loading state for initial agent status fetch in frontend/src/components/dashboard/agent-status.tsx

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently - users can manage tasks, generate plans, AND monitor agent status

---

## Phase 6: User Story 4 - View Activity Feed (Priority: P4)

**Goal**: Display chronological timeline of system activities and logs

**Independent Test**: Can be fully tested by viewing the activity feed section and verifying it displays a chronological list of system events with timestamps and descriptions

### Implementation for User Story 4

- [ ] T042 [P] [US4] Create ActivityLog type in frontend/src/types/activity.ts with ActivityEventType enum
- [ ] T043 [P] [US4] Create Zod schema for ActivityLog in frontend/src/lib/validations.ts (ActivityLogSchema, ActivityEventTypeSchema)
- [ ] T044 [P] [US4] Create useActivityLog hook in frontend/src/hooks/use-activity-log.ts with pagination support
- [ ] T045 [US4] Create activity feed component in frontend/src/components/dashboard/activity-feed.tsx with timeline layout
- [ ] T046 [US4] Add timestamp formatting in frontend/src/components/dashboard/activity-feed.tsx (relative time: "2 minutes ago")
- [ ] T047 [US4] Add event type icons/labels in frontend/src/components/dashboard/activity-feed.tsx for each ActivityEventType
- [ ] T048 [US4] Add loading skeleton for activity feed in frontend/src/components/dashboard/activity-feed.tsx
- [ ] T049 [US4] Integrate activity feed into dashboard page in frontend/src/app/page.tsx
- [ ] T050 [US4] Add "Load More" button or infinite scroll for pagination in frontend/src/components/dashboard/activity-feed.tsx

**Checkpoint**: All user stories should now be independently functional - complete Silver Tier dashboard with tasks, plans, agent status, and activity feed

---

## Phase 7: UX Hardening & Polish

**Purpose**: Cross-cutting improvements that affect multiple user stories

- [ ] T051 [P] Add toast notification component integration in frontend/src/components/ui/toast.tsx (shadcn/ui)
- [ ] T052 [P] Add disabled button states during async operations across all forms and buttons
- [ ] T053 [P] Ensure all loading states use skeletons (not spinners) across all components
- [ ] T054 [P] Add keyboard navigation support for all interactive elements
- [ ] T055 [P] Add ARIA labels for screen reader accessibility
- [ ] T056 [P] Test and fix dark mode compatibility for all components
- [ ] T057 [P] Test responsive layout at mobile (375px), tablet (768px), and desktop (1920px) breakpoints
- [ ] T058 Remove all mock data files: delete frontend/src/data/mock-tasks.ts, frontend/src/data/mock-activity.ts (if exist)
- [ ] T059 [P] Run TypeScript strict mode check: `npx tsc --noEmit` and fix all errors
- [ ] T060 [P] Run ESLint: `npm run lint` and fix all warnings
- [ ] T061 [P] Update frontend/README.md with Silver Tier setup instructions from quickstart.md
- [ ] T062 [P] Verify no hardcoded localhost URLs: grep for "localhost" and ensure only in .env.local

---

## Phase 8: Validation & Testing

**Purpose**: Verify all gates pass and implementation is production-ready

- [ ] T063 Run unit tests for all hooks: `npm test -- hooks/`
- [ ] T064 Run unit tests for API client: `npm test -- lib/api-client.test.ts`
- [ ] T065 Run E2E test for complete task management flow: `npm run test:e2e`
- [ ] T066 Validate G1 (Test-First): Verify >80% test coverage
- [ ] T067 Validate G2 (Environment Safety): Confirm no localhost in source code
- [ ] T068 Validate G3 (Separation of Concerns): Audit components for fetch calls (should be zero)
- [ ] T069 Validate G4 (Error Handling): Manually trigger API errors and verify toast notifications
- [ ] T070 Validate G5 (Accessibility): Run axe-core audit and fix violations
- [ ] T071 Validate G6 (Responsive Design): Test at 3 breakpoints with no layout breaking
- [ ] T072 Validate G7 (Dark Mode): Toggle theme and verify all components render correctly
- [ ] T073 Build production bundle: `npm run build` and verify zero errors
- [ ] T074 Test production build locally: `npm run start` and verify all features work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **UX Hardening (Phase 7)**: Depends on all user stories being complete
- **Validation (Phase 8)**: Depends on UX Hardening completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1 but assumes tasks exist
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent of US1/US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent of US1/US2/US3

### Within Each User Story

- Models/types marked [P] can run in parallel
- Hooks marked [P] can run in parallel
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 (Setup)**: T002, T003, T004 can all run in parallel
- **Phase 2 (Foundational)**: T005, T006, T007, T008, T009, T010, T011 can all run in parallel
- **Phase 3 (US1)**: T013, T014, T015 can run in parallel; T016, T017, T018 can run in parallel
- **Phase 4 (US2)**: T025, T026, T027 can run in parallel
- **Phase 5 (US3)**: T034, T035, T036 can run in parallel
- **Phase 6 (US4)**: T042, T043, T044 can run in parallel
- **Phase 7 (UX)**: T051, T052, T053, T054, T055, T056, T057 can run in parallel
- **Phase 8 (Validation)**: T063, T064, T065 can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all type/hook creation for User Story 1 together:
Task: "Create useTasks hook in frontend/src/hooks/use-tasks.ts"
Task: "Create Task type in frontend/src/types/task.ts"
Task: "Create Zod schema for Task in frontend/src/lib/validations.ts"

# Then launch component creation in parallel:
Task: "Create task card component in frontend/src/components/dashboard/task-card.tsx"
Task: "Create task list component in frontend/src/components/dashboard/task-list.tsx"
Task: "Create create task form in frontend/src/components/dashboard/create-task-form.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundational (T005-T012)
3. Complete Phase 3: User Story 1 (T013-T024)
4. **STOP and VALIDATE**: Test User Story 1 independently
   - Dashboard loads with live tasks
   - Can create new task
   - Can update task status
   - Loading skeletons appear during fetch
   - Toast notifications on errors
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Add User Story 4 → Test independently → Deploy/Demo
6. Complete UX Hardening → Final polish
7. Run Validation → Production ready

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (T013-T024)
   - Developer B: User Story 2 (T025-T033)
   - Developer C: User Story 3 (T034-T041)
   - Developer D: User Story 4 (T042-T050)
3. Stories complete and integrate independently
4. Team reunites for UX Hardening (Phase 7)
5. Team runs Validation together (Phase 8)

---

## Task Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup | 4 tasks |
| Phase 2 | Foundational | 8 tasks |
| Phase 3 | User Story 1 (Tasks) | 12 tasks |
| Phase 4 | User Story 2 (Plans) | 9 tasks |
| Phase 5 | User Story 3 (Agent Status) | 8 tasks |
| Phase 6 | User Story 4 (Activity Feed) | 9 tasks |
| Phase 7 | UX Hardening | 12 tasks |
| Phase 8 | Validation | 12 tasks |
| **Total** | | **74 tasks** |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Tests are optional - only include if explicitly requested or TDD approach desired
