'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Plan, PLAN_STATUS_VARIANTS } from '@/data/types/plan';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { FileText, Star } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface RecentPlansListProps {
  plans?: Plan[];
  className?: string;
}

export function RecentPlansList({ plans = [], className }: RecentPlansListProps) {
  const mockPlans: Plan[] = plans.length === 0 ? [
    {
      id: 'plan-001',
      title: 'Q1 Marketing Strategy',
      status: 'Ready',
      createdAt: new Date('2026-02-15T09:00:00Z'),
      description: 'Comprehensive marketing plan for Q1 2026',
      updatedAt: new Date('2026-02-18T14:30:00Z'),
    },
    {
      id: 'plan-002',
      title: 'Product Launch Timeline',
      status: 'Draft',
      createdAt: new Date('2026-02-20T11:00:00Z'),
      description: 'Timeline and milestones for new product launch',
    },
    {
      id: 'plan-003',
      title: 'Customer Feedback Analysis',
      status: 'Done',
      createdAt: new Date('2026-02-10T08:00:00Z'),
      description: 'Analysis of customer feedback from January survey',
      completedAt: new Date('2026-02-12T16:00:00Z'),
    },
  ] : plans;

  const getStatusConfig = (status: Plan['status']) => {
    switch (status) {
      case 'Draft':
        return { gradient: 'from-gray-400 to-gray-600', bg: 'bg-gradient-to-r from-gray-500/10 to-gray-600/10', text: 'text-gray-600 dark:text-gray-400' };
      case 'Ready':
        return { gradient: 'from-blue-400 to-cyan-500', bg: 'bg-gradient-to-r from-blue-500/10 to-cyan-500/10', text: 'text-blue-600 dark:text-blue-400' };
      case 'Done':
        return { gradient: 'from-green-400 to-emerald-500', bg: 'bg-gradient-to-r from-green-500/10 to-emerald-500/10', text: 'text-green-600 dark:text-green-400' };
    }
  };

  return (
    <Card className={cn('overflow-hidden border-0 glass shadow-xl transition-all duration-300 hover:shadow-2xl', className)}>
      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-pink-500/5" />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-gradient-to-br from-purple-400 to-pink-500">
            <FileText className="h-3 w-3 text-white" />
          </div>
          Recent Plans
        </CardTitle>
      </CardHeader>
      <CardContent className="relative z-10">
        <div className="space-y-3">
          {mockPlans.slice(0, 5).map((plan, index) => {
            const config = getStatusConfig(plan.status);
            return (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                whileHover={{ scale: 1.02, x: 5 }}
                className="group cursor-pointer"
              >
                <div className="relative p-4 rounded-xl bg-muted/50 group-hover:bg-gradient-to-r group-hover:from-primary/10 group-hover:to-accent/10 transition-all duration-300">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <h4 className="font-semibold group-hover:text-primary transition-colors">
                          {plan.title}
                        </h4>
                        {plan.status === 'Done' && (
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ type: 'spring', delay: index * 0.1 }}
                          >
                            <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
                          </motion.div>
                        )}
                      </div>
                      {plan.description && (
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {plan.description}
                        </p>
                      )}
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary/50" />
                        <span>{new Date(plan.createdAt).toLocaleDateString()}</span>
                        {plan.completedAt && (
                          <>
                            <span>•</span>
                            <span className="text-green-500">Completed</span>
                          </>
                        )}
                      </div>
                    </div>
                    <motion.div
                      initial={{ scale: 0, rotate: -180 }}
                      animate={{ scale: 1, rotate: 0 }}
                      transition={{ type: 'spring', delay: 0.2 + index * 0.1 }}
                    >
                      <Badge
                        variant={getStatusConfig(plan.status).text.includes('green') ? 'default' : 'secondary'}
                        className={cn(
                          'border-0 bg-gradient-to-r text-white shadow-lg transition-all duration-300 group-hover:scale-110',
                          config.gradient
                        )}
                      >
                        {plan.status}
                      </Badge>
                    </motion.div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
