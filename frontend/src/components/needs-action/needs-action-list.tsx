'use client';

import { NeedsActionItem } from '@/data/types/needs-action';
import { NeedsActionItemCard } from './needs-action-item';
import { EmptyState } from '@/components/shared/empty-state';
import { ScrollArea } from '@/components/ui/scroll-area';
import { motion } from 'framer-motion';
import { CheckCircle2 } from 'lucide-react';

interface NeedsActionListProps {
  items?: NeedsActionItem[];
  selectedId?: string;
  onItemSelected?: (item: NeedsActionItem) => void;
  className?: string;
}

export function NeedsActionList({
  items = [],
  selectedId,
  onItemSelected,
  className,
}: NeedsActionListProps) {
  // Mock data if no items provided
  const mockItems: NeedsActionItem[] = items.length === 0 ? [
    {
      id: 'action-001',
      type: 'InputRequired',
      priority: 'high',
      createdAt: new Date('2026-02-21T09:00:00Z'),
      title: 'Provide budget approval',
      description: 'Review and approve the Q1 marketing budget proposal',
      context: 'The marketing team is waiting for budget confirmation.',
      relatedPlanId: 'plan-001',
      dueDate: new Date('2026-02-23T17:00:00Z'),
    },
    {
      id: 'action-002',
      type: 'DecisionNeeded',
      priority: 'medium',
      createdAt: new Date('2026-02-20T14:00:00Z'),
      title: 'Choose launch date',
      description: 'Select preferred launch date from proposed options',
      context: 'Three launch dates have been proposed.',
    },
    {
      id: 'action-003',
      type: 'ReviewRequired',
      priority: 'low',
      createdAt: new Date('2026-02-19T11:00:00Z'),
      title: 'Review design mockups',
      description: 'Review and provide feedback on the new website design',
    },
    {
      id: 'action-004',
      type: 'ConfirmationNeeded',
      priority: 'urgent',
      createdAt: new Date('2026-02-21T08:00:00Z'),
      title: 'Confirm meeting attendance',
      description: 'Confirm your attendance for the stakeholder meeting',
      dueDate: new Date('2026-02-22T12:00:00Z'),
    },
  ] : items;

  if (mockItems.length === 0) {
    return (
      <EmptyState
        title="No Action Items"
        description="You're all caught up! Check back later for new action items."
        icon={CheckCircle2}
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
      <div className="mb-4 px-2">
        <h2 className="text-lg font-semibold">Action Items</h2>
        <p className="text-sm text-muted-foreground">
          {mockItems.length} item{mockItems.length !== 1 ? 's' : ''} requiring your attention
        </p>
      </div>
      <ScrollArea className="h-[calc(100vh-200px)]">
        <div className="space-y-3 px-2 pb-4">
          {mockItems.map((item) => (
            <NeedsActionItemCard
              key={item.id}
              item={item}
              isSelected={item.id === selectedId}
              onClick={() => onItemSelected?.(item)}
            />
          ))}
        </div>
      </ScrollArea>
    </motion.div>
  );
}
