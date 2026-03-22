'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/lib/api-client';

export interface GoalTask {
  id: string;
  title: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
}

export interface Goal {
  id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'Draft' | 'Active' | 'Completed' | 'Cancelled';
  progress: number;
  tasks: GoalTask[];
  createdAt?: string;
  updatedAt?: string;
}

export type CreateGoalInput = Pick<Goal, 'title' | 'description' | 'priority'>;
export type UpdateGoalInput = Partial<Pick<Goal, 'title' | 'description' | 'priority' | 'status'>>;

const GOALS_KEY = ['goals'];

export function useGoals() {
  return useQuery({
    queryKey: GOALS_KEY,
    queryFn: () => apiGet<Goal[]>('/api/goals'),
  });
}

export function useGoal(id: string) {
  return useQuery({
    queryKey: [...GOALS_KEY, id],
    queryFn: () => apiGet<Goal>(`/api/goals/${id}`),
    enabled: !!id,
  });
}

export function useCreateGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CreateGoalInput) => apiPost<Goal>('/api/goals', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GOALS_KEY });
    },
  });
}

export function useUpdateGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...data }: UpdateGoalInput & { id: string }) =>
      apiPatch<Goal>(`/api/goals/${id}`, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: GOALS_KEY });
      queryClient.invalidateQueries({ queryKey: [...GOALS_KEY, variables.id] });
    },
  });
}

export function useDeleteGoal() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiDelete<void>(`/api/goals/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GOALS_KEY });
    },
  });
}
