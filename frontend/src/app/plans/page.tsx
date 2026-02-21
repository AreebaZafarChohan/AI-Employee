'use client';

import { PlansList } from '@/components/plans/plans-list';
import { Header } from '@/components/shared/header';
import { motion } from 'framer-motion';

export default function PlansPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header title="Plans" />
      <main className="flex-1 bg-background">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="container mx-auto py-8 px-4"
        >
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Plans</h1>
            <p className="text-muted-foreground">
              View and manage plans created by your AI Employee
            </p>
          </div>

          <div className="max-w-4xl mx-auto">
            <PlansList />
          </div>
        </motion.div>
      </main>
    </div>
  );
}
