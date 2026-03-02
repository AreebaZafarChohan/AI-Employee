/**
 * Watcher Orchestrator Component
 * 24/7 monitoring and control panel
 */

'use client';

import { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useWatcherStore } from '@/store/watcher-store';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Play,
  Pause,
  StopCircle,
  RotateCcw,
  Activity,
  Clock,
  Zap,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';

interface WatcherOrchestratorProps {
  className?: string;
}

export function WatcherOrchestrator({ className }: WatcherOrchestratorProps) {
  const {
    status,
    lastSync,
    queueSize,
    processingSpeed,
    uptime,
    services,
    startWatcher,
    stopWatcher,
    pauseWatcher,
    restartWatcher,
    fetchWatcherStatus,
  } = useWatcherStore();

  // Poll for status updates every 5 seconds
  useEffect(() => {
    fetchWatcherStatus();
    const interval = setInterval(fetchWatcherStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchWatcherStatus]);

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatLastSync = (timestamp: string | null) => {
    if (!timestamp) return 'Never';
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const getStatusColor = () => {
    switch (status) {
      case 'running':
        return 'text-green-600 bg-green-100 dark:bg-green-900/30';
      case 'paused':
        return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
      case 'stopped':
        return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30';
      case 'error':
        return 'text-red-600 bg-red-100 dark:bg-red-900/30';
    }
  };

  const getServiceStatusColor = (serviceStatus: string) => {
    switch (serviceStatus) {
      case 'active':
        return 'text-green-600';
      case 'inactive':
        return 'text-gray-400';
      case 'error':
        return 'text-red-600';
    }
  };

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-lg', getStatusColor())}>
              <Activity className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg">Watcher Orchestrator</CardTitle>
              <p className="text-sm text-muted-foreground">24/7 Service Monitoring</p>
            </div>
          </div>
          <Badge
            variant="outline"
            className={cn('flex items-center gap-1 px-3 py-1', getStatusColor())}
          >
            <span className="relative flex h-2 w-2">
              {status === 'running' && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75" />
              )}
              <span
                className={cn(
                  'relative inline-flex rounded-full h-2 w-2',
                  status === 'running' ? 'bg-green-500' : 'bg-current'
                )}
              />
            </span>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Stats Grid */}
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Clock className="h-4 w-4" />
              <span>Uptime</span>
            </div>
            <p className="text-lg font-semibold">{formatUptime(uptime)}</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Zap className="h-4 w-4" />
              <span>Speed</span>
            </div>
            <p className="text-lg font-semibold">{processingSpeed}/min</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <CheckCircle2 className="h-4 w-4" />
              <span>Queue</span>
            </div>
            <p className="text-lg font-semibold">{queueSize}</p>
          </div>
        </div>

        {/* Services Status */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Services</p>
          <div className="grid grid-cols-2 gap-2">
            {services.map((service) => (
              <div
                key={service.name}
                className="flex items-center justify-between p-2 rounded-md bg-muted/50"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={cn('h-2 w-2 rounded-full', getServiceStatusColor(service.status))}
                  />
                  <span className="text-sm">{service.name}</span>
                </div>
                <span className="text-xs text-muted-foreground">{service.itemsProcessed}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Last Sync */}
        <div className="flex items-center justify-between text-xs text-muted-foreground pt-2 border-t">
          <span>Last sync: {formatLastSync(lastSync)}</span>
          <span>Auto-refresh: 5s</span>
        </div>

        {/* Control Buttons */}
        <div className="flex gap-2 pt-2 border-t">
          <Button
            size="sm"
            variant={status === 'running' ? 'secondary' : 'default'}
            onClick={startWatcher}
            disabled={status === 'running'}
            className="flex-1"
          >
            <Play className="h-4 w-4 mr-1" />
            Start
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={pauseWatcher}
            disabled={status !== 'running'}
            className="flex-1"
          >
            <Pause className="h-4 w-4 mr-1" />
            Pause
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={restartWatcher}
            className="flex-1"
          >
            <RotateCcw className="h-4 w-4 mr-1" />
            Restart
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={stopWatcher}
            disabled={status === 'stopped'}
            className="flex-1"
          >
            <StopCircle className="h-4 w-4 mr-1" />
            Stop
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
