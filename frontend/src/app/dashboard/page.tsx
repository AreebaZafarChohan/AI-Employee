'use client';

import { useEffect } from 'react';
import { Header } from '@/components/shared/header';
import { Sidebar } from '@/components/shared/sidebar';
import { StatsCard } from '@/components/dashboard/stats-card';
import { WatcherOrchestrator } from '@/components/watcher/orchestrator';
import { ActivityFeed } from '@/components/activity/activity-feed';
import { ApprovalCard } from '@/components/approval/approval-card';
import { useWatcherStore } from '@/store/watcher-store';
import { useApprovalStore } from '@/store/approval-store';
import { useActivityStore } from '@/store/activity-store';
import { motion } from 'framer-motion';
import {
  Inbox,
  CheckCircle,
  XCircle,
  Clock,
  Mail,
  MessageSquare,
  Linkedin,
  FileText,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export default function DashboardPage() {
  const { services, status: watcherStatus } = useWatcherStore();
  const { items: approvals, stats, fetchPending } = useApprovalStore();
  const { activities, fetchActivities } = useActivityStore();

  useEffect(() => {
    fetchPending();
    fetchActivities();
  }, [fetchPending, fetchActivities]);

  const pendingApprovals = approvals.filter((a) => a.status === 'pending');

  // Calculate stats from services
  const totalProcessed = services.reduce((sum, s) => sum + s.itemsProcessed, 0);
  const activeServices = services.filter((s) => s.status === 'active').length;

  return (
    <div className="flex min-h-screen bg-background">
      {/* Sidebar */}
      <Sidebar />

      {/* Main Content */}
      <div className="ml-72 flex-1 flex flex-col">
        <Header title="Dashboard" subtitle="AI Employee Command Center" />
      
        <main className="flex-1 bg-background">
          <div className="container mx-auto py-8 px-4 space-y-8">
            {/* Welcome Section */}
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1 className="text-4xl font-bold gradient-text mb-2">
                Welcome Back
              </h1>
              <p className="text-muted-foreground text-lg">
                Here's what's happening with your AI Employee today.
              </p>
            </motion.div>

            {/* Stats Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <StatsCard
                title="Total Processed"
                value={totalProcessed.toLocaleString()}
                icon={Zap}
                trend={{ value: 12, label: 'vs last week', isPositive: true }}
                color="purple"
              />
              <StatsCard
                title="Pending Approvals"
                value={stats.pending}
                icon={Clock}
                color="orange"
              />
              <StatsCard
                title="Approved Today"
                value={stats.approved}
                icon={CheckCircle}
                trend={{ value: 8, label: 'vs yesterday', isPositive: true }}
                color="green"
              />
              <StatsCard
                title="Rejected Today"
                value={stats.rejected}
                icon={XCircle}
                color="red"
              />
            </div>

            {/* Main Content Grid */}
            <div className="grid gap-6 lg:grid-cols-3">
              {/* Left Column - Watcher & Approvals */}
              <div className="lg:col-span-2 space-y-6">
                {/* Watcher Orchestrator */}
                <WatcherOrchestrator />

                {/* Pending Approvals */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="text-2xl font-bold">Pending Approvals</h2>
                    <Badge variant="outline" className="text-sm">
                      {pendingApprovals.length} items
                    </Badge>
                  </div>
                  
                  {pendingApprovals.length === 0 ? (
                    <Card>
                      <CardContent className="py-8 text-center text-muted-foreground">
                        <CheckCircle className="h-12 w-12 mx-auto mb-4 opacity-50" />
                        <p>All caught up! No pending approvals.</p>
                      </CardContent>
                    </Card>
                  ) : (
                    <div className="space-y-4">
                      {pendingApprovals.map((approval) => (
                        <ApprovalCard key={approval.id} approval={approval} />
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column - Activity Feed */}
              <div className="space-y-6">
                <ActivityFeed limit={20} />

                {/* Service Status Cards */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Active Services</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {services.map((service) => {
                      const Icon = 
                        service.name === 'Gmail' ? Mail :
                        service.name === 'WhatsApp' ? MessageSquare :
                        service.name === 'LinkedIn' ? Linkedin :
                        FileText;
                      
                      return (
                        <div
                          key={service.name}
                          className="flex items-center justify-between p-3 rounded-lg border"
                        >
                          <div className="flex items-center gap-3">
                            <div className={cn(
                              'p-2 rounded-lg',
                              service.status === 'active' 
                                ? 'bg-green-100 dark:bg-green-900/30' 
                                : 'bg-gray-100 dark:bg-gray-900/30'
                            )}>
                              <Icon className={cn(
                                'h-5 w-5',
                                service.status === 'active'
                                  ? 'text-green-600 dark:text-green-400'
                                  : 'text-gray-400'
                              )} />
                            </div>
                            <div>
                              <p className="font-medium">{service.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {service.itemsProcessed} processed
                              </p>
                            </div>
                          </div>
                          <Badge
                            variant="outline"
                            className={cn(
                              'capitalize',
                              service.status === 'active'
                                ? 'text-green-600 border-green-200'
                                : 'text-gray-400 border-gray-200'
                            )}
                          >
                            {service.status}
                          </Badge>
                        </div>
                      );
                    })}
                  </CardContent>
                </Card>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
