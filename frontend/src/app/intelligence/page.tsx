'use client';

import { motion } from 'framer-motion';
import { ActivityHeatmap } from '@/components/intelligence/activity-heatmap';
import { ExecutionTimeline } from '@/components/intelligence/execution-timeline';
import { QueueHealth } from '@/components/intelligence/queue-health';

export default function IntelligencePage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 p-6"
    >
      <h1 className="text-2xl font-bold">System Intelligence</h1>
      <ActivityHeatmap />
      <ExecutionTimeline />
      <QueueHealth />
    </motion.div>
  );
}
