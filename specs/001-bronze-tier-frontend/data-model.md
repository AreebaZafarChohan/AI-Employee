# Data Model: Bronze Tier Frontend

**Feature**: Bronze Tier Frontend  
**Date**: 2026-02-21  
**Branch**: 1-bronze-tier-frontend

## Overview

This document defines all TypeScript interfaces and types for the Bronze Tier Frontend entities. All types are designed to be easily replaced with real API responses in Silver tier.

---

## Core Entities

### AI Status

Represents the current operational state of the AI Employee.

```typescript
// src/data/types/ai-status.ts

/**
 * AI Employee operational states
 * - Idle: No active processing, waiting for input
 * - Thinking: Actively processing or analyzing
 * - Planning: Creating a structured plan
 */
export type AiStatusType = 'Idle' | 'Thinking' | 'Planning';

/**
 * AI Status visual variants for UI components
 */
export type AiStatusVariant = 'default' | 'processing' | 'active';

/**
 * Represents the current state of the AI Employee
 */
export interface AiStatus {
  /** Unique identifier for the status record */
  id: string;
  
  /** Current operational state */
  type: AiStatusType;
  
  /** When the status was last updated */
  updatedAt: Date;
  
  /** Optional human-readable message about current activity */
  message?: string;
  
  /** Optional timestamp of when current state started */
  startedAt?: Date;
}

/**
 * Maps AI status types to UI variants
 */
export const AI_STATUS_VARIANTS: Record<AiStatusType, AiStatusVariant> = {
  'Idle': 'default',
  'Thinking': 'processing',
  'Planning': 'active'
};
```

---

### Plan

Represents a structured approach created by the AI Employee.

```typescript
// src/data/types/plan.ts

/**
 * Plan lifecycle states
 * - Draft: Plan is being created/edited
 * - Ready: Plan is complete and ready for review
 * - Done: Plan has been executed/completed
 */
export type PlanStatus = 'Draft' | 'Ready' | 'Done';

/**
 * Visual badge variants for plan status
 */
export type PlanStatusVariant = 'secondary' | 'default' | 'success';

/**
 * Represents a plan created by the AI Employee
 */
export interface Plan {
  /** Unique identifier for the plan */
  id: string;
  
  /** Short, descriptive title */
  title: string;
  
  /** Current lifecycle state */
  status: PlanStatus;
  
  /** When the plan was created */
  createdAt: Date;
  
  /** Optional detailed description of the plan */
  description?: string;
  
  /** Optional timestamp of last update */
  updatedAt?: Date;
  
  /** Optional timestamp when plan was completed */
  completedAt?: Date;
  
  /** Optional array of task IDs associated with this plan */
  taskIds?: string[];
}

/**
 * Maps plan status to badge variants
 */
export const PLAN_STATUS_VARIANTS: Record<PlanStatus, PlanStatusVariant> = {
  'Draft': 'secondary',
  'Ready': 'default',
  'Done': 'success'
};

/**
 * Sort order for plan lists
 */
export type PlanSortOrder = 'newest' | 'oldest' | 'status';
```

---

### Needs Action Item

Represents a task or input request that requires user attention.

```typescript
// src/data/types/needs-action.ts

/**
 * Types of action items
 * - InputRequired: User needs to provide information
 * - DecisionNeeded: User needs to make a choice
 * - ReviewRequired: User needs to review and approve
 * - ConfirmationNeeded: User needs to confirm an action
 */
export type ActionItemType = 'InputRequired' | 'DecisionNeeded' | 'ReviewRequired' | 'ConfirmationNeeded';

/**
 * Priority levels for action items
 */
export type ActionItemPriority = 'low' | 'medium' | 'high' | 'urgent';

/**
 * Represents an item requiring user action
 */
export interface NeedsActionItem {
  /** Unique identifier for the action item */
  id: string;
  
  /** Type of action required */
  type: ActionItemType;
  
  /** Priority level */
  priority: ActionItemPriority;
  
  /** When the item was created */
  createdAt: Date;
  
  /** Brief title describing what's needed */
  title: string;
  
  /** Detailed description of what's needed from user */
  description: string;
  
  /** Optional context or background information */
  context?: string;
  
  /** Optional related plan ID */
  relatedPlanId?: string;
  
  /** Optional due date */
  dueDate?: Date;
  
  /** Optional metadata for specific action types */
  metadata?: Record<string, unknown>;
}

/**
 * Maps priority to color variants
 */
export const PRIORITY_VARIANTS: Record<ActionItemPriority, string> = {
  'low': 'text-muted-foreground',
  'medium': 'text-blue-500',
  'high': 'text-orange-500',
  'urgent': 'text-red-500'
};

/**
 * Maps action item type to icon names
 */
export const ACTION_ITEM_ICONS: Record<ActionItemType, string> = {
  'InputRequired': 'message-square',
  'DecisionNeeded': 'scale',
  'ReviewRequired': 'eye',
  'ConfirmationNeeded': 'check-circle'
};
```

---

### Activity Feed Item

Represents a historical action or event in the AI Employee system.

```typescript
// src/data/types/activity.ts

/**
 * Types of activity events
 * - PlanCreated: New plan was generated
 * - PlanUpdated: Existing plan was modified
 * - PlanCompleted: Plan was marked as done
 * - StatusChanged: AI Employee status changed
 * - ActionItemCreated: New action item was created
 * - ActionItemResolved: Action item was completed
 * - SystemEvent: System-level event
 */
export type ActivityType = 
  | 'PlanCreated'
  | 'PlanUpdated'
  | 'PlanCompleted'
  | 'StatusChanged'
  | 'ActionItemCreated'
  | 'ActionItemResolved'
  | 'SystemEvent';

/**
 * Represents an activity feed entry
 */
export interface ActivityFeedItem {
  /** Unique identifier for the activity */
  id: string;
  
  /** Type of activity */
  type: ActivityType;
  
  /** When the activity occurred */
  timestamp: Date;
  
  /** Brief description of what happened */
  title: string;
  
  /** Optional detailed description */
  description?: string;
  
  /** Optional related entity ID (plan, action item, etc.) */
  relatedEntityId?: string;
  
  /** Optional related entity type */
  relatedEntityType?: 'plan' | 'action-item' | 'status';
  
  /** Optional icon name for the activity */
  icon?: string;
}

/**
 * Groups activity items by date for display
 */
export interface ActivityGroup {
  /** Date label (e.g., "Today", "Yesterday", "Feb 20, 2026") */
  label: string;
  
  /** Activities for this date */
  items: ActivityFeedItem[];
}
```

---

### Task

Represents an active unit of work being processed.

```typescript
// src/data/types/task.ts

/**
 * Task states
 * - Pending: Task is queued
 * - InProgress: Task is being worked on
 * - Blocked: Task is waiting on something
 * - Completed: Task is finished
 */
export type TaskStatus = 'Pending' | 'InProgress' | 'Blocked' | 'Completed';

/**
 * Represents a unit of work
 */
export interface Task {
  /** Unique identifier for the task */
  id: string;
  
  /** Task title */
  title: string;
  
  /** Current status */
  status: TaskStatus;
  
  /** When the task was created */
  createdAt: Date;
  
  /** Optional detailed description */
  description?: string;
  
  /** Optional related plan ID */
  planId?: string;
  
  /** Optional estimated completion date */
  estimatedCompletion?: Date;
  
  /** Optional actual completion date */
  completedAt?: Date;
}

/**
 * Maps task status to display colors
 */
export const TASK_STATUS_COLORS: Record<TaskStatus, string> = {
  'Pending': 'bg-gray-100 text-gray-800',
  'InProgress': 'bg-blue-100 text-blue-800',
  'Blocked': 'bg-red-100 text-red-800',
  'Completed': 'bg-green-100 text-green-800'
};
```

---

## Composite Types

### Dashboard Data

Aggregated data for the dashboard view.

```typescript
// src/data/types/dashboard.ts

import { AiStatus } from './ai-status';
import { Task } from './task';
import { Plan } from './plan';
import { ActivityFeedItem } from './activity';

/**
 * Complete dashboard data payload
 */
export interface DashboardData {
  /** Current AI Employee status */
  aiStatus: AiStatus;
  
  /** Preview of active tasks (limited to 3-5) */
  activeTasks: Task[];
  
  /** Recent plans (limited to 5) */
  recentPlans: Plan[];
  
  /** Recent activity feed items (limited to 10) */
  activityFeed: ActivityFeedItem[];
}
```

---

## API Response Types (Future Silver Tier)

Standardized response formats for future API integration.

```typescript
// src/data/types/api.ts

/**
 * Standard API response wrapper
 */
export interface ApiResponse<T> {
  /** Response data payload */
  data: T;
  
  /** Optional error information */
  error?: ApiError;
  
  /** Response metadata */
  meta?: {
    /** Request timestamp */
    timestamp: string;
    /** Request ID for tracing */
    requestId: string;
  };
}

/**
 * Standard error format
 */
export interface ApiError {
  /** Error code */
  code: string;
  
  /** Human-readable message */
  message: string;
  
  /** Optional detailed description */
  details?: Record<string, unknown>;
}

/**
 * Paginated response for lists
 */
export interface PaginatedResponse<T> {
  /** Array of items */
  items: T[];
  
  /** Total count of items */
  total: number;
  
  /** Current page number */
  page: number;
  
  /** Items per page */
  pageSize: number;
  
  /** Total pages */
  totalPages: number;
}
```

---

## Validation Rules

### AI Status Validation

```typescript
export const AiStatusValidation = {
  /** Status type must be one of the defined values */
  type: (value: string): boolean => 
    ['Idle', 'Thinking', 'Planning'].includes(value),
  
  /** Message max length: 140 characters */
  message: (value: string): boolean => 
    value.length <= 140,
  
  /** startedAt must be before or equal to updatedAt */
  timestamps: (startedAt?: Date, updatedAt?: Date): boolean => 
    !startedAt || !updatedAt || startedAt <= updatedAt
};
```

### Plan Validation

```typescript
export const PlanValidation = {
  /** Title required, 1-100 characters */
  title: (value: string): boolean => 
    value.length >= 1 && value.length <= 100,
  
  /** Description max length: 500 characters */
  description: (value: string): boolean => 
    value.length <= 500,
  
  /** Status must be valid */
  status: (value: string): boolean => 
    ['Draft', 'Ready', 'Done'].includes(value)
};
```

### Needs Action Item Validation

```typescript
export const NeedsActionItemValidation = {
  /** Title required, 1-80 characters */
  title: (value: string): boolean => 
    value.length >= 1 && value.length <= 80,
  
  /** Description required, 1-500 characters */
  description: (value: string): boolean => 
    value.length >= 1 && value.length <= 500,
  
  /** Priority must be valid */
  priority: (value: string): boolean => 
    ['low', 'medium', 'high', 'urgent'].includes(value),
  
  /** Type must be valid */
  type: (value: string): boolean => 
    ['InputRequired', 'DecisionNeeded', 'ReviewRequired', 'ConfirmationNeeded'].includes(value)
};
```

---

## State Transitions

### AI Status State Machine

```
Idle ──────┬──────> Thinking
           │
           └──────> Planning

Thinking ──┬──────> Idle
           │
           └──────> Planning

Planning ──┬──────> Idle
           │
           └──────> Thinking
```

### Plan Status State Machine

```
Draft ──────┬──────> Ready
            │
            └──────> (deleted)

Ready ──────┬──────> Done
            │
            └──────> Draft (edit)

Done ───────┴──────> (terminal state)
```

### Task Status State Machine

```
Pending ────┬──────> InProgress
            │
            └──────> (deleted)

InProgress ─┬──────> Completed
            │
            └──────> Blocked

Blocked ────┬──────> InProgress
            │
            └──────> Pending

Completed ──┴──────> (terminal state)
```

---

## Mock Data Examples

### AI Status Mock Data

```typescript
const mockAiStatus: AiStatus = {
  id: 'status-001',
  type: 'Thinking',
  updatedAt: new Date('2026-02-21T10:30:00Z'),
  message: 'Analyzing user requirements...',
  startedAt: new Date('2026-02-21T10:28:00Z')
};
```

### Plan Mock Data

```typescript
const mockPlans: Plan[] = [
  {
    id: 'plan-001',
    title: 'Q1 Marketing Strategy',
    status: 'Ready',
    createdAt: new Date('2026-02-15T09:00:00Z'),
    description: 'Comprehensive marketing plan for Q1 2026',
    updatedAt: new Date('2026-02-18T14:30:00Z')
  },
  {
    id: 'plan-002',
    title: 'Product Launch Timeline',
    status: 'Draft',
    createdAt: new Date('2026-02-20T11:00:00Z'),
    description: 'Timeline and milestones for new product launch'
  },
  {
    id: 'plan-003',
    title: 'Customer Feedback Analysis',
    status: 'Done',
    createdAt: new Date('2026-02-10T08:00:00Z'),
    description: 'Analysis of customer feedback from January survey',
    completedAt: new Date('2026-02-12T16:00:00Z')
  }
];
```

### Needs Action Item Mock Data

```typescript
const mockActionItems: NeedsActionItem[] = [
  {
    id: 'action-001',
    type: 'InputRequired',
    priority: 'high',
    createdAt: new Date('2026-02-21T09:00:00Z'),
    title: 'Provide budget approval',
    description: 'Review and approve the Q1 marketing budget proposal',
    context: 'The marketing team is waiting for budget confirmation to proceed with campaign planning.',
    relatedPlanId: 'plan-001',
    dueDate: new Date('2026-02-23T17:00:00Z')
  },
  {
    id: 'action-002',
    type: 'DecisionNeeded',
    priority: 'medium',
    createdAt: new Date('2026-02-20T14:00:00Z'),
    title: 'Choose launch date',
    description: 'Select preferred launch date from proposed options',
    context: 'Three launch dates have been proposed based on market analysis.'
  }
];
```

---

## Migration Notes (Bronze → Silver)

When migrating to Silver tier with real API:

1. **Keep all type definitions** - They are API-ready
2. **Replace mock data functions** with real API calls:
   ```typescript
   // Bronze: src/data/mock/plans.ts
   export async function getPlans(): Promise<Plan[]> {
     await delay(100);
     return MOCK_PLANS;
   }

   // Silver: src/data/api/plans.ts
   export async function getPlans(): Promise<Plan[]> {
     const response = await fetch('/api/plans');
     if (!response.ok) throw new Error('Failed to fetch');
     return response.json();
   }
   ```
3. **Update import paths** in components
4. **Add error handling** for network failures
5. **Add loading states** for async operations

---

## Next Steps

1. ✅ Data model complete
2. ➡️ Create API contracts in `contracts/` directory
3. ➡️ Write `quickstart.md` developer guide
4. ➡️ Update agent context with technology stack
