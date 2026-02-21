'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ActivityFeedItem } from '@/data/types/activity';
import { cn, formatRelativeTime } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  FileText,
  Edit,
  CheckCircle,
  Cpu,
  AlertCircle,
  CheckSquare,
  Settings,
  Sparkles,
} from 'lucide-react';

interface ActivityFeedProps {
  items?: ActivityFeedItem[];
  className?: string;
}

const iconMap = {
  'PlanCreated': FileText,
  'PlanUpdated': Edit,
  'PlanCompleted': CheckCircle,
  'StatusChanged': Cpu,
  'ActionItemCreated': AlertCircle,
  'ActionItemResolved': CheckSquare,
  'SystemEvent': Settings,
};

const getIconGradient = (type: ActivityFeedItem['type']) => {
  switch (type) {
    case 'PlanCreated':
      return 'from-blue-400 to-cyan-500';
    case 'PlanUpdated':
      return 'from-orange-400 to-yellow-500';
    case 'PlanCompleted':
      return 'from-green-400 to-emerald-500';
    case 'StatusChanged':
      return 'from-purple-400 to-pink-500';
    case 'ActionItemCreated':
      return 'from-red-400 to-orange-500';
    case 'ActionItemResolved':
      return 'from-green-400 to-teal-500';
    default:
      return 'from-gray-400 to-gray-500';
  }
};

export function ActivityFeed({ items = [], className }: ActivityFeedProps) {
  const mockItems: ActivityFeedItem[] = items.length === 0 ? [
    {
      id: 'activity-001',
      type: 'PlanCreated',
      timestamp: new Date('2026-02-21T10:30:00Z'),
      title: 'New plan created',
      description: 'AI Employee created a new plan for Q1 Marketing Strategy',
      icon: 'file-text',
    },
    {
      id: 'activity-002',
      type: 'StatusChanged',
      timestamp: new Date('2026-02-21T10:28:00Z'),
      title: 'AI status changed',
      description: 'AI Employee is now Thinking',
      icon: 'cpu',
    },
    {
      id: 'activity-003',
      type: 'ActionItemCreated',
      timestamp: new Date('2026-02-21T09:00:00Z'),
      title: 'Action item created',
      description: 'Budget approval required for Q1 marketing',
      icon: 'alert-circle',
    },
    {
      id: 'activity-004',
      type: 'PlanCompleted',
      timestamp: new Date('2026-02-20T16:00:00Z'),
      title: 'Plan completed',
      description: 'Customer Feedback Analysis plan marked as done',
      icon: 'check-circle',
    },
  ] : items;

  return (
    <Card className={cn('overflow-hidden border-0 glass shadow-xl transition-all duration-300 hover:shadow-2xl', className)}>
      <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/5 to-blue-500/5" />
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
        <CardTitle className="text-sm font-medium flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-gradient-to-br from-cyan-400 to-blue-500">
            <Sparkles className="h-3 w-3 text-white" />
          </div>
          Recent Activity
        </CardTitle>
      </CardHeader>
      <CardContent className="relative z-10">
        <ScrollArea className="h-[350px] pr-2">
          <div className="space-y-4">
            <AnimatePresence>
              {mockItems.slice(0, 10).map((item, index) => {
                const IconComponent = iconMap[item.type] || Settings;
                const gradient = getIconGradient(item.type);
                return (
                  <motion.div
                    key={item.id}
                    initial={{ opacity: 0, x: -30, scale: 0.9 }}
                    animate={{ opacity: 1, x: 0, scale: 1 }}
                    exit={{ opacity: 0, x: 30, scale: 0.9 }}
                    transition={{ duration: 0.3, delay: index * 0.05 }}
                    whileHover={{ scale: 1.02, x: 5 }}
                    className="group cursor-pointer"
                  >
                    <div className="flex items-start space-x-3 p-3 rounded-xl bg-muted/50 group-hover:bg-gradient-to-r group-hover:from-primary/10 group-hover:to-accent/10 transition-all duration-300">
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', delay: index * 0.1 }}
                        className={cn(
                          'flex h-10 w-10 items-center justify-center rounded-xl shadow-lg bg-gradient-to-br flex-shrink-0',
                          gradient
                        )}
                      >
                        <IconComponent className="h-5 w-5 text-white" />
                      </motion.div>
                      <div className="flex-1 space-y-1 min-w-0">
                        <motion.p
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.2 + index * 0.05 }}
                          className="text-sm font-semibold group-hover:text-primary transition-colors"
                        >
                          {item.title}
                        </motion.p>
                        {item.description && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.3 + index * 0.05 }}
                            className="text-xs text-muted-foreground line-clamp-2"
                          >
                            {item.description}
                          </motion.p>
                        )}
                        <motion.p
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: 0.4 + index * 0.05 }}
                          className="text-xs text-muted-foreground/60 flex items-center gap-2"
                        >
                          <span className="inline-block w-1.5 h-1.5 rounded-full bg-primary/30" />
                          {formatRelativeTime(item.timestamp)}
                        </motion.p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
