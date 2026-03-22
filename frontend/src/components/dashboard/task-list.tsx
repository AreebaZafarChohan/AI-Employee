'use client';

import { useTasks } from '@/hooks/use-tasks';
import { TaskCard } from './task-card';
import { TaskListSkeleton } from '@/components/shared/loading-skeleton';
import { EmptyState } from '@/components/shared/empty-state';
import { useToast } from '@/components/ui/use-toast';
import type { TaskStatus } from '@/types/task';
import { cn } from '@/lib/utils';
import { AlertCircle, Inbox } from 'lucide-react';

interface TaskListProps {
  className?: string;
}

export function TaskList({ className }: TaskListProps) {
  const { tasks, isLoading, error, updateTask } = useTasks();
  const { toast } = useToast();

  const handleStatusChange = async (taskId: string, status: TaskStatus) => {
    try {
      await updateTask({ id: taskId, input: { status } });
      toast({
        title: 'Task updated',
        description: `Status changed to ${status}`,
        variant: 'success',
      });
    } catch (err) {
      toast({
        title: 'Failed to update task',
        description: err instanceof Error ? err.message : 'Please try again',
        variant: 'error',
      });
    }
  };

  if (isLoading) {
    return (
      <div className={cn('space-y-4', className)}>
        <TaskListSkeleton />
      </div>
    );
  }

  if (error) {
    return (
      <EmptyState
        icon={AlertCircle}
        title="Failed to load tasks"
        description={error.message}
        action={{
          label: 'Retry',
          onClick: () => window.location.reload(),
        }}
      />
    );
  }

  if (tasks.length === 0) {
    return (
      <EmptyState
        icon={Inbox}
        title="No tasks yet"
        description="Create your first task to get started"
      />
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onStatusChange={handleStatusChange}
        />
      ))}
    </div>
  );
}
