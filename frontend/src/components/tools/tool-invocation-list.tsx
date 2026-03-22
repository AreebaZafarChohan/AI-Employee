'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToolInvocations, type ToolInvocation } from '@/hooks/use-tools';
import { ToolInvocationDetail } from './tool-invocation-detail';
import { Pagination } from '@/components/shared/pagination';
import { SkeletonLoader } from '@/components/shared/skeleton-loader';
import { EmptyState } from '@/components/shared/empty-state';
import { Wrench } from 'lucide-react';

const statusStyles: Record<string, string> = {
  success: 'bg-green-500/10 text-green-500',
  failure: 'bg-red-500/10 text-red-500',
  pending: 'bg-yellow-500/10 text-yellow-500',
};

export function ToolInvocationList() {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const { data, isLoading } = useToolInvocations(page, pageSize);

  if (isLoading) return <SkeletonLoader variant="table" count={5} />;

  if (!data || data.items.length === 0) {
    return (
      <EmptyState
        icon={Wrench}
        title="No tool invocations"
        description="Tool executions will appear here in real time."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/30">
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Tool</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Agent</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Time</th>
              <th className="px-4 py-3 text-left font-medium text-muted-foreground">Duration</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((inv: ToolInvocation) => (
              <ToolRow
                key={inv.id}
                invocation={inv}
                isExpanded={expandedId === inv.id}
                onToggle={() => setExpandedId(expandedId === inv.id ? null : inv.id)}
              />
            ))}
          </tbody>
        </table>
      </div>

      <Pagination
        total={data.total}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
        onPageSizeChange={setPageSize}
      />
    </div>
  );
}

function ToolRow({
  invocation,
  isExpanded,
  onToggle,
}: {
  invocation: ToolInvocation;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr
        className="border-b border-border/50 hover:bg-muted/20 transition-colors cursor-pointer"
        onClick={onToggle}
      >
        <td className="px-4 py-3 font-medium">{invocation.toolName}</td>
        <td className="px-4 py-3">
          <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium', statusStyles[invocation.status])}>
            {invocation.status === 'pending' && <Loader2 className="h-3 w-3 animate-spin" />}
            {invocation.status}
          </span>
        </td>
        <td className="px-4 py-3 text-muted-foreground">{invocation.agentName}</td>
        <td className="px-4 py-3 text-muted-foreground">{new Date(invocation.timestamp).toLocaleTimeString()}</td>
        <td className="px-4 py-3 text-muted-foreground">{invocation.duration ? `${invocation.duration}ms` : '—'}</td>
      </tr>
      <AnimatePresence>
        {isExpanded && (
          <tr>
            <td colSpan={5} className="p-0">
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <ToolInvocationDetail invocation={invocation} />
              </motion.div>
            </td>
          </tr>
        )}
      </AnimatePresence>
    </>
  );
}
