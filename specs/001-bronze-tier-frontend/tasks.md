# Tasks: Bronze Tier Frontend

**Feature**: Bronze Tier Frontend  
**Branch**: `1-bronze-tier-frontend`  
**Input**: Design documents from `/specs/001-bronze-tier-frontend/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Component tests are OPTIONAL for Bronze tier - included below for production-grade quality assurance.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3])
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths follow plan.md structure: App Router, components by feature domain

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and tooling configuration

- [X] T001 Initialize Next.js 14+ project with TypeScript in repository root
- [X] T002 [P] Install and configure Tailwind CSS 3.x with custom theme in `tailwind.config.ts`
- [X] T003 [P] Install and configure shadcn/ui components (`npx shadcn-ui@latest init`)
- [X] T004 [P] Install Aceternity UI components and Framer Motion dependency
- [X] T005 [P] Configure ESLint, Prettier, and TypeScript strict mode in respective config files
- [ ] T006 [P] Setup Jest + React Testing Library configuration in `jest.config.js` and `tests/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 [P] Create TypeScript type definitions in `src/data/types/ai-status.ts` per data-model.md
- [X] T008 [P] Create TypeScript type definitions in `src/data/types/plan.ts` per data-model.md
- [X] T009 [P] Create TypeScript type definitions in `src/data/types/needs-action.ts` per data-model.md
- [X] T010 [P] Create TypeScript type definitions in `src/data/types/activity.ts` per data-model.md
- [X] T011 [P] Create TypeScript type definitions in `src/data/types/task.ts` per data-model.md
- [X] T012 [P] Create mock data layer in `src/data/mock/ai-status.ts` with sample data
- [X] T013 [P] Create mock data layer in `src/data/mock/plans.ts` with sample data
- [X] T014 [P] Create mock data layer in `src/data/mock/needs-action.ts` with sample data
- [X] T015 [P] Create mock data layer in `src/data/mock/activity-feed.ts` with sample data
- [X] T016 Create utility functions in `src/lib/utils.ts` (cn helper, common utilities)
- [X] T017 Create app-wide constants in `src/lib/constants.ts`
- [X] T018 Setup global styles with Tailwind directives in `src/styles/globals.css`
- [ ] T019 Configure dark/light theme system in `src/styles/theme.ts`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - View AI Employee Dashboard Status (Priority: P1) 🎯 MVP

**Goal**: Implement dashboard with AI Status card showing Idle/Thinking/Planning states

**Independent Test**: Can be fully tested by opening the dashboard and observing the AI Status card displaying one of three states with appropriate visual indicators

### Tests for User Story 1 (OPTIONAL) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T020 [P] [US1] Component test for AiStatusCard renders correctly in `tests/components/dashboard/ai-status-card.test.tsx`
- [ ] T021 [P] [US1] Component test for ActiveTasksPreview in `tests/components/dashboard/active-tasks-preview.test.tsx`
- [ ] T022 [P] [US1] Component test for RecentPlansList in `tests/components/dashboard/recent-plans-list.test.tsx`
- [ ] T023 [P] [US1] Component test for ActivityFeed in `tests/components/dashboard/activity-feed.test.tsx`

### Implementation for User Story 1

- [X] T024 [P] [US1] Create shadcn Card component in `src/components/ui/card.tsx` (if not already added)
- [X] T025 [P] [US1] Create shadcn Badge component in `src/components/ui/badge.tsx` (if not already added)
- [ ] T026 [P] [US1] Create AnimatedBackground wrapper component in `src/components/shared/animated-background.tsx` using Aceternity UI
- [X] T027 [US1] Implement AiStatusCard component in `src/components/dashboard/ai-status-card.tsx` with 3 state variants
- [X] T028 [US1] Implement ActiveTasksPreview component in `src/components/dashboard/active-tasks-preview.tsx`
- [X] T029 [US1] Implement RecentPlansList component in `src/components/dashboard/recent-plans-list.tsx`
- [X] T030 [US1] Implement ActivityFeed component in `src/components/dashboard/activity-feed.tsx`
- [X] T031 [US1] Create root layout with navigation structure in `src/app/layout.tsx`
- [X] T032 [US1] Implement Dashboard page in `src/app/page.tsx` integrating all 4 dashboard components
- [X] T033 [US1] Add hover effects and transitions to dashboard components using Framer Motion
- [ ] T034 [US1] Add responsive styling for dashboard on mobile devices (320px-640px)

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently - MVP ready!

---

## Phase 4: User Story 2 - View and Interact with Needs Action Items (Priority: P2)

**Goal**: Implement Needs Action view with list, detail panel, and "Generate Plan" button

**Independent Test**: Can be fully tested by navigating to Needs Action view, seeing a list of input items, clicking one to view details, and observing the detail panel with a "Generate Plan" button

### Tests for User Story 2 (OPTIONAL) ⚠️

- [ ] T035 [P] [US2] Component test for NeedsActionList in `tests/components/needs-action/needs-action-list.test.tsx`
- [ ] T036 [P] [US2] Component test for NeedsActionItem in `tests/components/needs-action/needs-action-item.test.tsx`
- [ ] T037 [P] [US2] Component test for NeedsActionDetailPanel in `tests/components/needs-action/needs-action-detail-panel.test.tsx`

### Implementation for User Story 2

- [X] T038 [P] [US2] Create shadcn Button component in `src/components/ui/button.tsx` (if not already added)
- [X] T039 [P] [US2] Create shadcn ScrollArea component in `src/components/ui/scroll-area.tsx` (if not already added)
- [X] T040 [P] [US2] Create LoadingSkeleton component in `src/components/shared/loading-skeleton.tsx`
- [X] T041 [US2] Implement NeedsActionList component in `src/components/needs-action/needs-action-list.tsx`
- [X] T042 [US2] Implement NeedsActionItem card component in `src/components/needs-action/needs-action-item.tsx`
- [X] T043 [US2] Implement NeedsActionDetailPanel with slide-in animation in `src/components/needs-action/needs-action-detail-panel.tsx`
- [X] T044 [US2] Create empty state component for Needs Action view in `src/components/shared/empty-state.tsx`
- [X] T045 [US2] Implement Needs Action page in `src/app/needs-action/page.tsx`
- [X] T046 [US2] Add "Generate Plan" button with mock action handler and visual feedback
- [ ] T047 [US2] Add keyboard navigation support for Needs Action list items
- [X] T048 [US2] Add responsive styling for Needs Action page on mobile devices

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - View Plans and Their Status (Priority: P3)

**Goal**: Implement Plans view with list and status indicators (Draft/Ready/Done)

**Independent Test**: Can be fully tested by navigating to Plans view and observing a list of plans with status indicators

### Tests for User Story 3 (OPTIONAL) ⚠️

- [ ] T049 [P] [US3] Component test for PlansList in `tests/components/plans/plans-list.test.tsx`
- [ ] T050 [P] [US3] Component test for PlanItem in `tests/components/plans/plan-item.test.tsx`
- [ ] T051 [P] [US3] Component test for StatusIndicator in `tests/components/plans/status-indicator.test.tsx`

### Implementation for User Story 3

- [X] T052 [P] [US3] Create shadcn Separator component in `src/components/ui/separator.tsx` (if not already added)
- [X] T053 [US3] Implement StatusIndicator component in `src/components/plans/status-indicator.tsx` with 3 state variants
- [X] T054 [US3] Implement PlanItem card component in `src/components/plans/plan-item.tsx`
- [X] T055 [US3] Implement PlansList component in `src/components/plans/plans-list.tsx`
- [X] T056 [US3] Implement Plans page in `src/app/plans/page.tsx`
- [X] T057 [US3] Add hover card effects to plan items using Framer Motion
- [X] T058 [US3] Add optional filtering/sorting functionality for plans list
- [X] T059 [US3] Add responsive styling for Plans page on mobile devices

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently

---

## Phase 6: User Story 4 - View System Settings and Configuration (Priority: P4)

**Goal**: Implement Settings view with environment info and mock configuration display

**Independent Test**: Can be fully tested by navigating to Settings and observing environment information and mock configuration display

### Tests for User Story 4 (OPTIONAL) ⚠️

- [ ] T060 [P] [US4] Component test for EnvironmentInfo in `tests/components/settings/environment-info.test.tsx`
- [ ] T061 [P] [US4] Component test for ConfigDisplay in `tests/components/settings/config-display.test.tsx`

### Implementation for User Story 4

- [X] T062 [US4] Implement EnvironmentInfo panel in `src/components/settings/environment-info.tsx`
- [X] T063 [US4] Implement ConfigDisplay component in `src/components/settings/config-display.tsx`
- [X] T064 [US4] Implement Settings page in `src/app/settings/page.tsx`
- [X] T065 [US4] Add mock configuration items display with proper organization
- [X] T066 [US4] Add responsive styling for Settings page on mobile devices

**Checkpoint**: All 4 user stories should now be independently functional

---

## Phase 7: Shared Components & Navigation

**Purpose**: Complete shared navigation structure and cross-cutting components

- [X] T067 [P] Implement Sidebar navigation component in `src/components/shared/sidebar.tsx`
- [X] T068 [P] Implement Header/Topbar component in `src/components/shared/header.tsx`
- [X] T069 [US1] Add theme toggle (dark/light mode) in header component
- [X] T070 [US1] Add responsive mobile menu toggle for sidebar
- [X] T071 [US1] Ensure navigation works across all 4 pages (Dashboard, Needs Action, Plans, Settings)
- [X] T072 [US1] Add active route highlighting in sidebar navigation

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [X] T073 [P] Implement page transition animations between all routes using Framer Motion
- [X] T074 [P] Add micro-animations to all interactive buttons (hover, active, focus states)
- [X] T075 [P] Fine-tune animation timing to ensure all complete within 300ms
- [X] T076 [P] Add reduced-motion media query support for accessibility
- [ ] T077 [P] Run accessibility audit with axe-core and fix any WCAG 2.1 AA violations
- [X] T078 [P] Verify color contrast ratios meet 4.5:1 minimum (normal text)
- [X] T079 [P] Test keyboard navigation across all pages and components
- [ ] T080 [P] Performance optimization: implement lazy loading for non-critical components
- [ ] T081 [P] Run Lighthouse performance audit and optimize to achieve page load < 2s
- [X] T082 [P] Code cleanup: extract reusable components, remove duplication
- [X] T083 [P] Add JSDoc comments to all exported functions and components
- [ ] T084 [P] Update README.md with architecture decisions and project structure
- [X] T085 [P] Validate no hardcoded localhost API calls exist in codebase
- [X] T086 [P] Validate no secrets or tokens are hardcoded
- [X] T087 [P] Validate all imports resolve correctly (no broken imports)
- [X] T088 [P] Verify dark mode compatibility across all components
- [X] T089 [P] Run TypeScript strict type checking and resolve all errors
- [ ] T090 [P] Run full test suite and ensure all tests pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Shared Components (Phase 7)**: Can start after any user story phase, depends on layout structure
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent, may share components with US1
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Independent, may share components with US1/US2
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Independent, informational only

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Type definitions before mock data
- Mock data before components
- Core components before page integration
- Page complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002-T006)
- All Foundational type definition tasks can run in parallel (T007-T011)
- All Foundational mock data tasks can run in parallel (T012-T015)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- UI base components (Card, Badge, Button) can be created in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Component test for AiStatusCard in tests/components/dashboard/ai-status-card.test.tsx"
Task: "Component test for ActiveTasksPreview in tests/components/dashboard/active-tasks-preview.test.tsx"
Task: "Component test for RecentPlansList in tests/components/dashboard/recent-plans-list.test.tsx"
Task: "Component test for ActivityFeed in tests/components/dashboard/activity-feed.test.tsx"

# Launch all UI base components for User Story 1 together:
Task: "Create shadcn Card component in src/components/ui/card.tsx"
Task: "Create shadcn Badge component in src/components/ui/badge.tsx"

# Launch all dashboard components for User Story 1 together (after base components):
Task: "Implement AiStatusCard component in src/components/dashboard/ai-status-card.tsx"
Task: "Implement ActiveTasksPreview component in src/components/dashboard/active-tasks-preview.tsx"
Task: "Implement RecentPlansList component in src/components/dashboard/recent-plans-list.tsx"
Task: "Implement ActivityFeed component in src/components/dashboard/activity-feed.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T006)
2. Complete Phase 2: Foundational (T007-T019) - **CRITICAL - blocks all stories**
3. Complete Phase 3: User Story 1 (T020-T034)
4. **STOP and VALIDATE**: 
   - Run `npm run dev` and open dashboard
   - Verify AI Status card displays 3 states correctly
   - Verify all dashboard sections render
   - Run `npm run test` for dashboard components
   - Run accessibility audit
5. Deploy/demo if ready - **This is your MVP!**

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (Dashboard) → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 (Needs Action) → Test independently → Deploy/Demo
4. Add User Story 3 (Plans) → Test independently → Deploy/Demo
5. Add User Story 4 (Settings) → Test independently → Deploy/Demo
6. Add Phase 7 (Shared Navigation) → Complete navigation structure
7. Add Phase 8 (Polish) → Production-ready UI
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together (T001-T019)
2. Once Foundational is done:
   - **Developer A**: User Story 1 - Dashboard (T020-T034)
   - **Developer B**: User Story 2 - Needs Action (T035-T048)
   - **Developer C**: User Story 3 - Plans (T049-T059)
   - **Developer D**: User Story 4 - Settings (T060-T066)
3. Stories complete and integrate independently
4. Team reconvenes for Phase 7 (Shared Components) and Phase 8 (Polish)

---

## Task Summary

| Phase | Description | Task Count | Story |
|-------|-------------|------------|-------|
| Phase 1 | Setup | 6 tasks | - |
| Phase 2 | Foundational | 13 tasks | - |
| Phase 3 | User Story 1 (Dashboard) | 15 tasks | US1 (P1) |
| Phase 4 | User Story 2 (Needs Action) | 14 tasks | US2 (P2) |
| Phase 5 | User Story 3 (Plans) | 11 tasks | US3 (P3) |
| Phase 6 | User Story 4 (Settings) | 5 tasks | US4 (P4) |
| Phase 7 | Shared Components | 6 tasks | Mixed |
| Phase 8 | Polish & Validation | 18 tasks | - |
| **Total** | **All Phases** | **88 tasks** | **4 Stories** |

### MVP Scope (User Story 1 Only)
- **Minimum**: Phases 1-3 complete (34 tasks)
- **Deliverable**: Working dashboard with AI Status, Tasks, Plans, Activity Feed

### Full Bronze Scope
- **Complete**: All 8 phases (88 tasks)
- **Deliverable**: Production-grade 4-screen dashboard UI with animations and accessibility

---

## Notes

- [P] tasks = different files, no dependencies, can run in parallel
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are OPTIONAL - skip test tasks if not doing TDD for Bronze tier
- Commit after each task or logical group of tasks
- Stop at each checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- **CRITICAL**: Phase 2 (Foundational) MUST be complete before starting any user story
