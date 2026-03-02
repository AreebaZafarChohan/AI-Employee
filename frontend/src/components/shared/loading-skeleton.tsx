'use client';

import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

/**
 * Task List Loading Skeleton
 * Shows placeholder cards while tasks are loading
 */
export function TaskListSkeleton() {
  return (
    <div className="space-y-4">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-4 border rounded-lg">
          <div className="flex items-start justify-between mb-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-20" />
          </div>
          <Skeleton className="h-4 w-full mb-2" />
          <Skeleton className="h-4 w-2/3" />
        </div>
      ))}
    </div>
  );
}

/**
 * Agent Status Loading Skeleton
 */
export function AgentStatusSkeleton() {
  return (
    <div className="p-4">
      <div className="flex items-center gap-4">
        <Skeleton className="h-14 w-14 rounded-xl" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-5 w-24" />
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-3 w-40" />
        </div>
      </div>
    </div>
  );
}

/**
 * Activity Feed Loading Skeleton
 */
export function ActivityFeedSkeleton() {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex items-start gap-3">
          <Skeleton className="h-8 w-8 rounded-full flex-shrink-0" />
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-1/2" />
          </div>
        </div>
      ))}
    </div>
  );
}

/**
 * Plan Display Loading Skeleton
 */
export function PlanSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-6 w-1/2" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
      <div className="space-y-2 mt-4">
        <Skeleton className="h-5 w-1/3" />
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-4 w-full ml-4" />
        ))}
      </div>
    </div>
  );
}

/**
 * Dashboard Stats Loading Skeleton
 */
export function DashboardStatsSkeleton() {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {[1, 2, 3].map((i) => (
        <div key={i} className="p-6 border rounded-xl">
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-8 w-16" />
        </div>
      ))}
    </div>
  );
}
