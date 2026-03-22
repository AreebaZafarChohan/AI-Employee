'use client';

import type { ToolInvocation } from '@/hooks/use-tools';

interface ToolInvocationDetailProps {
  invocation: ToolInvocation;
}

export function ToolInvocationDetail({ invocation }: ToolInvocationDetailProps) {
  return (
    <div className="px-6 py-4 bg-muted/10 space-y-3 border-t border-border/30">
      <div className="grid grid-cols-2 gap-4 text-sm">
        <div>
          <h4 className="font-medium text-muted-foreground mb-1">Input Parameters</h4>
          <pre className="bg-muted/30 rounded-lg p-3 text-xs overflow-auto max-h-48">
            {JSON.stringify(invocation.input, null, 2)}
          </pre>
        </div>
        <div>
          <h4 className="font-medium text-muted-foreground mb-1">
            {invocation.error ? 'Error' : 'Output'}
          </h4>
          <pre className="bg-muted/30 rounded-lg p-3 text-xs overflow-auto max-h-48">
            {invocation.error
              ? invocation.error
              : invocation.output != null ? JSON.stringify(invocation.output, null, 2) : 'No output'}
          </pre>
        </div>
      </div>
      <div className="flex gap-6 text-xs text-muted-foreground">
        <span>Agent: {invocation.agentName}</span>
        <span>Duration: {invocation.duration ? `${invocation.duration}ms` : 'N/A'}</span>
        <span>Time: {new Date(invocation.timestamp).toLocaleString()}</span>
      </div>
    </div>
  );
}
