'use client';

import { motion } from 'framer-motion';
import { Card, CardContent } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

interface StatCardProps {
  title: string;
  value: number | string | undefined;
  icon: React.ReactNode;
  gradient: string;
  isLoading?: boolean;
}

export function StatCard({ title, value, icon, gradient, isLoading }: StatCardProps) {
  return (
    <motion.div whileHover={{ scale: 1.03 }} transition={{ type: 'spring', stiffness: 300 }}>
      <Card className="glass overflow-hidden relative group">
        <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-10 group-hover:opacity-20 transition-opacity`} />
        <CardContent className="p-5 relative z-10">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider">{title}</p>
              {isLoading ? (
                <Skeleton className="h-8 w-16 mt-1" />
              ) : (
                <p className="text-3xl font-bold mt-1">{value ?? 0}</p>
              )}
            </div>
            <div className={`p-3 rounded-xl bg-gradient-to-br ${gradient}`}>
              {icon}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
