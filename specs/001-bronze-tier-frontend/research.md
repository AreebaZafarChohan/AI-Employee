# Research: Bronze Tier Frontend Technical Decisions

**Feature**: Bronze Tier Frontend  
**Date**: 2026-02-21  
**Branch**: 1-bronze-tier-frontend

## Overview

This document consolidates all technical research and decisions for the Bronze Tier Frontend implementation. Each section addresses a research task from the implementation plan.

---

## 1. Next.js App Router Best Practices (2024)

### Decision: Use App Router with Server Components by Default

**What was chosen**:
- Next.js 14+ with App Router (`app/` directory)
- Server Components as default (use `'use client'` directive only when needed)
- Layout-based routing with nested layouts
- Server-side data fetching with async components

**Why chosen**:
- Better performance (reduced bundle size, server rendering)
- Simplified data fetching (no useEffect for initial data)
- Better SEO and initial page load
- Future-proof (Next.js direction)
- Aligns with "Server Components + minimal client state" constraint

**Alternatives considered**:
- **Pages Router**: Rejected - legacy approach, limited capabilities
- **All Client Components**: Rejected - larger bundles, worse performance

**Implementation pattern**:
```typescript
// Server Component (default)
export default async function Dashboard() {
  const data = await fetchData(); // Direct async/await
  return <DashboardView data={data} />;
}

// Client Component (when interactivity needed)
'use client';
export function InteractiveComponent() {
  const [state, setState] = useState();
  // ... client logic
}
```

---

## 2. shadcn/ui Integration Patterns

### Decision: Use shadcn/ui as Base Component Library

**What was chosen**:
- shadcn/ui components (Button, Card, Badge, etc.)
- Radix UI primitives under the hood
- Tailwind CSS for styling
- Components copied into project (not npm dependency)

**Why chosen**:
- Full control over component code
- No runtime dependency
- Accessible by default (Radix UI)
- Highly customizable
- Perfect for production-grade applications
- Aligns with "clean design system" requirement

**Alternatives considered**:
- **Material-UI**: Rejected - heavier, less customizable
- **Chakra UI**: Rejected - runtime dependency, larger bundle
- **Headless UI**: Rejected - requires more custom styling work

**Implementation pattern**:
```bash
# Install shadcn CLI
npx shadcn-ui@latest init

# Add components as needed
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add badge
```

**Component composition**:
```typescript
// Combine shadcn primitives for custom components
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function AiStatusCard({ status }: { status: AiStatus }) {
  return (
    <Card>
      <CardHeader>
        <Badge variant={getStatusVariant(status)}>{status}</Badge>
      </CardHeader>
      <CardContent>...</CardContent>
    </Card>
  );
}
```

---

## 3. Aceternity UI Integration

### Decision: Use Aceternity UI for Animations and Effects

**What was chosen**:
- Aceternity UI components for animated backgrounds
- Framer Motion as animation engine (Aceternity dependency)
- Tailwind CSS for styling
- Selective use of effects (not overwhelming)

**Why chosen**:
- Modern, polished animations
- Built on Framer Motion (industry standard)
- Tailwind-compatible
- Copy-paste components (like shadcn)
- Perfect for "animated background, hover card effects, subtle transitions"

**Alternatives considered**:
- **Framer Motion alone**: Rejected - requires building effects from scratch
- **React Spring**: Rejected - steeper learning curve
- **GSAP**: Rejected - overkill for subtle UI animations

**Selected Aceternity components**:
- **Animated Background**: Grid background or dot pattern
- **Hover Cards**: Card hover effects with scale/shadow
- **Transitions**: Fade in/out, slide animations
- **Motion wrappers**: For page transitions

**Implementation pattern**:
```typescript
// Example: Animated background
import { BackgroundGrid } from "@/components/ui/background-grid";

export function Dashboard() {
  return (
    <div className="relative">
      <BackgroundGrid />
      <Content />
    </div>
  );
}

// Example: Hover card effect
import { motion } from "framer-motion";

export function PlanCard({ plan }: { plan: Plan }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -2 }}
      transition={{ duration: 0.2 }}
    >
      {/* Card content */}
    </motion.div>
  );
}
```

**Performance considerations**:
- Use `will-change` sparingly
- Limit concurrent animations
- Respect `prefers-reduced-motion`
- Keep animation duration < 300ms

---

## 4. Accessibility in Next.js Applications

### Decision: WCAG 2.1 AA Compliance with Proactive Testing

**What was chosen**:
- WCAG 2.1 AA as minimum standard
- Semantic HTML elements
- ARIA labels where needed
- Keyboard navigation support
- Focus management
- Color contrast ≥ 4.5:1 (normal text), ≥ 3:1 (large text)

**Why chosen**:
- Required by spec (SC-004: 95% compliance)
- Legal/ethical requirement for production apps
- shadcn/Radix components accessible by default
- Improves UX for all users

**Alternatives considered**:
- **WCAG 2.0**: Rejected - outdated, 2.1 has mobile improvements
- **WCAG 2.2 AAA**: Rejected - overly strict for Bronze tier

**Implementation patterns**:

**Semantic HTML**:
```typescript
// Use semantic elements
<nav aria-label="Main navigation">
  <ul role="list">
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

<main id="main-content" role="main">
  {/* Page content */}
</main>
```

**Focus management**:
```typescript
// Trap focus in modal/panel
import { FocusTrap } from "@/components/shared/focus-trap";

export function DetailPanel({ isOpen, onClose }: Props) {
  return (
    <FocusTrap active={isOpen}>
      <Panel content={...} />
    </FocusTrap>
  );
}
```

**Keyboard navigation**:
```typescript
// Handle keyboard events
function handleKeyDown(e: KeyboardEvent) {
  if (e.key === 'Escape') onClose();
  if (e.key === 'Enter' || e.key === ' ') onSelect();
}
```

**Testing tools**:
- **axe-core**: Automated accessibility testing
- **Lighthouse**: Accessibility audits
- **Manual testing**: Keyboard-only navigation

---

## 5. Mock Data Layer Design

### Decision: Abstracted Mock Data with Type-Safe Interfaces

**What was chosen**:
- TypeScript interfaces for all entities
- Mock data in separate `data/mock/` directory
- Functions that return Promise (mimics API calls)
- Easy replacement with real API in Silver tier

**Why chosen**:
- Clean separation of concerns
- Type safety throughout
- Easy migration to real APIs
- No code changes needed for Silver tier integration
- Supports "future-tier extensibility" principle

**Alternatives considered**:
- **Hardcoded data in components**: Rejected - tight coupling
- **MSW (Mock Service Worker)**: Rejected - overkill for Bronze
- **JSON Server**: Rejected - requires separate process

**Implementation pattern**:

**Type definitions** (`src/data/types/`):
```typescript
// src/data/types/ai-status.ts
export type AiStatusType = 'Idle' | 'Thinking' | 'Planning';

export interface AiStatus {
  id: string;
  type: AiStatusType;
  updatedAt: Date;
  message?: string;
}

// src/data/types/plan.ts
export type PlanStatus = 'Draft' | 'Ready' | 'Done';

export interface Plan {
  id: string;
  title: string;
  status: PlanStatus;
  createdAt: Date;
  description?: string;
}
```

**Mock data** (`src/data/mock/`):
```typescript
// src/data/mock/plans.ts
import { Plan } from '@/data/types/plan';

const MOCK_PLANS: Plan[] = [
  {
    id: '1',
    title: 'Q1 Marketing Strategy',
    status: 'Ready',
    createdAt: new Date('2026-02-15'),
    description: 'Comprehensive marketing plan for Q1'
  },
  // ... more mock data
];

export async function getPlans(): Promise<Plan[]> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_PLANS;
}

export async function getPlanById(id: string): Promise<Plan | undefined> {
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_PLANS.find(p => p.id === id);
}
```

**Silver tier migration**:
```typescript
// Future: Replace mock implementation with real API
// src/data/real/plans.ts
export async function getPlans(): Promise<Plan[]> {
  const response = await fetch('/api/plans');
  if (!response.ok) throw new Error('Failed to fetch plans');
  return response.json();
}

// Only change: import path in components
// Before: import { getPlans } from '@/data/mock/plans';
// After:  import { getPlans } from '@/data/real/plans';
```

---

## 6. Responsive Design Strategy

### Decision: Mobile-First Responsive Breakpoints

**What was chosen**:
- Mobile-first approach
- Tailwind breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Fluid typography and spacing
- Collapsible sidebar on mobile
- Touch-friendly targets (≥ 44px)

**Why chosen**:
- Industry standard approach
- Tailwind-optimized
- Ensures usability across all devices
- Aligns with "responsive 320px-1920px" requirement

**Implementation pattern**:
```typescript
// Mobile-first responsive layout
export function Dashboard() {
  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 md:p-6">
      {/* Sidebar: hidden on mobile, visible on md+ */}
      <aside className="hidden md:block w-64">
        <Sidebar />
      </aside>

      {/* Mobile header */}
      <header className="md:hidden">
        <MobileHeader />
      </header>

      {/* Main content */}
      <main className="flex-1">
        <AiStatusCard />
      </main>
    </div>
  );
}
```

---

## 7. Dark Mode Implementation

### Decision: System-Preference Dark Mode with Manual Toggle

**What was chosen**:
- Tailwind CSS `dark:` variant
- System preference detection (`prefers-color-scheme`)
- Manual toggle in settings
- Persistence via localStorage
- CSS variables for theme colors

**Why chosen**:
- shadcn/ui supports dark mode out of box
- User preference respected
- Minimal implementation overhead
- Aligns with "dark mode ready" requirement

**Implementation pattern**:
```typescript
// Theme provider
'use client';
export function ThemeProvider({ children }: Props) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Check system preference on mount
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    setTheme(prefersDark ? 'dark' : 'light');
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    localStorage.setItem('theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

---

## Summary of Technical Decisions

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| Framework | Next.js 14+ App Router | Performance, future-proof, server components |
| UI Library | shadcn/ui | Accessible, customizable, no runtime |
| Animations | Aceternity UI + Framer Motion | Modern effects, Tailwind-compatible |
| Styling | Tailwind CSS | Industry standard, rapid development |
| State Management | React state only | No Redux needed for Bronze scope |
| Data Layer | Abstracted mock data | Easy Silver tier migration |
| Accessibility | WCAG 2.1 AA | Compliance, better UX |
| Responsive | Mobile-first breakpoints | Universal usability |
| Theme | Dark mode with toggle | User preference, modern expectation |

## Next Steps

1. ✅ Research complete
2. ➡️ Proceed to Phase 1: Design & Contracts
3. Create `data-model.md` with TypeScript interfaces
4. Create API contract stubs in `contracts/`
5. Write `quickstart.md` developer guide
