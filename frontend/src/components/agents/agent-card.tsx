'use client';

import { Play, Square, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AgentStatusBadge } from '@/components/agents/agent-status-badge';
import { useStartAgent, useStopAgent, type Agent } from '@/hooks/use-agents';

interface AgentCardProps {
  agent: Agent;
  onViewLogs: (agentId: string) => void;
}

export function AgentCard({ agent, onViewLogs }: AgentCardProps) {
  const startAgent = useStartAgent();
  const stopAgent = useStopAgent();

  const isLoading = startAgent.isPending || stopAgent.isPending;

  return (
    <div className="rounded-lg border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-sm">{agent.name}</h3>
        <AgentStatusBadge status={agent.status} />
      </div>

      <p className="text-xs text-muted-foreground">Type: {agent.type}</p>

      {agent.status === 'error' && agent.errorMessage && (
        <p className="text-xs text-red-500">{agent.errorMessage}</p>
      )}

      <div className="flex items-center gap-2 pt-1">
        {agent.status === 'running' ? (
          <Button
            size="sm"
            variant="outline"
            onClick={() => stopAgent.mutate(agent.id)}
            disabled={isLoading}
          >
            <Square className="h-3 w-3 mr-1" />
            Stop
          </Button>
        ) : (
          <Button
            size="sm"
            variant="outline"
            onClick={() => startAgent.mutate(agent.id)}
            disabled={isLoading}
          >
            <Play className="h-3 w-3 mr-1" />
            Start
          </Button>
        )}
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onViewLogs(agent.id)}
        >
          <FileText className="h-3 w-3 mr-1" />
          View Logs
        </Button>
      </div>
    </div>
  );
}
