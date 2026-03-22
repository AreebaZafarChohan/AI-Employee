'use client';

import { motion } from 'framer-motion';
import { ToolInvocationList } from '@/components/tools/tool-invocation-list';

export default function ToolsPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 p-6"
    >
      <h1 className="text-2xl font-bold">Tool Execution Monitor</h1>
      <ToolInvocationList />
    </motion.div>
  );
}
