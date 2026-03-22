'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useHeatmap, type HeatmapCell } from '@/hooks/use-intelligence';

export function ActivityHeatmap() {
  const { data, isLoading } = useHeatmap();

  const { agents, hours, cellMap } = useMemo(() => {
    if (!data || data.length === 0) return { agents: [], hours: [], cellMap: new Map<string, number>() };

    const agentSet = new Set<string>();
    const hourSet = new Set<number>();
    const map = new Map<string, number>();

    data.forEach((cell: HeatmapCell) => {
      agentSet.add(cell.agent);
      hourSet.add(cell.hour);
      map.set(`${cell.agent}-${cell.hour}`, cell.intensity);
    });

    return {
      agents: Array.from(agentSet).sort(),
      hours: Array.from(hourSet).sort((a, b) => a - b),
      cellMap: map,
    };
  }, [data]);

  if (isLoading) return <Skeleton className="h-64 w-full rounded-xl" />;

  if (agents.length === 0) {
    return (
      <Card className="border-white/10 bg-background/50 backdrop-blur-md">
        <CardHeader><CardTitle>Activity Heatmap</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">No activity data yet.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-white/10 bg-background/50 backdrop-blur-md">
      <CardHeader><CardTitle>Activity Heatmap</CardTitle></CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <div
            className="grid gap-1"
            style={{
              gridTemplateColumns: `120px repeat(${hours.length}, 1fr)`,
            }}
          >
            {/* Header row */}
            <div className="text-xs text-muted-foreground" />
            {hours.map((h) => (
              <div key={h} className="text-xs text-center text-muted-foreground">
                {h}:00
              </div>
            ))}

            {/* Agent rows */}
            {agents.map((agent) => (
              <div key={agent} className="contents">
                <div className="text-xs font-medium truncate pr-2 flex items-center">
                  {agent}
                </div>
                {hours.map((h) => {
                  const intensity = cellMap.get(`${agent}-${h}`) ?? 0;
                  return (
                    <div
                      key={`${agent}-${h}`}
                      className="rounded-sm h-6 transition-colors"
                      style={{
                        backgroundColor: `hsl(142 76% 36% / ${intensity})`,
                      }}
                      title={`${agent} at ${h}:00 — ${(intensity * 100).toFixed(0)}%`}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
