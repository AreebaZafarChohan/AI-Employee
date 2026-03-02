'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Activity, Wifi, WifiOff } from 'lucide-react';
import { useSystemHealth } from '@/hooks/use-vault';
import { formatRelativeTime } from '@/lib/utils';
import type { WatcherStatus as WatcherStatusType } from '@/types/vault';

export function WatcherStatusPanel() {
  const { data: health, isLoading, isError } = useSystemHealth();

  if (isLoading) {
    return (
      <Card className="glass">
        <CardHeader><CardTitle>Watcher Status</CardTitle></CardHeader>
        <CardContent className="space-y-3">
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
          <Skeleton className="h-6 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !health) {
    return (
      <Card className="glass border-red-500/30">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <WifiOff className="h-5 w-5 text-red-400" />
            Watcher Status
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">Unable to reach backend.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          Watcher Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main status */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">System</span>
          <div className="flex items-center gap-2">
            <div className={`h-2.5 w-2.5 rounded-full ${health.watcher_running ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
            <span className={`text-sm font-medium ${health.watcher_running ? 'text-green-400' : 'text-red-400'}`}>
              {health.watcher_running ? 'Running' : 'Stopped'}
            </span>
          </div>
        </div>

        {/* Individual watchers */}
        {health.watchers && Object.entries(health.watchers).map(([name, watcher]) => (
          <WatcherRow key={name} name={name} watcher={watcher as WatcherStatusType} />
        ))}

        {/* Meta */}
        <div className="pt-2 border-t border-white/10 space-y-1 text-xs text-muted-foreground">
          {health.last_scan_time && (
            <div className="flex justify-between">
              <span>Last Scan</span>
              <span>{formatRelativeTime(new Date(health.last_scan_time))}</span>
            </div>
          )}
          {health.last_action && (
            <div className="flex justify-between">
              <span>Last Action</span>
              <span className="truncate ml-4 max-w-[200px]">{health.last_action}</span>
            </div>
          )}
          <div className="flex justify-between">
            <span>Queue Size</span>
            <span>{health.queue_size}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function WatcherRow({ name, watcher }: { name: string; watcher: WatcherStatusType }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex items-center justify-between"
    >
      <span className="text-sm capitalize text-muted-foreground">{name}</span>
      <div className="flex items-center gap-2">
        {watcher.running ? (
          <Wifi className="h-3.5 w-3.5 text-green-400" />
        ) : (
          <WifiOff className="h-3.5 w-3.5 text-red-400" />
        )}
        <span className={`text-xs ${watcher.running ? 'text-green-400' : 'text-red-400'}`}>
          {watcher.running ? 'Active' : 'Off'}
        </span>
        {watcher.items_processed > 0 && (
          <span className="text-xs text-muted-foreground">({watcher.items_processed})</span>
        )}
      </div>
    </motion.div>
  );
}
