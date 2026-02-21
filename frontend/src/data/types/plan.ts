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
