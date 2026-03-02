/**
 * Activity Log Model Type Definitions
 * TypeScript types for ActivityLog entity
 */

import { ActivityLog } from '@prisma/client';

export type { ActivityLog };

export interface ActivityLogCreateInput {
  type: string;
  description: string;
  metadata?: Record<string, unknown>;
}

export interface ActivityLogQuery {
  type?: string;
  startTime?: Date;
  endTime?: Date;
  page?: number;
  pageSize?: number;
}

// Activity type constants
export const ActivityTypes = {
  TASK_CREATED: 'task.created',
  TASK_UPDATED: 'task.updated',
  TASK_DELETED: 'task.deleted',
  PLAN_GENERATED: 'plan.generated',
  PLAN_UPDATED: 'plan.updated',
  PLAN_DELETED: 'plan.deleted',
  AI_INVOKED: 'ai.invoked',
  AI_COMPLETED: 'ai.completed',
  AI_FAILED: 'ai.failed',
  STATE_CHANGED: 'state.changed',
  ERROR_OCCURRED: 'error.occurred',
  WHATSAPP_SENT: 'whatsapp.sent',
  WHATSAPP_RECEIVED: 'whatsapp.received',
  EMAIL_RECEIVED: 'email.received',
  EMAIL_SENT: 'email.sent',
} as const;

export type ActivityType = (typeof ActivityTypes)[keyof typeof ActivityTypes];
