'use client';

import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { StatusBadge } from './status-badge';
import { RiskBadge } from './risk-badge';
import { ChannelBadge } from './channel-badge';
import { ApprovalActions } from './approval-actions';
import { formatRelativeTime, truncateText } from '@/lib/utils';
import type { VaultItem } from '@/types/vault';

interface Column {
  key: string;
  label: string;
  render?: (item: VaultItem) => React.ReactNode;
}

interface VaultTableProps {
  title: string;
  icon?: React.ReactNode;
  items: VaultItem[] | undefined;
  isLoading: boolean;
  isError: boolean;
  columns: Column[];
  showActions?: boolean;
  emptyMessage?: string;
}

export function VaultTable({
  title,
  icon,
  items,
  isLoading,
  isError,
  columns,
  showActions = true,
  emptyMessage = 'No items found.',
}: VaultTableProps) {
  if (isError) {
    return (
      <Card className="border-red-500/30">
        <CardHeader>
          <CardTitle className="text-red-400 flex items-center gap-2">
            {icon}
            {title}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">Failed to load data. The backend may be unavailable.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="glass">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {icon}
          {title}
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
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
          </div>
        ) : !items || items.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            {emptyMessage}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  {columns.map((col) => (
                    <th key={col.key} className="text-left p-3 text-muted-foreground font-medium">
                      {col.label}
                    </th>
                  ))}
                  {showActions && (
                    <th className="text-left p-3 text-muted-foreground font-medium">Actions</th>
                  )}
                </tr>
              </thead>
              <tbody>
                {items.map((item, idx) => (
                  <motion.tr
                    key={item.filename}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.03 }}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    {columns.map((col) => (
                      <td key={col.key} className="p-3">
                        {col.render ? col.render(item) : getDefaultValue(item, col.key)}
                      </td>
                    ))}
                    {showActions && (
                      <td className="p-3">
                        {item.status === 'pending' || item.status === 'needs_action' ? (
                          <ApprovalActions filename={item.filename} />
                        ) : (
                          <StatusBadge status={item.status} />
                        )}
                      </td>
                    )}
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function getDefaultValue(item: VaultItem, key: string): React.ReactNode {
  switch (key) {
    case 'sender':
      return item.metadata.sender ?? item.metadata.from ?? '—';
    case 'from':
      return item.metadata.from ?? '—';
    case 'subject':
      return item.metadata.subject ?? item.title;
    case 'snippet':
      return truncateText(item.metadata.snippet ?? item.body_preview, 80);
    case 'message_preview':
      return truncateText(item.metadata.message_preview ?? item.body_preview, 80);
    case 'risk':
      return <RiskBadge level={item.risk_level} />;
    case 'status':
      return <StatusBadge status={item.status} />;
    case 'channel':
      return <ChannelBadge channel={item.channel} />;
    case 'time':
      return item.created_at ? formatRelativeTime(new Date(item.created_at)) : '—';
    case 'title':
      return truncateText(item.title, 60);
    default:
      return '—';
  }
}
