'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { AgentList } from '@/components/agents/agent-list';
import { AgentLogViewer } from '@/components/agents/agent-log-viewer';

export default function AgentsPage() {
  const [selectedAgentId, setSelectedAgentId] = useState<string | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="flex gap-6 h-full"
    >
      <div className="flex-1 space-y-6">
        <h1 className="text-2xl font-bold">Agent Control Panel</h1>
        <AgentList onViewLogs={(id) => setSelectedAgentId(id)} />
      </div>

      {selectedAgentId && (
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.2 }}
          className="w-[420px] shrink-0 border-l pl-6 flex flex-col"
        >
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Agent Logs</h2>
            <Button size="icon" variant="ghost" onClick={() => setSelectedAgentId(null)}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <AgentLogViewer agentId={selectedAgentId} />
        </motion.div>
      )}
    </motion.div>
  );
}
