'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect, useCallback } from 'react';
import { apiGet } from '@/lib/api-client';
import { useWebSocket } from '@/hooks/use-websocket';

export type LogSeverity = 'All' | 'Info' | 'Warn' | 'Error';

export interface AgentLog {
  id: string;
  timestamp: string;
  severity: 'Info' | 'Warn' | 'Error';
  message: string;
}

interface AgentLogsResponse {
  logs: AgentLog[];
  total: number;
  page: number;
  pageSize: number;
}

export function useAgentLogs(agentId: string, initialSeverity: LogSeverity = 'All') {
  const queryClient = useQueryClient();
  const { subscribe, unsubscribe } = useWebSocket();
  const [severity, setSeverity] = useState<LogSeverity>(initialSeverity);
  const [page, setPage] = useState(1);
  const pageSize = 50;

  const severityParam = severity === 'All' ? '' : severity;
  const query = useQuery<AgentLogsResponse>({
    queryKey: ['agent-logs', agentId, severity, page],
    queryFn: () =>
      apiGet<AgentLogsResponse>(
        `/api/agents/${agentId}/logs?severity=${severityParam}&page=${page}&pageSize=${pageSize}`
      ),
    enabled: !!agentId,
  });

  const handleLogEvent = useCallback(
    (data: unknown) => {
      const event = data as { agentId?: string };
      if (event.agentId === agentId) {
        queryClient.invalidateQueries({ queryKey: ['agent-logs', agentId] });
      }
    },
    [agentId, queryClient]
  );

  useEffect(() => {
    subscribe('agent:log', handleLogEvent);
    return () => unsubscribe('agent:log', handleLogEvent);
  }, [subscribe, unsubscribe, handleLogEvent]);

  return {
    ...query,
    severity,
    setSeverity,
    page,
    setPage,
  };
}
