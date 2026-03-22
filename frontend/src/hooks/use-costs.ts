'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api-client';

export type CostPeriod = 'day' | 'week' | 'month';

export interface CostSummary {
  totalCost: number;
  totalTokens: number;
  totalRequests: number;
  breakdown: {
    byAgent: { name: string; cost: number; tokens: number; requests: number }[];
    byModel: { name: string; cost: number; tokens: number; requests: number }[];
  };
}

export interface CostTimeseriesPoint {
  date: string;
  cost: number;
  tokens: number;
  requests: number;
}

export function useCostSummary(period: CostPeriod) {
  return useQuery({
    queryKey: ['costs', 'summary', period],
    queryFn: () => apiGet<CostSummary>(`/api/costs/summary?period=${period}`),
  });
}

export function useCostTimeseries(period: CostPeriod, from?: string, to?: string) {
  const params = new URLSearchParams({ period });
  if (from) params.set('from', from);
  if (to) params.set('to', to);

  return useQuery({
    queryKey: ['costs', 'timeseries', period, from, to],
    queryFn: () => apiGet<CostTimeseriesPoint[]>(`/api/costs/timeseries?${params.toString()}`),
  });
}
