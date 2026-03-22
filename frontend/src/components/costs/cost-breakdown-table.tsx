'use client';

import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import type { CostSummary } from '@/hooks/use-costs';

type Tab = 'agent' | 'model';
type SortKey = 'name' | 'cost' | 'tokens';

interface CostBreakdownTableProps {
  data?: CostSummary;
  isLoading: boolean;
}

export function CostBreakdownTable({ data, isLoading }: CostBreakdownTableProps) {
  const [tab, setTab] = useState<Tab>('agent');
  const [sortKey, setSortKey] = useState<SortKey>('cost');
  const [sortAsc, setSortAsc] = useState(false);

  const rows = useMemo(() => {
    const source = tab === 'agent' ? data?.breakdown.byAgent : data?.breakdown.byModel;
    if (!source) return [];
    return [...source].sort((a, b) => {
      const mul = sortAsc ? 1 : -1;
      if (sortKey === 'name') return mul * a.name.localeCompare(b.name);
      return mul * (a[sortKey] - b[sortKey]);
    });
  }, [data, tab, sortKey, sortAsc]);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  };

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <th
      className="px-4 py-2 text-left text-xs font-medium text-muted-foreground cursor-pointer hover:text-foreground select-none"
      onClick={() => toggleSort(field)}
    >
      {label} {sortKey === field ? (sortAsc ? '↑' : '↓') : ''}
    </th>
  );

  return (
    <Card className="border-white/10 bg-background/50 backdrop-blur-md">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Cost Breakdown</CardTitle>
        <div className="flex gap-1 rounded-lg bg-muted p-1">
          {(['agent', 'model'] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={cn(
                'px-3 py-1 text-xs font-medium rounded-md transition-colors capitalize',
                tab === t
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              )}
            >
              By {t}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-48 w-full rounded-xl" />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <SortHeader label="Name" field="name" />
                  <SortHeader label="Cost ($)" field="cost" />
                  <SortHeader label="Tokens" field="tokens" />
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.name} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                    <td className="px-4 py-2 font-medium">{row.name}</td>
                    <td className="px-4 py-2">${row.cost.toFixed(4)}</td>
                    <td className="px-4 py-2">{row.tokens.toLocaleString()}</td>
                  </tr>
                ))}
                {rows.length === 0 && (
                  <tr>
                    <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">No data</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
