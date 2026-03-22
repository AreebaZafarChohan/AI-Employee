'use client';

import { useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { useAgentLogs, type LogSeverity } from '@/hooks/use-agent-logs';

const severities: LogSeverity[] = ['All', 'Info', 'Warn', 'Error'];

const severityColors: Record<string, string> = {
  Info: 'text-blue-500',
  Warn: 'text-yellow-500',
  Error: 'text-red-500',
};

interface AgentLogViewerProps {
  agentId: string;
}

export function AgentLogViewer({ agentId }: AgentLogViewerProps) {
  const { data, isLoading, severity, setSeverity } = useAgentLogs(agentId);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [data]);

  return (
    <div className="flex flex-col h-full gap-3">
      <div className="flex items-center gap-1">
        {severities.map((s) => (
          <Button
            key={s}
            size="sm"
            variant={severity === s ? 'default' : 'outline'}
            onClick={() => setSeverity(s)}
          >
            {s}
          </Button>
        ))}
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto rounded-md border bg-muted/30 p-3 font-mono text-xs space-y-1"
      >
        {isLoading && <p className="text-muted-foreground">Loading logs...</p>}
        {data?.logs.map((log) => (
          <div key={log.id} className="flex gap-2">
            <span className="text-muted-foreground shrink-0">
              {new Date(log.timestamp).toLocaleTimeString()}
            </span>
            <span className={`shrink-0 w-10 ${severityColors[log.severity] ?? ''}`}>
              {log.severity}
            </span>
            <span>{log.message}</span>
          </div>
        ))}
        {!isLoading && (!data?.logs || data.logs.length === 0) && (
          <p className="text-muted-foreground">No logs found.</p>
        )}
      </div>
    </div>
  );
}
