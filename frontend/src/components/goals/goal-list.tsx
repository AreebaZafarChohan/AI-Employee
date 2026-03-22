'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { SkeletonLoader } from '@/components/shared/skeleton-loader';
import { EmptyState } from '@/components/shared/empty-state';
import { GoalCard } from './goal-card';
import { GoalForm } from './goal-form';
import { useGoals, useCreateGoal, type Goal } from '@/hooks/use-goals';
import { Target } from 'lucide-react';

interface GoalListProps {
  onSelectGoal?: (goal: Goal) => void;
}

export function GoalList({ onSelectGoal }: GoalListProps) {
  const { data: goals, isLoading, isError } = useGoals();
  const createGoal = useCreateGoal();
  const [showForm, setShowForm] = useState(false);

  if (isLoading) {
    return <SkeletonLoader variant="card" count={6} />;
  }

  if (isError) {
    return (
      <div className="text-center py-8 text-destructive">
        Failed to load goals. Please try again.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Goals</h2>
        <Button onClick={() => setShowForm(true)} size="sm">
          <Plus className="h-4 w-4 mr-1" />
          Create Goal
        </Button>
      </div>

      {showForm && (
        <div className="rounded-xl border p-4">
          <GoalForm
            isLoading={createGoal.isPending}
            onSubmit={(data) => {
              createGoal.mutate(data, {
                onSuccess: () => setShowForm(false),
              });
            }}
            onCancel={() => setShowForm(false)}
          />
        </div>
      )}

      {(!goals || goals.length === 0) ? (
        <EmptyState
          icon={Target}
          title="No goals yet"
          description="Create your first goal to start tracking progress."
          action={{ label: 'Create Goal', onClick: () => setShowForm(true) }}
        />
      ) : (
        <motion.div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          variants={{ hidden: {}, show: { transition: { staggerChildren: 0.05 } } }}
          initial="hidden"
          animate="show"
        >
          {goals.map((goal) => (
            <motion.div key={goal.id} variants={{ hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } }}>
              <GoalCard
                goal={goal}
                onClick={() => onSelectGoal?.(goal)}
              />
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
