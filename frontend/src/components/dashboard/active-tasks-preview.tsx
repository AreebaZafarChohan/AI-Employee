'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Task, TASK_STATUS_COLORS } from '@/data/types/task';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { ClipboardList, Zap } from 'lucide-react';

interface ActiveTasksPreviewProps {
  tasks?: Task[];
  className?: string;
}

export function ActiveTasksPreview({ tasks = [], className }: ActiveTasksPreviewProps) {
  const mockTasks: Task[] = tasks.length === 0 ? [
    {
      id: 'task-001',
      title: 'Review Q1 budget proposal',
      status: 'InProgress',
      createdAt: new Date('2026-02-20T09:00:00Z'),
    },
    {
      id: 'task-002',
      title: 'Prepare stakeholder presentation',
      status: 'Pending',
      createdAt: new Date('2026-02-20T10:00:00Z'),
    },
    {
      id: 'task-003',
      title: 'Update project documentation',
      status: 'Blocked',
      createdAt: new Date('2026-02-19T14:00:00Z'),
    },
  ] : tasks;

  const getStatusConfig = (status: Task['status']) => {
    switch (status) {
      case 'Pending':
        return { gradient: 'from-gray-400 to-gray-500', bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-600 dark:text-gray-400' };
      case 'InProgress':
        return { gradient: 'from-blue-400 to-cyan-500', bg: 'bg-blue-100 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400' };
      case 'Blocked':
        return { gradient: 'from-red-400 to-orange-500', bg: 'bg-red-100 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400' };
      case 'Completed':
        return { gradient: 'from-green-400 to-emerald-500', bg: 'bg-green-100 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400' };
    }
  };

  return (
    <Card className={cn('overflow-hidden border-0 glass shadow-xl transition-all duration-300 hover:shadow-2xl', className)}>
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5" />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-gradient-to-br from-orange-400 to-red-500">
            <Zap className="h-3 w-3 text-white" />
          </div>
          Active Tasks
        </CardTitle>
        <ClipboardList className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent className="relative z-10">
        <div className="space-y-3">
          {mockTasks.slice(0, 3).map((task, index) => {
            const config = getStatusConfig(task.status);
            return (
              <motion.div
                key={task.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                whileHover={{ scale: 1.02, x: 5 }}
                className="group cursor-pointer"
              >
                <div className="flex items-center justify-between p-3 rounded-xl bg-muted/50 group-hover:bg-gradient-to-r group-hover:from-primary/10 group-hover:to-accent/10 transition-all duration-300">
                  <div className="flex items-center space-x-3 flex-1">
                    <motion.div
                      className={cn('h-3 w-3 rounded-full shadow-lg bg-gradient-to-br', config.gradient)}
                      animate={{
                        scale: [1, 1.2, 1],
                      }}
                      transition={{
                        duration: 2,
                        repeat: Infinity,
                        delay: index * 0.3,
                      }}
                    />
                    <span className="text-sm font-medium truncate max-w-[180px] group-hover:text-primary transition-colors">
                      {task.title}
                    </span>
                  </div>
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2 + index * 0.1 }}
                    className={cn(
                      'text-xs px-3 py-1 rounded-full font-medium shadow-md',
                      config.bg,
                      config.text
                    )}
                  >
                    {task.status === 'InProgress' ? 'In Progress' : task.status}
                  </motion.span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
