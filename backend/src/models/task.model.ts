/**
 * Task Model Type Definitions
 * TypeScript types for Task entity
 */

import { Task } from '@prisma/client';

export type TaskStatus = 'Pending' | 'InProgress' | 'Done' | 'Failed' | 'Skipped' | string;
export type { Task };

export interface TaskCreateInput {
  title: string;
  description?: string | null;
  status?: TaskStatus;
}

export interface TaskUpdateInput {
  title?: string;
  description?: string | null;
  status?: TaskStatus;
  completedAt?: Date | null;
}

export interface TaskStatusTransition {
  currentStatus: TaskStatus;
  newStatus: TaskStatus;
}

// Valid status transitions: Pending -> InProgress -> Done
export const VALID_STATUS_TRANSITIONS: Record<TaskStatus, TaskStatus[]> = {
  Pending: ['InProgress'],
  InProgress: ['Done'],
  Done: [],
};
