'use client';

import { PlanStatus, PLAN_STATUS_VARIANTS } from '@/data/types/plan';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { CheckCircle2, FileText, Clock } from 'lucide-react';

interface StatusIndicatorProps {
  status: PlanStatus;
  showLabel?: boolean;
  className?: string;
}

export function StatusIndicator({
  status,
  showLabel = true,
  className,
}: StatusIndicatorProps) {
  const variant = PLAN_STATUS_VARIANTS[status];

  const getIcon = () => {
    switch (status) {
      case 'Draft':
        return <FileText className="h-4 w-4" />;
      case 'Ready':
        return <Clock className="h-4 w-4" />;
      case 'Done':
        return <CheckCircle2 className="h-4 w-4" />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'Draft':
        return 'bg-secondary text-secondary-foreground';
      case 'Ready':
        return 'bg-blue-100 text-blue-800';
      case 'Done':
        return 'bg-green-100 text-green-800';
    }
  };

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Badge
        variant={variant === 'secondary' ? 'secondary' : variant === 'success' ? 'default' : 'default'}
        className={cn(getStatusColor(), 'gap-1')}
      >
        {getIcon()}
        {showLabel && status}
      </Badge>
    </div>
  );
}
