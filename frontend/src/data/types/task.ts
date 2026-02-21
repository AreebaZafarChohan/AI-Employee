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
