'use client';

import { Card, CardContent } from '@/components/ui/card';
import { NeedsActionItem, PRIORITY_VARIANTS, ACTION_ITEM_ICONS } from '@/data/types/needs-action';
import { cn, formatDate } from '@/lib/utils';
import { motion } from 'framer-motion';
import { ChevronRight, Clock, Calendar } from 'lucide-react';

interface NeedsActionItemProps {
  item: NeedsActionItem;
  isSelected?: boolean;
  onClick?: () => void;
}

export function NeedsActionItemCard({
  item,
  isSelected = false,
  onClick,
}: NeedsActionItemProps) {
  const priorityConfig = {
    low: { gradient: 'from-gray-400 to-gray-600', border: 'border-l-gray-400', bg: 'from-gray-500/10' },
    medium: { gradient: 'from-blue-400 to-cyan-500', border: 'border-l-blue-500', bg: 'from-blue-500/10' },
    high: { gradient: 'from-orange-400 to-red-500', border: 'border-l-orange-500', bg: 'from-orange-500/10' },
    urgent: { gradient: 'from-red-400 to-pink-500', border: 'border-l-red-500', bg: 'from-red-500/10' },
  };

  const config = priorityConfig[item.priority];

  const getIcon = () => {
    switch (item.type) {
      case 'InputRequired':
        return (
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
        );
      case 'DecisionNeeded':
        return (
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
          </svg>
        );
      case 'ReviewRequired':
        return (
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>
          </svg>
        );
      case 'ConfirmationNeeded':
        return (
          <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02, x: 5 }}
      transition={{ type: 'spring', damping: 20 }}
    >
      <Card
        onClick={onClick}
        className={cn(
          'cursor-pointer transition-all duration-300 border-l-4 hover:shadow-2xl glass overflow-hidden',
          config.border,
          isSelected && 'ring-2 ring-primary shadow-2xl'
        )}
      >
        <div className={cn('absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-50 transition-opacity', config.bg)} />
        <CardContent className="p-5 relative z-10">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-3">
              <div className="flex items-center gap-3">
                <div className={cn('p-2 rounded-lg bg-gradient-to-br shadow-lg', config.gradient)}>
                  <div className="text-white">
                    {getIcon()}
                  </div>
                </div>
                <h4 className="font-bold text-lg group-hover:text-primary transition-colors">
                  {item.title}
                </h4>
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {item.description}
              </p>
              {item.context && (
                <div className="p-3 rounded-lg bg-muted/50 text-xs text-muted-foreground">
                  {item.context}
                </div>
              )}
              <div className="flex items-center gap-4 text-xs">
                <motion.span
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  className={cn(
                    'px-3 py-1 rounded-full font-medium bg-gradient-to-r text-white shadow-md',
                    config.gradient
                  )}
                >
                  {item.priority.charAt(0).toUpperCase() + item.priority.slice(1)} Priority
                </motion.span>
                <span className="flex items-center gap-1 text-muted-foreground">
                  <Calendar className="h-3 w-3" />
                  {formatDate(item.createdAt)}
                </span>
                {item.dueDate && (
                  <span className={cn(
                    'flex items-center gap-1 font-medium',
                    new Date(item.dueDate) < new Date() ? 'text-red-500' : 'text-muted-foreground'
                  )}>
                    <Clock className="h-3 w-3" />
                    Due: {formatDate(item.dueDate)}
                  </span>
                )}
              </div>
            </div>
            <motion.div
              initial={{ x: -10 }}
              animate={{ x: 0 }}
              className="flex-shrink-0"
            >
              <ChevronRight className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
            </motion.div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
