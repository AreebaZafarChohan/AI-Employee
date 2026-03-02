'use client';

import { Badge } from '@/components/ui/badge';
import type { RiskLevel } from '@/types/vault';

const riskConfig: Record<RiskLevel, { label: string; className: string }> = {
  low: {
    label: 'Low',
    className: 'bg-green-500/20 text-green-400 border-green-500/30',
  },
  medium: {
    label: 'Medium',
    className: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  },
  high: {
    label: 'High',
    className: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  },
  critical: {
    label: 'Critical',
    className: 'bg-red-500/20 text-red-400 border-red-500/30',
  },
};

interface RiskBadgeProps {
  level: RiskLevel;
}

export function RiskBadge({ level }: RiskBadgeProps) {
  const config = riskConfig[level] ?? riskConfig.low;
  return (
    <Badge variant="outline" className={config.className}>
      {config.label}
    </Badge>
  );
}
