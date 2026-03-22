'use client';

import { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useCostTimeseries, type CostPeriod } from '@/hooks/use-costs';
import { cn } from '@/lib/utils';

const PERIODS: CostPeriod[] = ['day', 'week', 'month'];

export function CostChart() {
  const [period, setPeriod] = useState<CostPeriod>('week');
  const { data, isLoading } = useCostTimeseries(period);

  return (
    <Card className="border-white/10 bg-background/50 backdrop-blur-md">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Cost Over Time</CardTitle>
        <div className="flex gap-1 rounded-lg bg-muted p-1">
          {PERIODS.map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={cn(
                'px-3 py-1 text-xs font-medium rounded-md transition-colors capitalize',
                period === p
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              {p}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[300px] w-full rounded-xl" />
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={data ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis dataKey="date" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis yAxisId="cost" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <YAxis yAxisId="tokens" orientation="right" tick={{ fontSize: 12 }} stroke="hsl(var(--muted-foreground))" />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'hsl(var(--popover))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Line yAxisId="cost" type="monotone" dataKey="cost" stroke="#22c55e" strokeWidth={2} dot={false} name="Cost ($)" />
              <Line yAxisId="tokens" type="monotone" dataKey="tokens" stroke="#3b82f6" strokeWidth={2} dot={false} name="Tokens" />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
