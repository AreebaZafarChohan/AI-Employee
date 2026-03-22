'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect } from 'react';
import { apiGet } from '@/lib/api-client';
import { useWebSocket } from '@/hooks/use-websocket';

export type ToolStatus = 'success' | 'failure' | 'pending';

export interface ToolInvocation {
  id: string;
  toolName: string;
  status: ToolStatus;
  agentName: string;
  duration?: number;
  timestamp: string;
  input: Record<string, unknown>;
  output?: unknown;
  error?: string;
}

export interface ToolInvocationPage {
  items: ToolInvocation[];
  total: number;
  page: number;
  pageSize: number;
}

export function useToolInvocations(page: number, pageSize: number) {
  const queryClient = useQueryClient();
  const { subscribe, unsubscribe } = useWebSocket();

  const query = useQuery({
    queryKey: ['tools', 'invocations', page, pageSize],
    queryFn: () =>
      apiGet<ToolInvocationPage>(`/api/tools/invocations?page=${page}&pageSize=${pageSize}`),
  });

  useEffect(() => {
    const handler = () => {
      queryClient.invalidateQueries({ queryKey: ['tools', 'invocations'] });
    };
    subscribe('tool:invocation', handler);
    return () => unsubscribe('tool:invocation', handler);
  }, [subscribe, unsubscribe, queryClient]);

  return query;
}

export function useToolInvocationDetail(id: string | null) {
  return useQuery({
    queryKey: ['tools', 'invocations', id],
    queryFn: () => apiGet<ToolInvocation>(`/api/tools/invocations/${id}`),
    enabled: !!id,
  });
}
