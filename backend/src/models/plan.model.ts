/**
 * Plan Model Type Definitions
 * TypeScript types for Plan and PlanStep entities
 */

import { Plan, PlanStatus, PlanStep } from '@prisma/client';

export type { Plan, PlanStatus, PlanStep };

export interface PlanStepCreateInput {
  order: number;
  title: string;
  description: string;
  estimatedDuration?: number | null;
  completed?: boolean;
}

export interface PlanCreateInput {
  taskId: string;
  steps: PlanStepCreateInput[];
}

export interface PlanWithSteps extends Plan {
  steps: PlanStep[];
  taskTitle?: string;
}

export interface PlanUpdateInput {
  status?: PlanStatus;
}
