'use client';

import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';
import { useAgents } from '@/hooks/use-agents';
import { AgentCard } from '@/components/agents/agent-card';
import { SkeletonLoader } from '@/components/shared/skeleton-loader';
import { EmptyState } from '@/components/shared/empty-state';

interface AgentListProps {
  onViewLogs: (agentId: string) => void;
}

const container = { hidden: {}, show: { transition: { staggerChildren: 0.05 } } };
const item = { hidden: { opacity: 0, y: 10 }, show: { opacity: 1, y: 0 } };

export function AgentList({ onViewLogs }: AgentListProps) {
  const { data: agents, isLoading, error } = useAgents();

  if (isLoading) {
    return <SkeletonLoader />;
  }

  if (error) {
    return <p className="text-red-500 text-sm">Failed to load agents: {error.message}</p>;
  }

  if (!agents || agents.length === 0) {
    return <EmptyState icon={Bot} title="No agents" description="No agents are registered yet." />;
  }

  return (
    <motion.div
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {agents.map((agent) => (
        <motion.div key={agent.id} variants={item}>
          <AgentCard agent={agent} onViewLogs={onViewLogs} />
        </motion.div>
      ))}
    </motion.div>
  );
}
