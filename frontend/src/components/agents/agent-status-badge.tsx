'use client';

import { Badge } from '@/components/ui/badge';

interface AgentStatusBadgeProps {
  status: 'running' | 'stopped' | 'error';
}

const statusConfig = {
  running: { label: 'Running', className: 'bg-green-500/15 text-green-600 border-green-500/30' },
  stopped: { label: 'Stopped', className: 'bg-gray-500/15 text-gray-500 border-gray-500/30' },
  error: { label: 'Error', className: 'bg-red-500/15 text-red-600 border-red-500/30' },
} as const;

export function AgentStatusBadge({ status }: AgentStatusBadgeProps) {
  const config = statusConfig[status];
  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  );
}
