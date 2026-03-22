'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { GoalList } from '@/components/goals/goal-list';
import { TaskBreakdown } from '@/components/goals/task-breakdown';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { X } from 'lucide-react';
import type { Goal } from '@/hooks/use-goals';

export default function GoalsPage() {
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 p-6"
    >
      <h1 className="text-2xl font-bold">Goal Management</h1>

      <div className="flex gap-6">
        <div className={selectedGoal ? 'flex-1' : 'w-full'}>
          <GoalList onSelectGoal={setSelectedGoal} />
        </div>

        {selectedGoal && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="w-96 shrink-0"
          >
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-base">{selectedGoal.title}</CardTitle>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedGoal(null)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </CardHeader>
              <CardContent>
                {selectedGoal.description && (
                  <p className="text-sm text-muted-foreground mb-4">
                    {selectedGoal.description}
                  </p>
                )}
                <TaskBreakdown tasks={selectedGoal.tasks ?? []} />
              </CardContent>
            </Card>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
