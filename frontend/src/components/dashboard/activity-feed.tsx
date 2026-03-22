'use client';

import { useActivityLog } from '@/hooks/use-activity-log';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ActivityFeedSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import { cn, formatRelativeTime } from '@/lib/utils';
import {
  FilePlus2,
  CheckSquare2,
  FileText,
  Power,
  AlertTriangle,
  Clock,
  MessageCircle,
  Mail,
  AlertCircle,
} from 'lucide-react';
import type { ActivityEventType } from '@/types/activity';

interface ActivityFeedProps {
  className?: string;
}

const EVENT_CONFIG: Record<ActivityEventType, { label: string; icon: React.ReactNode; color: string }> = {
  'task_created': {
    label: 'Task Created',
    icon: <FilePlus2 className="h-4 w-4" />,
    color: 'text-blue-600 dark:text-blue-400',
  },
  'task_updated': {
    label: 'Task Updated',
    icon: <CheckSquare2 className="h-4 w-4" />,
    color: 'text-green-600 dark:text-green-400',
  },
  'plan_generated': {
    label: 'Plan Generated',
    icon: <FileText className="h-4 w-4" />,
    color: 'text-purple-600 dark:text-purple-400',
  },
  'system_started': {
    label: 'System Started',
    icon: <Power className="h-4 w-4" />,
    color: 'text-green-600 dark:text-green-400',
  },
  'system_error': {
    label: 'System Error',
    icon: <AlertTriangle className="h-4 w-4" />,
    color: 'text-red-600 dark:text-red-400',
  },
  'whatsapp_message_sent': {
    label: 'WhatsApp Sent',
    icon: <MessageCircle className="h-4 w-4" />,
    color: 'text-emerald-600 dark:text-emerald-400',
  },
  'whatsapp_message_received': {
    label: 'WhatsApp Received',
    icon: <MessageCircle className="h-4 w-4" />,
    color: 'text-teal-600 dark:text-teal-400',
  },
  'email_received': {
    label: 'Email Received',
    icon: <Mail className="h-4 w-4" />,
    color: 'text-orange-600 dark:text-orange-400',
  },
  'email_sent': {
    label: 'Email Sent',
    icon: <Mail className="h-4 w-4" />,
    color: 'text-yellow-600 dark:text-yellow-400',
  },
};

export function ActivityFeed({ className }: ActivityFeedProps) {
  const { logs, isLoading, error, hasMore } = useActivityLog({ limit: 20 });

  if (isLoading) {
    return (
      <Card className={cn('overflow-hidden', className)}>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Recent Activity</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <ActivityFeedSkeleton />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={cn('overflow-hidden', className)}>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Recent Activity</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={AlertCircle}
            title="Failed to load activity"
            description={error.message}
          />
        </CardContent>
      </Card>
    );
  }

  if (logs.length === 0) {
    return (
      <Card className={cn('overflow-hidden', className)}>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            <CardTitle className="text-base">Recent Activity</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <EmptyState
            icon={Clock}
            title="No activity yet"
            description="System activity will appear here"
          />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-primary" />
          <CardTitle className="text-base">Recent Activity</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-3">
            {logs.map((log) => {
              const config = EVENT_CONFIG[log.eventType];
              
              return (
                <div key={log.id} className="flex items-start gap-3">
                  <div className={cn('p-2 rounded-full bg-muted', config.color)}>
                    {config.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium">{config.label}</span>
                      <Badge variant="outline" className="text-xs">
                        {formatRelativeTime(new Date(log.timestamp))}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {log.message}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {hasMore && (
            <div className="pt-2 border-t">
              <p className="text-sm text-muted-foreground text-center py-2">
                There are more activities available
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
