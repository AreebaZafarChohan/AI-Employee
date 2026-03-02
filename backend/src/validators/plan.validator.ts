/**
 * Plan Validators
 * Zod schemas for plan request validation
 */

import { z } from 'zod';

export const PlanStepSchema = z.object({
  title: z
    .string()
    .min(1, 'Step title is required')
    .max(200, 'Step title must be less than 200 characters'),
  description: z.string().min(1, 'Step description is required'),
  estimatedDuration: z.number().int().positive().nullable().optional(),
});

export const PlanCreateSchema = z.object({
  taskId: z.string().uuid('Invalid task ID format'),
  steps: z.array(PlanStepSchema).min(1, 'Plan must have at least one step'),
});

export const PlanStatusUpdateSchema = z.object({
  status: z.enum(['Draft', 'Active', 'Completed', 'Archived'] as const, {
    errorMap: () => ({ message: 'Status must be Draft, Active, Completed, or Archived' }),
  }),
});

export const PlanQuerySchema = z.object({
  status: z.enum(['Draft', 'Active', 'Completed', 'Archived'] as const).optional(),
  page: z.string().transform(Number).default('1'),
  pageSize: z.string().transform(Number).default('20'),
});

export type PlanStepInput = z.infer<typeof PlanStepSchema>;
export type PlanCreateInput = z.infer<typeof PlanCreateSchema>;
export type PlanStatusUpdateInput = z.infer<typeof PlanStatusUpdateSchema>;
