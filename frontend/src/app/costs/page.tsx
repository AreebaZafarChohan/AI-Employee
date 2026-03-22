'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { CostSummaryCards } from '@/components/costs/cost-summary';
import { CostChart } from '@/components/costs/cost-chart';
import { CostBreakdownTable } from '@/components/costs/cost-breakdown-table';
import { useCostSummary, type CostPeriod } from '@/hooks/use-costs';

export default function CostsPage() {
  const [period] = useState<CostPeriod>('week');
  const { data, isLoading } = useCostSummary(period);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6 p-6"
    >
      <h1 className="text-2xl font-bold">Cost Dashboard</h1>
      <CostSummaryCards data={data} isLoading={isLoading} />
      <CostChart />
      <CostBreakdownTable data={data} isLoading={isLoading} />
    </motion.div>
  );
}
