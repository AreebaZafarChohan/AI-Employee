'use client';

import { Badge } from '@/components/ui/badge';
import type { VaultStatus } from '@/types/vault';

const statusConfig: Record<VaultStatus, { label: string; className: string }> = {
  pending: {
    label: 'Pending',
    className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  },
  approved: {
    label: 'Approved',
    className: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  rejected: {
    label: 'Rejected',
    className: 'bg-red-500/20 text-red-400 border-red-500/30',
  },
  done: {
    label: 'Done',
    className: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  },
  needs_action: {
    label: 'Needs Action',
    className: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  },
};

interface StatusBadgeProps {
  status: VaultStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const config = statusConfig[status] ?? statusConfig.pending;
  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  );
}
