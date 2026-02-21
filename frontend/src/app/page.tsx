'use client';

import { AiStatusCard } from '@/components/dashboard/ai-status-card';
import { ActiveTasksPreview } from '@/components/dashboard/active-tasks-preview';
import { RecentPlansList } from '@/components/dashboard/recent-plans-list';
import { ActivityFeed } from '@/components/dashboard/activity-feed';
import { Header } from '@/components/shared/header';
import { MOCK_AI_STATUS } from '@/data/mock/ai-status';
import { MOCK_PLANS } from '@/data/mock/plans';
import { motion } from 'framer-motion';
import { TrendingUp, Clock, CheckCircle, Sparkles } from 'lucide-react';

export default function DashboardPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 30 },
    show: { 
      opacity: 1, 
      y: 0,
      transition: {
        type: 'spring' as const,
        damping: 20,
        stiffness: 100,
      }
    },
  };

  const stats = [
    { label: 'Active Tasks', value: '5', icon: Clock, gradient: 'from-blue-500 to-cyan-500', color: 'text-blue-500' },
    { label: 'Plans Created', value: '12', icon: TrendingUp, gradient: 'from-purple-500 to-pink-500', color: 'text-purple-500' },
    { label: 'Completed', value: '8', icon: CheckCircle, gradient: 'from-green-500 to-emerald-500', color: 'text-green-500' },
  ];

  return (
    <div className="flex flex-col min-h-screen">
      <Header title="Dashboard" />
      <main className="flex-1 bg-background">
        <div className="container mx-auto py-8 px-4">
          {/* Welcome Section */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="mb-8"
          >
            <div className="flex items-center gap-3 mb-2">
              <Sparkles className="h-8 w-8 text-primary animate-pulse" />
              <h1 className="text-5xl font-bold gradient-text">Welcome Back</h1>
            </div>
            <p className="text-muted-foreground text-lg ml-11">
              Here's what's happening with your AI Employee today.
            </p>
          </motion.div>

          {/* Stats Cards */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="grid gap-4 md:grid-cols-3 mb-8"
          >
            {stats.map((stat, index) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: 0.1 + index * 0.1 }}
                whileHover={{ scale: 1.05, y: -5 }}
                className="relative group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-primary/20 to-accent/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative glass p-6 rounded-2xl shadow-xl">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
                      <p className="text-4xl font-bold gradient-text">{stat.value}</p>
                    </div>
                    <div className={cn('p-3 rounded-xl bg-gradient-to-br shadow-lg', stat.gradient)}>
                      <stat.icon className="h-6 w-6 text-white" />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Main Content Grid */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="show"
            className="grid gap-6 md:grid-cols-2 lg:grid-cols-3"
          >
            {/* AI Status Card */}
            <motion.div variants={itemVariants} className="md:col-span-2 lg:col-span-2">
              <AiStatusCard status={MOCK_AI_STATUS} className="h-full" />
            </motion.div>

            {/* Active Tasks Preview */}
            <motion.div variants={itemVariants}>
              <ActiveTasksPreview className="h-full" />
            </motion.div>

            {/* Recent Plans List */}
            <motion.div variants={itemVariants} className="md:col-span-2 lg:col-span-2">
              <RecentPlansList plans={MOCK_PLANS} className="h-full" />
            </motion.div>

            {/* Activity Feed */}
            <motion.div variants={itemVariants}>
              <ActivityFeed className="h-full" />
            </motion.div>
          </motion.div>
        </div>
      </main>
    </div>
  );
}

function cn(...classes: any[]) {
  return classes.filter(Boolean).join(' ');
}
