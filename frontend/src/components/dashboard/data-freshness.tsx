'use client';

import { useEffect, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

const STALE_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes

export function DataFreshness() {
  const [lastUpdated, setLastUpdated] = useState<Date>(new Date());
  const [agoText, setAgoText] = useState('just now');
  const [isStale, setIsStale] = useState(false);

  useEffect(() => {
    const tick = () => {
      const diff = Date.now() - lastUpdated.getTime();
      setIsStale(diff > STALE_THRESHOLD_MS);

      if (diff < 60000) setAgoText('just now');
      else if (diff < 3600000) setAgoText(`${Math.floor(diff / 60000)}m ago`);
      else setAgoText(`${Math.floor(diff / 3600000)}h ago`);
    };

    tick();
    const interval = setInterval(tick, 10000);
    return () => clearInterval(interval);
  }, [lastUpdated]);

  // Auto-refresh: mark as updated every 60s (simulates data refetch)
  useEffect(() => {
    const interval = setInterval(() => setLastUpdated(new Date()), 60000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex items-center gap-2">
      <RefreshCw
        className={cn(
          'h-3.5 w-3.5',
          isStale ? 'text-orange-500' : 'text-muted-foreground'
        )}
      />
      <span className="text-xs text-muted-foreground">
        Last updated: {agoText}
      </span>
      {isStale && (
        <Badge variant="outline" className="text-xs text-orange-600 border-orange-300">
          Stale
        </Badge>
      )}
    </div>
  );
}
