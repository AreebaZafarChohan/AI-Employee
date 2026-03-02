/**
 * System State Hook
 * TanStack Query hook for agent status with auto-polling
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api-client';
import type { SystemState } from '@/types/system-state';
import type { ApiError } from '@/types/api';

/**
 * Hook for monitoring AI agent status
 * Auto-refreshes every 30 seconds per NFR-001
 */
export function useSystemState() {
  const {
    data: state,
    isLoading,
    error,
    isStale,
    refetch,
  } = useQuery<SystemState, ApiError>({
    queryKey: ['systemState'],
    queryFn: () => apiGet<SystemState>('/system/state'),
    refetchInterval: 30000, // 30 seconds auto-refresh
    refetchIntervalInBackground: true, // Continue polling when tab is inactive
  });

  return {
    state,
    isLoading,
    error,
    isStale,
    refetch,
  };
}
