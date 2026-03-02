/**
 * Stats Card Component
 * Displays statistics with icons and trends
 */

'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn } from '@/lib/utils';
import { motion } from 'framer-motion';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  trend?: {
    value: number;
    label: string;
    isPositive: boolean;
  };
  color: 'purple' | 'blue' | 'green' | 'orange' | 'red';
  className?: string;
}

const COLOR_VARIANTS = {
  purple: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-600 dark:text-purple-400',
    border: 'border-purple-200 dark:border-purple-800',
  },
  blue: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800',
  },
  green: {
    bg: 'bg-green-100 dark:bg-green-900/30',
    text: 'text-green-600 dark:text-green-400',
    border: 'border-green-200 dark:border-green-800',
  },
  orange: {
    bg: 'bg-orange-100 dark:bg-orange-900/30',
    text: 'text-orange-600 dark:text-orange-400',
    border: 'border-orange-200 dark:border-orange-800',
  },
  red: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-600 dark:text-red-400',
    border: 'border-red-200 dark:border-red-800',
  },
};

export function StatsCard({
  title,
  value,
  icon: Icon,
  trend,
  color,
  className,
}: StatsCardProps) {
  const variant = COLOR_VARIANTS[color];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <Card className={cn('overflow-hidden transition-all duration-300 hover:shadow-lg', className)}>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            {title}
          </CardTitle>
          <div className={cn('p-2 rounded-lg', variant.bg)}>
            <Icon className={cn('h-4 w-4', variant.text)} />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{value}</div>
          {trend && (
            <p className="text-xs text-muted-foreground mt-1">
              <span className={cn(trend.isPositive ? 'text-green-600' : 'text-red-600')}>
                {trend.isPositive ? '↑' : '↓'} {Math.abs(trend.value)}%
              </span>{' '}
              {trend.label}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
