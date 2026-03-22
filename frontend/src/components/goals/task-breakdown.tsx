'use client';

import type { GoalTask } from '@/hooks/use-goals';

interface TaskBreakdownProps {
  tasks: GoalTask[];
}

const statusColor: Record<GoalTask['status'], string> = {
  pending: 'bg-gray-400',
  'in-progress': 'bg-blue-500',
  completed: 'bg-green-500',
  failed: 'bg-red-500',
};

const statusLabel: Record<GoalTask['status'], string> = {
  pending: 'Pending',
  'in-progress': 'In Progress',
  completed: 'Completed',
  failed: 'Failed',
};

export function TaskBreakdown({ tasks }: TaskBreakdownProps) {
  const completed = tasks.filter((t) => t.status === 'completed').length;
  const progress = tasks.length > 0 ? Math.round((completed / tasks.length) * 100) : 0;

  return (
    <div className="space-y-4">
      {/* Overall progress */}
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="font-medium">Task Progress</span>
          <span className="text-muted-foreground">
            {completed}/{tasks.length} completed
          </span>
        </div>
        <div className="h-2 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full rounded-full bg-primary transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Task list */}
      <ul className="space-y-2">
        {tasks.map((task) => (
          <li key={task.id} className="flex items-center gap-3 text-sm">
            <span
              className={`h-2.5 w-2.5 rounded-full shrink-0 ${statusColor[task.status]}`}
            />
            <span className="flex-1 truncate">{task.title}</span>
            <span className="text-xs text-muted-foreground shrink-0">
              {statusLabel[task.status]}
            </span>
          </li>
        ))}
      </ul>

      {tasks.length === 0 && (
        <p className="text-sm text-muted-foreground text-center py-4">
          No tasks yet
        </p>
      )}
    </div>
  );
}
