/**
 * Task Types
 * Type definitions for task entities
 */

/**
 * Task status values
 */
export type TaskStatus = 'pending' | 'in-progress' | 'completed' | 'cancelled';

/**
 * Task priority levels
 */
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

/**
 * Task entity
 */
export interface Task {
  id: string;              // UUID v4
  title: string;           // 1-200 characters
  description?: string;    // 0-2000 characters
  status: TaskStatus;
  priority?: TaskPriority;
  createdAt: string;       // ISO-8601 datetime
  updatedAt: string;       // ISO-8601 datetime
  dueDate?: string;        // ISO-8601 datetime
  completedAt?: string;    // ISO-8601 datetime
  tags?: string[];
  assignee?: string;
  metadata?: Record<string, unknown>;
  // Legacy fields for compatibility
  created_at?: string;
  updated_at?: string;
  due_date?: string;
  completed_at?: string;
}

/**
 * Input for creating a new task
 */
export interface CreateTaskInput {
  title: string;
  description?: string;    // Optional
}

/**
 * Input for updating a task
 */
export interface UpdateTaskInput {
  status?: TaskStatus;
  title?: string;
  description?: string;
}
