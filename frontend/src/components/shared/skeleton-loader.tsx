import { cn } from '@/lib/utils';

interface SkeletonLoaderProps {
  variant?: 'card' | 'list' | 'chart' | 'table';
  count?: number;
  className?: string;
}

function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div className={cn('rounded-lg bg-gradient-to-r from-muted/60 via-muted/30 to-muted/60 bg-[length:200%_100%] animate-shimmer', className)} />
  );
}

export function SkeletonLoader({ variant = 'card', count = 3, className }: SkeletonLoaderProps) {
  if (variant === 'card') {
    return (
      <div className={cn('grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4', className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="rounded-xl border p-6 space-y-3">
            <SkeletonBlock className="h-4 w-2/3" />
            <SkeletonBlock className="h-3 w-full" />
            <SkeletonBlock className="h-3 w-4/5" />
            <SkeletonBlock className="h-8 w-24 mt-4" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'list') {
    return (
      <div className={cn('space-y-3', className)}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 p-4 rounded-lg border">
            <SkeletonBlock className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-2">
              <SkeletonBlock className="h-4 w-1/3" />
              <SkeletonBlock className="h-3 w-2/3" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (variant === 'chart') {
    return (
      <div className={cn('rounded-xl border p-6', className)}>
        <SkeletonBlock className="h-4 w-1/4 mb-6" />
        <SkeletonBlock className="h-64 w-full" />
      </div>
    );
  }

  // table
  return (
    <div className={cn('rounded-xl border overflow-hidden', className)}>
      <div className="p-4 border-b">
        <SkeletonBlock className="h-4 w-1/4" />
      </div>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 border-b last:border-0">
          <SkeletonBlock className="h-4 w-1/4" />
          <SkeletonBlock className="h-4 w-1/3" />
          <SkeletonBlock className="h-4 w-1/5" />
        </div>
      ))}
    </div>
  );
}
