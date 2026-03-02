/**
 * Plans Hook
 * TanStack Query hook for AI plan generation
 */

'use client';

import { useMutation } from '@tanstack/react-query';
import { apiPost } from '@/lib/api-client';
import type { Plan, GeneratePlanInput, PlanGenerationStatus } from '@/types/plan';
import type { ApiError } from '@/types/api';

/**
 * Hook for generating AI plans
 */
export function usePlans() {
  const {
    mutateAsync: generatePlan,
    isPending: isGenerating,
    error,
  } = useMutation<Plan | PlanGenerationStatus, ApiError, GeneratePlanInput>({
    mutationFn: (input) => apiPost<Plan | PlanGenerationStatus>('/plans', input),
  });

  return {
    generatePlan,
    isGenerating,
    error,
  };
}
