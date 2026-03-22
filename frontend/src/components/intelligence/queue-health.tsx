'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { useQueueHealth, type QueueInfo } from '@/hooks/use-intelligence';
import { cn } from '@/lib/utils';

const statusColors: Record<string, string> = {
  healthy: 'bg-green-500',
  warning: 'bg-yellow-500',
  critical: 'bg-red-500',
};

const statusTextColors: Record<string, string> = {
  healthy: 'text-green-500',
  warning: 'text-yellow-500',
  critical: 'text-red-500',
};

export function QueueHealth() {
  const { data, isLoading } = useQueueHealth();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-xl" />
        ))}
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card className="border-white/10 bg-background/50 backdrop-blur-md">
        <CardHeader><CardTitle>Queue Health</CardTitle></CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground text-center py-8">No queues to monitor.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold">Queue Health</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((queue: QueueInfo) => (
          <Card key={queue.name} className="border-white/10 bg-background/50 backdrop-blur-md">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <span className="font-medium text-sm">{queue.name}</span>
                <span className={cn('flex items-center gap-1.5 text-xs font-medium capitalize', statusTextColors[queue.status])}>
                  <span className={cn('h-2 w-2 rounded-full', statusColors[queue.status])} />
                  {queue.status}
                </span>
              </div>
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Depth: {queue.depth}</span>
                <span>{queue.rate.toFixed(1)} items/min</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
