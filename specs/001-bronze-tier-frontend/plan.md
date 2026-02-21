# Implementation Plan: Bronze Tier Frontend

**Branch**: `1-bronze-tier-frontend` | **Date**: 2026-02-21 | **Spec**: [spec.md](./spec.md)
**Input**: Personal AI Employee – Bronze Tier Frontend (Next.js)

## Summary

Build a production-grade Bronze tier frontend for the Personal AI Employee system using Next.js App Router, TypeScript, Tailwind CSS, shadcn/ui, and Aceternity UI. The implementation delivers a clean, modern, animated dashboard UI with four core screens (Dashboard, Needs Action, Plans, Settings) using mock data, following production-ready architecture patterns that are scalable and extensible for future tiers.

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode)
**Primary Dependencies**: Next.js 14+ (App Router), React 18+, Tailwind CSS 3.x, shadcn/ui, Aceternity UI
**Storage**: N/A (mock data layer - in-memory/JSON files)
**Testing**: Jest + React Testing Library (component tests), Playwright (E2E - optional for Bronze)
**Target Platform**: Web browsers (Chrome, Firefox, Safari, Edge - latest 2 versions)
**Project Type**: Single Next.js application (frontend-only, no backend for Bronze)
**Performance Goals**: Page load < 2s, interactions < 100ms, animations < 300ms
**Constraints**: No hardcoded localhost APIs, no secrets in code, responsive 320px-1920px, WCAG 2.1 AA accessibility
**Scale/Scope**: 4 core screens, ~15-20 reusable components, mock data for 3 entities (AI Status, Plans, Needs Action Items)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle 1: Production-Ready Architecture
- ✅ **Pass**: Folder structure follows Next.js best practices, components are modular and reusable, design system is scalable

### Principle 2: Component-First Design
- ✅ **Pass**: UI built with reusable shadcn components, consistent design tokens, proper component composition

### Principle 3: Test-First (NON-NEGOTIABLE)
- ✅ **Pass**: Component tests written before implementation, acceptance criteria drive test cases, Red-Green-Refactor cycle enforced

### Principle 4: Accessibility First
- ✅ **Pass**: WCAG 2.1 AA compliance required, keyboard navigation, screen reader support, proper ARIA labels

### Principle 5: Future-Tier Extensibility
- ✅ **Pass**: Clean separation between UI and data layer, mock data abstracted for easy API replacement, no hardcoded implementation details

### Principle 6: Simplicity (YAGNI)
- ✅ **Pass**: No authentication, no backend, no WebSockets, no Redux - only what Bronze tier requires

**Gate Result**: ✅ PASS - All principles satisfied. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-bronze-tier-frontend/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts for future tiers)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── app/                      # Next.js App Router
│   ├── layout.tsx            # Root layout with providers
│   ├── page.tsx              # Dashboard (home)
│   ├── needs-action/
│   │   └── page.tsx          # Needs Action view
│   ├── plans/
│   │   └── page.tsx          # Plans view
│   └── settings/
│       └── page.tsx          # Settings view
├── components/
│   ├── ui/                   # shadcn/ui base components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── badge.tsx
│   │   └── ...
│   ├── dashboard/            # Dashboard-specific components
│   │   ├── ai-status-card.tsx
│   │   ├── active-tasks-preview.tsx
│   │   ├── recent-plans-list.tsx
│   │   └── activity-feed.tsx
│   ├── needs-action/         # Needs Action components
│   │   ├── needs-action-list.tsx
│   │   ├── needs-action-item.tsx
│   │   └── needs-action-detail-panel.tsx
│   ├── plans/                # Plans components
│   │   ├── plans-list.tsx
│   │   ├── plan-item.tsx
│   │   └── status-indicator.tsx
│   ├── settings/             # Settings components
│   │   ├── environment-info.tsx
│   │   └── config-display.tsx
│   └── shared/               # Shared components
│       ├── sidebar.tsx
│       ├── header.tsx
│       └── loading-skeleton.tsx
├── lib/
│   ├── utils.ts              # Utility functions (cn, etc.)
│   └── constants.ts          # App-wide constants
├── data/
│   ├── mock/                 # Mock data layer
│   │   ├── ai-status.ts
│   │   ├── plans.ts
│   │   ├── needs-action.ts
│   │   └── activity-feed.ts
│   └── types/                # TypeScript type definitions
│       ├── ai-status.ts
│       ├── plan.ts
│       ├── needs-action.ts
│       └── activity.ts
└── styles/
    ├── globals.css           # Global styles + Tailwind
    └── theme.ts              # Theme configuration (dark/light)

tests/
├── components/               # Component unit tests
│   ├── dashboard/
│   ├── needs-action/
│   ├── plans/
│   └── settings/
└── e2e/                      # E2E tests (optional)
    └── navigation.spec.ts

components.json               # shadcn/ui configuration
tailwind.config.ts            # Tailwind configuration
next.config.js                # Next.js configuration
tsconfig.json                 # TypeScript configuration
```

**Structure Decision**: Single Next.js application with App Router architecture. Components organized by feature domain for scalability. Mock data layer abstracted for easy replacement in Silver tier.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A - No violations detected | - | - |

## Phase 0: Research & Discovery

### Research Tasks

1. **Next.js App Router Best Practices (2024)**
   - Research current App Router patterns for production apps
   - Identify proper use of Server vs Client Components
   - Document layout and routing conventions

2. **shadcn/ui Integration Patterns**
   - Research optimal shadcn setup for Next.js 14+
   - Identify theming and customization approaches
   - Document component composition patterns

3. **Aceternity UI Integration**
   - Research Aceternity UI components compatible with App Router
   - Identify animation libraries and integration patterns
   - Document performance considerations for animations

4. **Accessibility in Next.js Applications**
   - Research WCAG 2.1 AA compliance patterns for Next.js
   - Identify ARIA best practices for dynamic content
   - Document keyboard navigation patterns

5. **Mock Data Layer Design**
   - Research patterns for mock data abstraction
   - Identify easy migration path to real APIs (Silver tier)
   - Document type-safe mock data generation

**Output**: `research.md` with resolved technical decisions

## Phase 1: Design & Contracts

### Deliverables

1. **data-model.md**: TypeScript interfaces for all entities
   - AI Status (Idle, Thinking, Planning)
   - Plan (Draft, Ready, Done)
   - Needs Action Item
   - Activity Feed Item
   - Task

2. **contracts/**: API contract stubs for Silver tier
   - REST endpoint definitions (OpenAPI format)
   - Request/response schemas
   - Error response formats

3. **quickstart.md**: Developer onboarding guide
   - Local development setup
   - Build and run commands
   - Testing instructions

4. **Agent Context Update**: Update `.claude/agents/` with technology stack

**Output**: Complete design documentation ready for task breakdown

## Phase 2: Implementation Phases

### Phase 2.1: Project Initialization
**Goal**: Set up Next.js project with all required dependencies

**Tasks**:
- Initialize Next.js 14+ with TypeScript
- Configure Tailwind CSS with custom theme
- Install and configure shadcn/ui
- Integrate Aceternity UI components
- Set up ESLint, Prettier, and testing framework

**Done Criteria**:
- `npm run dev` starts without errors
- Tailwind classes apply correctly
- shadcn components import successfully
- Basic test suite runs

---

### Phase 2.2: Design System Foundation
**Goal**: Establish layout shell and navigation structure

**Tasks**:
- Create root layout with sidebar navigation
- Implement responsive header component
- Set up typography system (fonts, sizes, weights)
- Configure dark/light theme toggle
- Create loading skeleton components

**Done Criteria**:
- Sidebar navigation works on all screen sizes
- Theme toggle persists preference
- Typography consistent across all pages
- Loading states display properly

---

### Phase 2.3: Core Dashboard Layout
**Goal**: Implement Dashboard screen with all required components

**Tasks**:
- Create AI Status Card component with 3 states
- Build Active Tasks Preview component
- Implement Recent Plans List component
- Create Activity Feed component
- Add animated background effects (Aceternity)

**Done Criteria**:
- All 4 dashboard sections render correctly
- Status card shows appropriate visual state
- Hover effects and transitions work smoothly
- Responsive on mobile and desktop

---

### Phase 2.4: Needs Action Page
**Goal**: Implement Needs Action view with list and detail panel

**Tasks**:
- Create Needs Action List component
- Build Needs Action Item card component
- Implement Detail Panel with slide-in animation
- Add "Generate Plan" button (mock action)
- Handle empty state gracefully

**Done Criteria**:
- List displays all mock items
- Clicking item opens detail panel
- "Generate Plan" provides visual feedback
- Empty state shows helpful message

---

### Phase 2.5: Plans Page
**Goal**: Implement Plans view with status indicators

**Tasks**:
- Create Plans List component
- Build Plan Item card component
- Implement Status Indicator (Draft/Ready/Done)
- Add filtering/sorting (optional enhancement)
- Apply hover card effects

**Done Criteria**:
- All plans display with correct status
- Status indicators visually distinct
- Hover effects smooth and consistent
- Layout responsive

---

### Phase 2.6: Settings Page
**Goal**: Implement Settings view with environment info

**Tasks**:
- Create Environment Info panel
- Build Config Display component
- Add mock configuration items
- Apply consistent styling

**Done Criteria**:
- Environment info displays correctly
- Configuration items organized clearly
- Consistent with overall design system

---

### Phase 2.7: Polish & Motion Layer
**Goal**: Add animations, transitions, and micro-interactions

**Tasks**:
- Implement page transition animations
- Add hover state animations to all interactive elements
- Create micro-animations for buttons and cards
- Fine-tune animation timing (all < 300ms)
- Add subtle background animations (Aceternity)

**Done Criteria**:
- All animations smooth and performant
- No jank or layout shifts
- Animation timing consistent
- Perceived performance high

---

### Phase 2.8: Structural Validation
**Goal**: Code quality pass and final validation

**Tasks**:
- Review folder structure for consistency
- Extract reusable components where applicable
- Add TypeScript strict type checking
- Run accessibility audit (axe-core)
- Performance optimization (lazy loading, code splitting)
- Write README with architecture decisions

**Done Criteria**:
- No TypeScript errors
- Accessibility audit passes (95%+ WCAG 2.1 AA)
- Page load < 2s
- Code properly commented and documented
- README complete

---

## Acceptance Criteria Validation

| Success Criteria | Validation Method | Target |
|------------------|-------------------|--------|
| SC-001: Status identified in 3s | User testing / heuristic evaluation | ✅ Pass |
| SC-002: Interactions < 100ms | React DevTools profiler | ✅ Pass |
| SC-003: Responsive 320px-1920px | Browser dev tools testing | ✅ Pass |
| SC-004: 95% WCAG 2.1 AA | axe-core audit | ✅ Pass |
| SC-005: Page load < 2s | Lighthouse performance | ✅ Pass |
| SC-006: Animations < 300ms | Code review / timing checks | ✅ Pass |
| SC-007: Navigation ≤ 2 clicks | User flow verification | ✅ Pass |
| SC-008: Color contrast 4.5:1 | Contrast checker tools | ✅ Pass |

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Aceternity UI compatibility with App Router | Medium | Test components early, have fallback animations ready |
| Animation performance on low-end devices | Medium | Implement reduced-motion media query, test on various devices |
| Scope creep (adding features beyond Bronze) | High | Strict adherence to spec, defer enhancements to Silver |
| Accessibility compliance gaps | Medium | Run audits early and often, use accessible shadcn components |

## Next Steps

1. ✅ Complete this plan review
2. ➡️ Run `/sp.tasks` to break down into actionable tasks
3. ➡️ Begin Phase 2.1 implementation
