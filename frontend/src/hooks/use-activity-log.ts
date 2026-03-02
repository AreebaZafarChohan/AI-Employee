/**
 * Activity Log Hook
 * TanStack Query hook for activity feed
 */

'use client';

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import type { ActivityLog, ActivityLogQuery } from '@/types/activity';
import type { ApiError } from '@/types/api';

const DEFAULT_LIMIT = 50;

// Backend response shape
interface ActivityLogResponse {
  data: Array<{
    id: string;
    timestamp: string;
    type: string;
    description: string;
    metadata?: Record<string, unknown>;
  }>;
  meta: {
    total: number;
    page: number;
    pageSize: number;
  };
}

// Map backend dot-notation type to frontend underscore EventType
function mapEventType(type: string): ActivityLog['eventType'] {
  const mapping: Record<string, ActivityLog['eventType']> = {
    'task.created': 'task_created',
    'task.updated': 'task_updated',
    'task.deleted': 'task_updated',
    'plan.generated': 'plan_generated',
    'plan.updated': 'plan_generated',
    'plan.deleted': 'plan_generated',
    'state.changed': 'system_started',
    'error.occurred': 'system_error',
    'ai.invoked': 'plan_generated',
    'ai.completed': 'plan_generated',
    'ai.failed': 'system_error',
    'whatsapp.sent': 'whatsapp_message_sent',
    'whatsapp.received': 'whatsapp_message_received',
    'email.received': 'email_received',
    'email.sent': 'email_sent',
  };
  return mapping[type] ?? 'system_started';
}

/**
 * Hook for fetching activity logs
 */
export function useActivityLog(options: ActivityLogQuery = {}) {
  const { limit = DEFAULT_LIMIT, offset = 0 } = options;
  const page = Math.floor(offset / limit) + 1;

  const {
    data: logs = [],
    isLoading,
    error,
  } = useQuery<ActivityLog[], ApiError>({
    queryKey: ['activityLog', { limit, offset }],
    queryFn: async () => {
      const params = new URLSearchParams({
        pageSize: limit.toString(),
        page: page.toString(),
      });
      const response = await apiClient<ActivityLogResponse>(
        `/activity-logs?${params.toString()}`
      );
      return response.data.map((entry) => ({
        id: entry.id,
        timestamp: entry.timestamp,
        eventType: mapEventType(entry.type),
        message: entry.description,
        metadata: entry.metadata,
      }));
    },
  });

  return {
    logs,
    isLoading,
    error,
    hasMore: logs.length >= limit,
  };
}
