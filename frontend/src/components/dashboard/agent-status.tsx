'use client';

import { useSystemState } from '@/hooks/use-system-state';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AgentStatusSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { Cpu, Loader2, CheckCircle2, AlertTriangle, WifiOff } from 'lucide-react';
import type { AgentStatus } from '@/types/system-state';

interface AgentStatusProps {
  className?: string;
}

const STATUS_CONFIG: Record<AgentStatus, { label: string; icon: React.ReactNode; color: string; bg: string; message: string }> = {
  'idle': {
    label: 'Idle',
    icon: <CheckCircle2 className="h-8 w-8" />,
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
    message: 'Ready for new tasks',
  },
  'processing': {
    label: 'Processing',
    icon: <Loader2 className="h-8 w-8 animate-spin" />,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    message: 'Analyzing tasks...',
  },
  'working': {
    label: 'Working',
    icon: <Cpu className="h-8 w-8" />,
    color: 'text-purple-600 dark:text-purple-400',
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    message: 'Executing tasks...',
  },
  'error': {
    label: 'Error',
    icon: <AlertTriangle className="h-8 w-8" />,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
    message: 'Action required',
  },
};

export function AgentStatus({ className }: AgentStatusProps) {
  const { state, isLoading, error, isStale } = useSystemState();

  if (isLoading) {
    return (
      <Card className={cn('overflow-hidden', className)}>
        <AgentStatusSkeleton />
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn('overflow-hidden border-destructive/50', className)}>
        <CardContent className="pt-6">
          <EmptyState
            icon={<WifiOff className="h-8 w-8 text-muted-foreground" />}
            title="Connection Issue"
            description="Unable to fetch agent status"
          />
        </CardContent>
      </Card>
    );
  }

  if (!state) {
    return null;
  }

  const config = STATUS_CONFIG[state.status];

  return (
    <Card className={cn('overflow-hidden transition-all duration-300', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <Cpu className="h-4 w-4 text-primary" />
            Agent Status
          </CardTitle>
          {isStale && (
            <Badge variant="outline" className="text-xs">
              Updating...
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <motion.div
          className="flex items-center gap-4"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          key={state.status}
        >
          <div className={cn('p-3 rounded-xl', config.bg, config.color)}>
            {config.icon}
          </div>
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <Badge
                variant="outline"
                className={cn('border-0 text-white', config.bg, config.color)}
              >
                {config.label}
              </Badge>
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                Auto-refreshing
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{config.message}</p>
            <p className="text-xs text-muted-foreground mt-1">
              Last activity: {new Date(state.lastActivityAt).toLocaleString()}
            </p>
          </div>
        </motion.div>
      </CardContent>
    </Card>
  );
}
