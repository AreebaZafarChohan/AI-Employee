'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Task, TaskStatus } from '@/types/task';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { CheckCircle2, Clock, XCircle, AlertCircle } from 'lucide-react';

interface TaskCardProps {
  task: Task;
  onStatusChange?: (taskId: string, status: TaskStatus) => void;
  className?: string;
}

const STATUS_CONFIG: Record<TaskStatus, { label: string; icon: React.ReactNode; color: string; bg: string }> = {
  'pending': {
    label: 'Pending',
    icon: <Clock className="h-3.5 w-3.5" />,
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
  },
  'in-progress': {
    label: 'In Progress',
    icon: <AlertCircle className="h-3.5 w-3.5" />,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
  },
  'completed': {
    label: 'Completed',
    icon: <CheckCircle2 className="h-3.5 w-3.5" />,
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
  },
  'cancelled': {
    label: 'Cancelled',
    icon: <XCircle className="h-3.5 w-3.5" />,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
  },
};

export function TaskCard({ task, onStatusChange, className }: TaskCardProps) {
  const statusConfig = STATUS_CONFIG[task.status];

  // Fallback for unknown status
  if (!statusConfig) {
    console.warn('Unknown task status:', task.status);
  }

  const handleStatusChange = (newStatus: TaskStatus) => {
    if (onStatusChange && newStatus !== task.status) {
      onStatusChange(task.id, newStatus);
    }
  };

  return (
    <Card className={cn('transition-all duration-200 hover:shadow-md', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-base font-semibold line-clamp-2">
            {task.title}
          </CardTitle>
          <Badge
            variant="outline"
            className={cn(
              'flex items-center gap-1 whitespace-nowrap border-0',
              statusConfig?.color || 'text-gray-600',
              statusConfig?.bg || 'bg-gray-100'
            )}
          >
            {statusConfig?.icon}
            {statusConfig?.label || task.status}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {task.description && (
          <p className="text-sm text-muted-foreground line-clamp-3">
            {task.description}
          </p>
        )}

        <div className="flex items-center justify-between pt-2 border-t">
          <span className="text-xs text-muted-foreground">
            Updated {new Date(task.updatedAt || task.updated_at || Date.now()).toLocaleDateString()}
          </span>

          {/* Status Update Dropdown */}
          <select
            value={task.status}
            onChange={(e) => handleStatusChange(e.target.value as TaskStatus)}
            className="text-xs border rounded-md px-2 py-1 bg-background focus:outline-none focus:ring-2 focus:ring-primary/20"
            aria-label="Update task status"
          >
            <option value="pending">Pending</option>
            <option value="in-progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
      </CardContent>
    </Card>
  );
}
