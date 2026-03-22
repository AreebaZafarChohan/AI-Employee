'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useTimeline, type TimelineEntry } from '@/hooks/use-intelligence';
import { cn } from '@/lib/utils';

const statusColors: Record<string, string> = {
  running: 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
};

export function ExecutionTimeline() {
  const { data, isLoading } = useTimeline();

  const { agents, timeRange } = useMemo(() => {
    if (!data || data.length === 0) return { agents: [], timeRange: { min: 0, max: 1 } };

    const agentSet = new Set<string>();
    let min = Infinity;
    let max = -Infinity;

    data.forEach((entry: TimelineEntry) => {
      agentSet.add(entry.agent);
      const s = new Date(entry.start).getTime();
      const e = new Date(entry.end).getTime();
      if (s < min) min = s;
      if (e > max) max = e;
    });

    return {
      agents: Array.from(agentSet).sort(),
      timeRange: { min, max: max === min ? max + 1 : max },
    };
  }, [data]);

  if (isLoading) return <Skeleton className="h-48 w-full rounded-xl" />;

  if (!data || data.length === 0) {
    return (
      <Card className="border-white/10 bg-background/50 backdrop-blur-md">
        <CardHeader><CardTitle>Execution Timeline</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">No execution data.</p>
        </CardContent>
      </Card>
    );
  }

  const range = timeRange.max - timeRange.min;

  return (
    <Card className="border-white/10 bg-background/50 backdrop-blur-md">
      <CardHeader><CardTitle>Execution Timeline</CardTitle></CardHeader>
      <CardContent>
        <div className="space-y-3">
          {agents.map((agent) => {
            const entries = data.filter((e: TimelineEntry) => e.agent === agent);
            return (
              <div key={agent} className="flex items-center gap-3">
                <span className="text-xs font-medium w-24 truncate">{agent}</span>
                <div className="flex-1 relative h-6 bg-muted/30 rounded">
                  {entries.map((entry: TimelineEntry) => {
                    const start = new Date(entry.start).getTime();
                    const end = new Date(entry.end).getTime();
                    const left = ((start - timeRange.min) / range) * 100;
                    const width = Math.max(((end - start) / range) * 100, 1);

                    return (
                      <div
                        key={entry.id}
                        className={cn('absolute top-0.5 bottom-0.5 rounded-sm', statusColors[entry.status])}
                        style={{ left: `${left}%`, width: `${width}%` }}
                        title={`${entry.task} (${entry.status})`}
                      />
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
