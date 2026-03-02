'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from './status-badge';
import { ChannelBadge } from './channel-badge';
import { RiskBadge } from './risk-badge';
import { ApprovalActions } from './approval-actions';
import { formatRelativeTime, truncateText } from '@/lib/utils';
import { Zap } from 'lucide-react';
import type { VaultItem } from '@/types/vault';

interface UnifiedFeedProps {
  items: VaultItem[] | undefined;
  isLoading: boolean;
}

export function UnifiedFeed({ items, isLoading }: UnifiedFeedProps) {
  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-primary" />
          Activity Feed
          {items && (
            <span className="ml-auto text-sm font-normal text-muted-foreground">
              {items.length} item{items.length !== 1 ? 's' : ''}
            </span>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </div>
        ) : !items || items.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No activity yet. Items will appear here as watchers process them.
          </div>
        ) : (
          <div className="space-y-3">
            {items.map((item, idx) => (
              <motion.div
                key={item.filename}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.04 }}
                className="flex items-start gap-4 p-4 rounded-xl border border-white/5 hover:bg-white/5 transition-colors"
              >
                <div className="flex-1 min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm truncate">{item.title}</span>
                    <ChannelBadge channel={item.channel} />
                    <RiskBadge level={item.risk_level} />
                  </div>
                  <p className="text-xs text-muted-foreground truncate">
                    {truncateText(item.body_preview || item.metadata.snippet || '', 120)}
                  </p>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {item.metadata.sender && <span>From: {item.metadata.sender}</span>}
                    {item.metadata.from && !item.metadata.sender && <span>From: {item.metadata.from}</span>}
                    <span>{formatRelativeTime(new Date(item.created_at))}</span>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  {item.status === 'pending' || item.status === 'needs_action' ? (
                    <ApprovalActions filename={item.filename} size="sm" />
                  ) : (
                    <StatusBadge status={item.status} />
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
