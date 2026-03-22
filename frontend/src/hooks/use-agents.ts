'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useEffect, useCallback } from 'react';
import { apiGet, apiPost } from '@/lib/api-client';
import { useWebSocket } from '@/hooks/use-websocket';

export interface Agent {
  id: string;
  name: string;
  type: string;
  status: 'running' | 'stopped' | 'error';
  errorMessage?: string;
}

export function useAgents() {
  const queryClient = useQueryClient();
  const { subscribe, unsubscribe } = useWebSocket();

  const query = useQuery<Agent[]>({
    queryKey: ['agents'],
    queryFn: () => apiGet<Agent[]>('/api/agents'),
  });

  const handleStatusChange = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['agents'] });
  }, [queryClient]);

  useEffect(() => {
    subscribe('agent:status', handleStatusChange);
    return () => unsubscribe('agent:status', handleStatusChange);
  }, [subscribe, unsubscribe, handleStatusChange]);

  return query;
}

export function useStartAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiPost(`/api/agents/${id}/start`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}

export function useStopAgent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiPost(`/api/agents/${id}/stop`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
