'use client';

import { NeedsActionItem, ACTION_ITEM_ICONS } from '@/data/types/needs-action';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { cn, formatDate } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Calendar, Clock, Link as LinkIcon } from 'lucide-react';

interface NeedsActionDetailPanelProps {
  item: NeedsActionItem | null;
  isOpen: boolean;
  onClose: () => void;
  onGeneratePlan: (itemId: string) => void;
}

export function NeedsActionDetailPanel({
  item,
  isOpen,
  onClose,
  onGeneratePlan,
}: NeedsActionDetailPanelProps) {
  if (!item) return null;

  const priorityColors = {
    low: 'bg-gray-100 text-gray-800',
    medium: 'bg-blue-100 text-blue-800',
    high: 'bg-orange-100 text-orange-800',
    urgent: 'bg-red-100 text-red-800',
  };

  const typeIcons: Record<NeedsActionItem['type'], React.ReactNode> = {
    'InputRequired': (
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>
    ),
    'DecisionNeeded': (
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      </svg>
    ),
    'ReviewRequired': (
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>
      </svg>
    ),
    'ConfirmationNeeded': (
      <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
      </svg>
    ),
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/50 z-40 md:hidden"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed right-0 top-0 h-full w-full md:w-[480px] bg-background shadow-xl z-50 border-l"
          >
            <div className="flex flex-col h-full">
              {/* Header */}
              <div className="flex items-center justify-between p-4 border-b">
                <h2 className="text-lg font-semibold">Action Item Details</h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={onClose}
                  className="h-8 w-8"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* Content */}
              <ScrollArea className="flex-1">
                <div className="p-4 space-y-6">
                  {/* Title and Type */}
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <h3 className="text-xl font-bold">{item.title}</h3>
                      <div className="flex items-center gap-2">
                        {typeIcons[item.type]}
                        <Badge variant="secondary">{item.type}</Badge>
                      </div>
                    </div>
                  </div>

                  {/* Priority Badge */}
                  <div>
                    <span className="text-sm text-muted-foreground">Priority</span>
                    <div className="mt-1">
                      <Badge className={cn(priorityColors[item.priority])}>
                        {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)}
                      </Badge>
                    </div>
                  </div>

                  {/* Description */}
                  <div className="space-y-2">
                    <span className="text-sm text-muted-foreground">Description</span>
                    <p className="text-base">{item.description}</p>
                  </div>

                  {/* Context */}
                  {item.context && (
                    <div className="space-y-2">
                      <span className="text-sm text-muted-foreground">Context</span>
                      <p className="text-sm bg-muted p-3 rounded-md">{item.context}</p>
                    </div>
                  )}

                  {/* Metadata */}
                  <div className="space-y-3 pt-4 border-t">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      <span>Created: {formatDate(item.createdAt)}</span>
                    </div>
                    {item.dueDate && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        <span>Due: {formatDate(item.dueDate)}</span>
                      </div>
                    )}
                    {item.relatedPlanId && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <LinkIcon className="h-4 w-4" />
                        <span>Related Plan: {item.relatedPlanId}</span>
                      </div>
                    )}
                  </div>
                </div>
              </ScrollArea>

              {/* Footer Actions */}
              <div className="p-4 border-t space-y-2">
                <Button
                  className="w-full"
                  size="lg"
                  onClick={() => onGeneratePlan(item.id)}
                >
                  Generate Plan
                </Button>
                <p className="text-xs text-muted-foreground text-center">
                  This will create a new plan based on this action item
                </p>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
