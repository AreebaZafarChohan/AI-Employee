/**
 * Task Validators
 * Zod schemas for task request validation
 */

import { z } from 'zod';

export const TaskCreateSchema = z.object({
  title: z
    .string()
    .min(1, 'Title is required')
    .max(200, 'Title must be less than 200 characters'),
  description: z
    .string()
    .max(1000, 'Description must be less than 1000 characters')
    .optional()
    .nullable()
    .transform((val) => (val === '' ? null : val)),
});

export const TaskUpdateSchema = z.object({
  title: z
    .string()
    .min(1, 'Title cannot be empty')
    .max(200, 'Title must be less than 200 characters')
    .optional(),
  description: z
    .string()
    .max(1000, 'Description must be less than 1000 characters')
    .optional()
    .nullable()
    .transform((val) => (val === '' ? null : val)),
});

export const TaskStatusUpdateSchema = z.object({
  status: z.enum(['Pending', 'In Progress', 'Done'] as const, {
    errorMap: () => ({ message: 'Status must be Pending, In Progress, or Done' }),
  }),
});

export const TaskQuerySchema = z.object({
  status: z.enum(['Pending', 'In Progress', 'Done'] as const).optional(),
  page: z.string().transform(Number).default('1'),
  pageSize: z.string().transform(Number).default('20'),
});

export type TaskCreateInput = z.infer<typeof TaskCreateSchema>;
export type TaskUpdateInput = z.infer<typeof TaskUpdateSchema>;
export type TaskStatusUpdateInput = z.infer<typeof TaskStatusUpdateSchema>;
