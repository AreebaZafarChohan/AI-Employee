/**
 * Tasks Hook
 * TanStack Query hook for task CRUD operations
 */

'use client';

import {
  useQuery,
  useMutation,
  useQueryClient,
  UseMutationResult,
} from '@tanstack/react-query';
import { apiGet, apiPost, apiPatch } from '@/lib/api-client';
import type { Task, CreateTaskInput, UpdateTaskInput } from '@/types/task';
import type { ApiError } from '@/types/api';
import { parseApiError } from './use-api-client';

/**
 * Hook for managing tasks
 */
export function useTasks() {
  const queryClient = useQueryClient();

  // Fetch all tasks
  const {
    data: tasks = [],
    isLoading,
    error,
    refetch,
  } = useQuery<Task[], ApiError>({
    queryKey: ['tasks'],
    queryFn: () => apiGet<Task[]>('/tasks'),
  });

  // Create task mutation
  const createTaskMutation = useMutation<Task, ApiError, CreateTaskInput>({
    mutationFn: (input) => apiPost<Task>('/tasks', input),
    onSuccess: () => {
      // Invalidate and refetch tasks
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  // Update task mutation with optimistic updates
  const updateTaskMutation = useMutation<Task, ApiError, { id: string; input: UpdateTaskInput }>({
    mutationFn: ({ id, input }) => apiPatch<Task>(`/tasks/${id}`, input),
    onMutate: async ({ id, input }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['tasks'] });

      // Snapshot the previous value
      const previousTasks = queryClient.getQueryData<Task[]>(['tasks']);

      // Optimistically update the task
      if (previousTasks) {
        const updatedTasks = previousTasks.map((task) =>
          task.id === id ? { ...task, ...input, updatedAt: new Date().toISOString() } : task
        );
        queryClient.setQueryData(['tasks'], updatedTasks);
      }

      return { previousTasks };
    },
    onError: (err, variables, context) => {
      // Rollback to previous value on error
      if (context && typeof context === 'object' && 'previousTasks' in context && context.previousTasks) {
        queryClient.setQueryData(['tasks'], context.previousTasks);
      }
    },
    onSettled: () => {
      // Always refetch to ensure consistency
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });

  return {
    tasks,
    isLoading,
    error,
    createTask: createTaskMutation.mutateAsync,
    updateTask: updateTaskMutation.mutateAsync,
    refetch,
    isCreating: createTaskMutation.isPending,
    isUpdating: updateTaskMutation.isPending,
    createError: createTaskMutation.error,
    updateError: updateTaskMutation.error,
  };
}

/**
 * Hook for creating a task (standalone)
 */
export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation<Task, ApiError, CreateTaskInput>({
    mutationFn: (input) => apiPost<Task>('/tasks', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}

/**
 * Hook for updating a task (standalone)
 */
export function useUpdateTask() {
  const queryClient = useQueryClient();

  return useMutation<Task, ApiError, { id: string; input: UpdateTaskInput }>({
    mutationFn: ({ id, input }) => apiPatch<Task>(`/tasks/${id}`, input),
    onMutate: async ({ id, input }) => {
      await queryClient.cancelQueries({ queryKey: ['tasks'] });
      const previousTasks = queryClient.getQueryData<Task[]>(['tasks']);

      if (previousTasks) {
        const updatedTasks = previousTasks.map((task) =>
          task.id === id ? { ...task, ...input, updatedAt: new Date().toISOString() } : task
        );
        queryClient.setQueryData(['tasks'], updatedTasks);
      }

      return { previousTasks };
    },
    onError: (err, variables, context) => {
      if (context && typeof context === 'object' && 'previousTasks' in context && context.previousTasks) {
        queryClient.setQueryData(['tasks'], context.previousTasks);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
