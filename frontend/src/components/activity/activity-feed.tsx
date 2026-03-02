/**
 * Activity Feed Component
 * Real-time activity timeline with animations
 */

'use client';

import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useActivityStore } from '@/store/activity-store';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  Mail,
  MessageSquare,
  Linkedin,
  FileText,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  CheckCheck,
} from 'lucide-react';

interface ActivityFeedProps {
  className?: string;
  limit?: number;
  showHeader?: boolean;
}

const SERVICE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  gmail: Mail,
  whatsapp: MessageSquare,
  linkedin: Linkedin,
  filesystem: FileText,
  system: Bell,
};

const SEVERITY_COLORS = {
  info: 'text-blue-600 bg-blue-100 dark:bg-blue-900/30',
  success: 'text-green-600 bg-green-100 dark:bg-green-900/30',
  warning: 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30',
  error: 'text-red-600 bg-red-100 dark:bg-red-900/30',
};

const TYPE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  email_received: Mail,
  email_sent: Mail,
  whatsapp_received: MessageSquare,
  whatsapp_sent: MessageSquare,
  linkedin_connection: Linkedin,
  linkedin_message: Linkedin,
  file_processed: FileText,
  approval_created: Clock,
  approval_approved: CheckCircle,
  approval_rejected: XCircle,
  task_completed: CheckCheck,
  error: AlertTriangle,
  system: Bell,
};

export function ActivityFeed({ className, limit = 50, showHeader = true }: ActivityFeedProps) {
  const { activities, unreadCount, isLoading, fetchActivities, markAllAsRead } = useActivityStore();
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchActivities();
    const interval = setInterval(fetchActivities, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [fetchActivities]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${days}d ago`;
  };

  const getIconForActivity = (activity: (typeof activities)[0]) => {
    const Icon = TYPE_ICONS[activity.type] || SERVICE_ICONS[activity.service] || Bell;
    return Icon;
  };

  return (
    <Card className={cn('overflow-hidden', className)}>
      {showHeader && (
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
                <Bell className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <CardTitle className="text-lg">Recent Activity</CardTitle>
                <p className="text-sm text-muted-foreground">
                  {unreadCount > 0 && (
                    <span className="text-purple-600 font-medium">{unreadCount} unread</span>
                  )}
                </p>
              </div>
            </div>
            {unreadCount > 0 && (
              <Button size="sm" variant="ghost" onClick={markAllAsRead}>
                Mark all read
              </Button>
            )}
          </div>
        </CardHeader>
      )}
      <CardContent>
        <div ref={containerRef} className="space-y-3 max-h-[600px] overflow-y-auto">
          <AnimatePresence initial={false}>
            {isLoading && activities.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-8 text-muted-foreground"
              >
                Loading activities...
              </motion.div>
            ) : activities.length === 0 ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-8 text-muted-foreground"
              >
                No recent activity
              </motion.div>
            ) : (
              activities.slice(0, limit).map((activity, index) => {
                const Icon = getIconForActivity(activity);
                return (
                  <motion.div
                    key={activity.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.05 }}
                    className={cn(
                      'flex gap-3 p-3 rounded-lg transition-colors',
                      !activity.read && 'bg-purple-50 dark:bg-purple-900/10'
                    )}
                  >
                    <div
                      className={cn(
                        'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                        SEVERITY_COLORS[activity.severity]
                      )}
                    >
                      <Icon className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium truncate">{activity.title}</p>
                        {!activity.read && (
                          <span className="h-2 w-2 rounded-full bg-purple-500" />
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground line-clamp-2">
                        {activity.description}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Badge variant="outline" className="text-xs">
                          {activity.service}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatTime(activity.timestamp)}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                );
              })
            )}
          </AnimatePresence>
        </div>
      </CardContent>
    </Card>
  );
}
