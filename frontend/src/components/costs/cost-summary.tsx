'use client';

import { StatsCard } from '@/components/dashboard/stats-card';
import { DollarSign, Hash, Activity } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import type { CostSummary } from '@/hooks/use-costs';

interface CostSummaryProps {
  data?: CostSummary;
  isLoading: boolean;
}

export function CostSummaryCards({ data, isLoading }: CostSummaryProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatsCard
        title="Total Cost"
        value={`$${(data?.totalCost ?? 0).toFixed(2)}`}
        icon={DollarSign}
        color="green"
      />
      <StatsCard
        title="Total Tokens"
        value={(data?.totalTokens ?? 0).toLocaleString()}
        icon={Hash}
        color="blue"
      />
      <StatsCard
        title="Total Requests"
        value={(data?.totalRequests ?? 0).toLocaleString()}
        icon={Activity}
        color="purple"
      />
    </div>
  );
}
