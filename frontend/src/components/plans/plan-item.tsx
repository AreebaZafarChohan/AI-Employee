'use client';

import { Card, CardContent } from '@/components/ui/card';
import { Plan } from '@/data/types/plan';
import { StatusIndicator } from './status-indicator';
import { cn, formatDate } from '@/lib/utils';
import { motion } from 'framer-motion';
import { FileText } from 'lucide-react';

interface PlanItemProps {
  plan: Plan;
  viewMode?: 'list' | 'grid';
  onClick?: () => void;
  className?: string;
}

export function PlanItem({ plan, viewMode = 'list', onClick, className }: PlanItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, y: -5 }}
      transition={{ type: 'spring', damping: 20 }}
    >
      <Card
        onClick={onClick}
        className={cn(
          'cursor-pointer transition-all duration-300 hover:shadow-2xl glass overflow-hidden border-0',
          viewMode === 'list' ? '' : 'h-full',
          className
        )}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-accent/5" />
        <CardContent className="p-5 relative z-10">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-gradient-to-br from-purple-400 to-pink-500 shadow-lg">
                  <FileText className="h-4 w-4 text-white" />
                </div>
                <h4 className="font-bold text-lg group-hover:text-primary transition-colors">
                  {plan.title}
                </h4>
              </div>
              {plan.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {plan.description}
                </p>
              )}
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary/50" />
                <span>{formatDate(plan.createdAt)}</span>
                {plan.completedAt && (
                  <>
                    <span>•</span>
                    <span className="text-green-500 font-medium">Completed</span>
                  </>
                )}
              </div>
            </div>
            <motion.div
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ type: 'spring', delay: 0.2 }}
            >
              <StatusIndicator status={plan.status} showLabel={true} />
            </motion.div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
