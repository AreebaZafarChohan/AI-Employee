'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useUpdateGoal, type Goal } from '@/hooks/use-goals';

interface GoalCardProps {
  goal: Goal;
  onClick?: () => void;
}

const priorityVariant: Record<Goal['priority'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
  low: 'secondary',
  medium: 'default',
  high: 'destructive',
  critical: 'destructive',
};

const statusVariant: Record<Goal['status'], 'default' | 'secondary' | 'success' | 'outline' | 'processing'> = {
  Draft: 'outline',
  Active: 'processing',
  Completed: 'success',
  Cancelled: 'secondary',
};

export function GoalCard({ goal, onClick }: GoalCardProps) {
  const updateGoal = useUpdateGoal();

  function transition(status: Goal['status']) {
    updateGoal.mutate({ id: goal.id, status });
  }

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow"
      onClick={onClick}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="text-base truncate">{goal.title}</CardTitle>
          <div className="flex gap-1 shrink-0">
            <Badge variant={priorityVariant[goal.priority]}>{goal.priority}</Badge>
            <Badge variant={statusVariant[goal.status]}>{goal.status}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {goal.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">{goal.description}</p>
        )}

        {/* Progress bar */}
        <div>
          <div className="flex justify-between text-xs text-muted-foreground mb-1">
            <span>Progress</span>
            <span>{goal.progress}%</span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full rounded-full bg-primary transition-all"
              style={{ width: `${goal.progress}%` }}
            />
          </div>
        </div>

        {/* Transition buttons */}
        <div className="flex gap-2 pt-1" onClick={(e) => e.stopPropagation()}>
          {goal.status === 'Draft' && (
            <Button size="sm" variant="default" onClick={() => transition('Active')}>
              Activate
            </Button>
          )}
          {goal.status === 'Active' && (
            <Button size="sm" variant="default" onClick={() => transition('Completed')}>
              Complete
            </Button>
          )}
          {(goal.status === 'Draft' || goal.status === 'Active') && (
            <Button size="sm" variant="outline" onClick={() => transition('Cancelled')}>
              Cancel
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
