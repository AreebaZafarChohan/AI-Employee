# Research: Silver Tier Frontend

**Feature**: 001-silver-tier-frontend  
**Date**: 2026-02-22  
**Purpose**: Resolve all NEEDS CLARIFICATION items and document technical decisions

---

## Decision 1: Backend API Base URL

**Chosen**: `NEXT_PUBLIC_API_URL` environment variable (e.g., `http://localhost:8000/api/v1` or production URL)

**Rationale**: Next.js requires `NEXT_PUBLIC_` prefix for client-side exposure. Allows different URLs per environment (dev, staging, production).

**Alternatives Considered**:
- Hardcoded `localhost:8000` - Rejected: violates FR-014 (no hardcoded localhost)
- Server-side proxy - Rejected: adds unnecessary complexity for Silver tier

**Implementation**:
```typescript
// src/lib/api-config.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
```

---

## Decision 2: TanStack Query Version

**Chosen**: TanStack Query v5 (latest stable)

**Rationale**: Better TypeScript support, improved devtools, smaller bundle size. Compatible with Next.js 14 and React 18.

**Alternatives Considered**:
- v4 - Rejected: v5 has better DX and is stable since late 2023
- SWR - Rejected: team familiarity with TanStack Query; richer feature set for complex state

**Implementation**:
```bash
npm install @tanstack/react-query@^5
```

---

## Decision 3: Error Response Structure

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

**Implementation**:
```typescript
// src/lib/api-client.ts
interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}
```

---

## Decision 4: Task Status Values

**Chosen**: `["pending", "in-progress", "completed", "cancelled"]`

**Rationale**: Standard workflow states covering common task lifecycle. Matches backend enum values.

**Alternatives Considered**:
- Simpler: `["open", "done"]` - Rejected: insufficient granularity for AI Employee workflow
- More complex with sub-states - Rejected: YAGNI for Silver tier

**Implementation**:
```typescript
// src/types/task.ts
export type TaskStatus = 'pending' | 'in-progress' | 'completed' | 'cancelled';
```

---

## Decision 5: Plan Structure Format

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

**Implementation**:
```typescript
// src/types/plan.ts
export interface Plan {
  id: string;
  taskId: string;
  sections: PlanSection[];
  summary: string;
  createdAt: string;
}

export interface PlanSection {
  title: string;
  steps: string[];
}
```

---

## Decision 6: Polling Strategy for Agent Status

**Chosen**: TanStack Query `refetchInterval: 30000` (30 seconds)

**Rationale**: Meets NFR-001 requirement. TanStack Query handles background refetch, stale-while-revalidate caching, and automatic cleanup on unmount.

**Alternatives Considered**:
- `setInterval` manual polling - Rejected: requires manual cleanup, no caching
- WebSocket - Rejected: out of scope (Gold tier)
- Longer interval (60s) - Rejected: 30s provides better UX per spec

**Implementation**:
```typescript
// src/hooks/use-system-state.ts
export function useSystemState() {
  return useQuery({
    queryKey: ['systemState'],
    queryFn: fetchSystemState,
    refetchInterval: 30000, // 30 seconds
  });
}
```

---

## Decision 7: Environment Variable Configuration

**Chosen**: `.env.local` for local development, `.env.example` as template

**Rationale**: Next.js standard pattern. `.env.local` is gitignored by default; `.env.example` provides documentation.

**Alternatives Considered**:
- Single `.env` file - Rejected: risks committing secrets
- Runtime config via API - Rejected: unnecessary for frontend-only config

**Implementation**:
```bash
# .env.example
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# .env.local (gitignored)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

---

## Decision 8: Loading State Pattern

**Chosen**: Skeleton loaders matching content layout

**Rationale**: Provides visual continuity and perceived performance improvement over spinners. Matches shadcn/ui patterns.

**Alternatives Considered**:
- Spinner only - Rejected: poorer UX; doesn't indicate content structure
- Blank until loaded - Rejected: jarring; users unsure if loading

**Implementation**:
```typescript
// src/components/shared/loading-skeleton.tsx
export function TaskListSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map(i => (
        <Skeleton key={i} className="h-24 w-full" />
      ))}
    </div>
  );
}
```

---

## Decision 9: Toast Notification Strategy

**Chosen**: shadcn/ui toast component with contextual variants

**Rationale**: Consistent with existing UI library. Supports success, error, warning, and info variants.

**Alternatives Considered**:
- Custom modal dialogs - Rejected: too intrusive for notifications
- Browser alerts - Rejected: poor UX; blocks interaction

**Implementation**:
```typescript
// src/components/ui/toast.tsx (shadcn)
import { toast } from '@/components/ui/use-toast';

toast({
  title: "Task created",
  description: "Your task has been saved successfully.",
  variant: "success",
});
```

---

## Decision 10: Optimistic Updates Pattern

**Chosen**: TanStack Query optimistic updates with rollback on failure

**Rationale**: Provides instant UI feedback (SC-002: <1 second). Rollback ensures data consistency on API failure.

**Alternatives Considered**:
- Wait for API response - Rejected: feels slow; violates SC-002
- Manual cache updates - Rejected: TanStack Query provides built-in pattern

**Implementation**:
```typescript
// src/hooks/use-tasks.ts
export function useUpdateTask() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: updateTaskApi,
    onMutate: async (newTask) => {
      await queryClient.cancelQueries({ queryKey: ['tasks'] });
      const previous = queryClient.getQueryData(['tasks']);
      queryClient.setQueryData(['tasks'], (old) => [...old, newTask]);
      return { previous };
    },
    onError: (err, newTask, context) => {
      queryClient.setQueryData(['tasks'], context.previous);
      toast({ title: "Failed to update task", variant: "error" });
    },
  });
}
```

---

## Summary of Resolved Unknowns

| Unknown | Resolution | Location |
|---------|-----------|----------|
| Backend API base URL format | `NEXT_PUBLIC_API_URL` env var | `api-config.ts` |
| TanStack Query version | v5 (latest stable) | `package.json` |
| Error response structure | Standard REST format with code/message | `api-client.ts` |
| Task status values | `pending`, `in-progress`, `completed`, `cancelled` | `types/task.ts` |
| Plan structure format | Sections with steps + summary | `types/plan.ts` |
| Polling interval | 30 seconds via `refetchInterval` | `hooks/use-system-state.ts` |
| Environment configuration | `.env.local` + `.env.example` | Root |
| Loading state pattern | Skeleton loaders | `components/shared/` |
| Toast notifications | shadcn/ui toast component | `components/ui/` |
| Optimistic updates | TanStack Query pattern with rollback | `hooks/use-tasks.ts` |

---

**Status**: ✅ All NEEDS CLARIFICATION items resolved. Ready for Phase 1 design.
