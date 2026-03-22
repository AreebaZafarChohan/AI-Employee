'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollText } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';

interface AuditEntry {
  timestamp: string;
  approval_id?: string;
  stage?: string;
  event_type?: string;
  action?: string;
  status?: string;
  [key: string]: unknown;
}

export function AuditLogViewer() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/audit-logs?limit=50`);
        if (res.ok) {
          const json = await res.json();
          setEntries(json.data || []);
        }
      } catch { /* silent */ }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 30000);
    return () => clearInterval(interval);
  }, []);

  const filtered = filter
    ? entries.filter((e) => JSON.stringify(e).toLowerCase().includes(filter.toLowerCase()))
    : entries;

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg flex items-center gap-2">
          <ScrollText className="h-5 w-5" />
          Audit Logs
          <Badge variant="outline" className="ml-auto text-xs">
            {filtered.length} entries
          </Badge>
        </CardTitle>
        <input
          type="text"
          placeholder="Filter logs..."
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className="mt-2 w-full rounded-md border px-3 py-1.5 text-sm bg-background"
        />
      </CardHeader>
      <CardContent>
        <div className="max-h-80 overflow-y-auto space-y-2">
          {filtered.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No audit log entries found.
            </p>
          ) : (
            filtered.map((entry, i) => (
              <div
                key={`${entry.timestamp}-${i}`}
                className="flex items-start gap-3 p-2 rounded-lg border text-sm"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs text-muted-foreground">
                      {entry.timestamp ? new Date(entry.timestamp).toLocaleString() : 'N/A'}
                    </span>
                    {(entry.stage || entry.event_type) && (
                      <Badge variant="outline" className="text-xs">
                        {entry.stage || entry.event_type}
                      </Badge>
                    )}
                    {entry.status && (
                      <Badge variant="outline" className="text-xs">
                        {entry.status}
                      </Badge>
                    )}
                  </div>
                  <p className="truncate text-muted-foreground">
                    {entry.approval_id && `[${entry.approval_id}] `}
                    {entry.action || entry.event_type || entry.stage || 'log entry'}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
}
