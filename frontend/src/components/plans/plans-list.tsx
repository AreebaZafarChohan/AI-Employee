'use client';

import { Plan } from '@/data/types/plan';
import { PlanItem } from './plan-item';
import { EmptyState } from '@/components/shared/empty-state';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Grid, List, Sparkles } from 'lucide-react';
import { useState } from 'react';

interface PlansListProps {
  plans?: Plan[];
  className?: string;
}

export function PlansList({ plans = [], className }: PlansListProps) {
  const [filter, setFilter] = useState<'all' | Plan['status']>('all');
  const [viewMode, setViewMode] = useState<'list' | 'grid'>('list');

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
    {
      id: 'plan-004',
      title: 'Website Redesign',
      status: 'Ready',
      createdAt: new Date('2026-02-18T10:00:00Z'),
      description: 'Complete overhaul of company website with modern design',
    },
    {
      id: 'plan-005',
      title: 'Employee Training Program',
      status: 'Draft',
      createdAt: new Date('2026-02-21T08:00:00Z'),
      description: 'Training program for new employee onboarding',
    },
  ] : plans;

  const filteredPlans = filter === 'all' 
    ? mockPlans 
    : mockPlans.filter(plan => plan.status === filter);

  const statusCounts = {
    all: mockPlans.length,
    Draft: mockPlans.filter(p => p.status === 'Draft').length,
    Ready: mockPlans.filter(p => p.status === 'Ready').length,
    Done: mockPlans.filter(p => p.status === 'Done').length,
  };

  const filterButtons = [
    { key: 'all', label: 'All', count: statusCounts.all, gradient: 'from-gray-400 to-gray-600' },
    { key: 'Draft', label: 'Draft', count: statusCounts.Draft, gradient: 'from-gray-400 to-gray-600' },
    { key: 'Ready', label: 'Ready', count: statusCounts.Ready, gradient: 'from-blue-400 to-cyan-500' },
    { key: 'Done', label: 'Done', count: statusCounts.Done, gradient: 'from-green-400 to-emerald-500' },
  ] as const;

  if (mockPlans.length === 0) {
    return (
      <EmptyState
        title="No Plans Yet"
        description="Plans will appear here as they are created by the AI Employee."
        icon={FileText}
      />
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className={className}
    >
      {/* Header and Filters */}
      <div className="mb-6 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold gradient-text flex items-center gap-2">
              <Sparkles className="h-6 w-6 text-primary" />
              Plans
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              {mockPlans.length} plan{mockPlans.length !== 1 ? 's' : ''} total
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setViewMode('list')}
              className={viewMode === 'list' ? 'bg-primary/10' : ''}
            >
              <List className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setViewMode('grid')}
              className={viewMode === 'grid' ? 'bg-primary/10' : ''}
            >
              <Grid className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Filter Buttons with animations */}
        <div className="flex gap-2 flex-wrap">
          {filterButtons.map((btn) => (
            <motion.div
              key={btn.key}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                variant={filter === btn.key ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilter(btn.key as typeof filter)}
                className={cn(
                  'relative overflow-hidden transition-all duration-300',
                  filter === btn.key && `bg-gradient-to-r ${btn.gradient} border-0 shadow-lg`
                )}
              >
                {btn.label}
                <span className={cn(
                  'ml-2 px-2 py-0.5 rounded-full text-xs',
                  filter === btn.key ? 'bg-white/20' : 'bg-muted'
                )}>
                  {btn.count}
                </span>
              </Button>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Plans Grid/List */}
      <ScrollArea className="h-[calc(100vh-320px)]">
        <AnimatePresence mode="wait">
          <motion.div
            key={viewMode}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={cn(
              'space-y-3 pr-4',
              viewMode === 'grid' && 'grid grid-cols-1 md:grid-cols-2 gap-4'
            )}
          >
            {filteredPlans.map((plan, index) => (
              <motion.div
                key={plan.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <PlanItem plan={plan} viewMode={viewMode} />
              </motion.div>
            ))}
          </motion.div>
        </AnimatePresence>
      </ScrollArea>
    </motion.div>
  );
}

function cn(...classes: any[]) {
  return classes.filter(Boolean).join(' ');
}
