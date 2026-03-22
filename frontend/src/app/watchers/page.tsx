'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sidebar } from '@/components/shared/sidebar';
import { Header } from '@/components/shared/header';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Eye, Play, StopCircle, RefreshCw, Activity, Terminal, Server,
  Mail, MessageSquare, Linkedin, Globe, ShoppingCart, Twitter,
  Facebook, Instagram, DollarSign, Folder, Webhook, Brain, Briefcase,
  CheckCircle, XCircle, Clock, Loader2, X, RotateCcw, Zap,
  Cpu, HardDrive, TrendingUp, AlertCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useWatchers, useWatcherLogs, useWatcherActions, useWatcherSummary } from '@/hooks/use-watchers';

// Icon mapping for watchers
const WATCHER_ICONS: Record<string, any> = {
  gmail: Mail,
  whatsapp: MessageSquare,
  linkedin: Linkedin,
  odoo: ShoppingCart,
  social: Globe,
  twitter: Twitter,
  facebook: Facebook,
  instagram: Instagram,
  bank: DollarSign,
  vault: Folder,
  webhook: Webhook,
  'vault-rag': Brain,
  'ceo-briefing-weekly': Briefcase,
  'gmail-pubsub': Mail,
  'mcp-odoo': Server,
  'mcp-email': Server,
  'mcp-whatsapp': Server,
  'mcp-linkedin': Server,
  'mcp-twitter': Server,
  'mcp-watcher': Server,
};

// Color mapping for watchers
const WATCHER_COLORS: Record<string, string> = {
  gmail: 'text-red-500 bg-red-500/10',
  whatsapp: 'text-green-500 bg-green-500/10',
  linkedin: 'text-blue-600 bg-blue-600/10',
  odoo: 'text-purple-500 bg-purple-500/10',
  social: 'text-cyan-500 bg-cyan-500/10',
  twitter: 'text-sky-400 bg-sky-400/10',
  facebook: 'text-blue-500 bg-blue-500/10',
  instagram: 'text-pink-500 bg-pink-500/10',
  bank: 'text-green-600 bg-green-600/10',
  vault: 'text-orange-500 bg-orange-500/10',
  webhook: 'text-yellow-500 bg-yellow-500/10',
  'vault-rag': 'text-violet-500 bg-violet-500/10',
  'ceo-briefing-weekly': 'text-indigo-500 bg-indigo-500/10',
  'gmail-pubsub': 'text-red-600 bg-red-600/10',
  'mcp-odoo': 'text-orange-600 bg-orange-600/10',
  'mcp-email': 'text-red-600 bg-red-600/10',
  'mcp-whatsapp': 'text-green-600 bg-green-600/10',
  'mcp-linkedin': 'text-blue-600 bg-blue-600/10',
  'mcp-twitter': 'text-sky-600 bg-sky-600/10',
  'mcp-watcher': 'text-gray-500 bg-gray-500/10',
};

// Status configuration
const STATUS_CONFIG: Record<string, { 
  label: string; 
  color: string; 
  bg: string; 
  icon: any;
  pulse?: boolean;
}> = {
  running: { 
    label: 'Online', 
    color: 'text-emerald-400', 
    bg: 'bg-emerald-500/10 border-emerald-500/20', 
    icon: CheckCircle,
    pulse: true,
  },
  stopped: { 
    label: 'Offline', 
    color: 'text-gray-400', 
    bg: 'bg-gray-500/10 border-gray-500/20', 
    icon: XCircle,
  },
  error: { 
    label: 'Error', 
    color: 'text-red-400', 
    bg: 'bg-red-500/10 border-red-500/20', 
    icon: AlertCircle,
  },
  unknown: { 
    label: 'Unknown', 
    color: 'text-yellow-400', 
    bg: 'bg-yellow-500/10 border-yellow-500/20', 
    icon: Clock,
  },
};

// Format uptime
function formatUptime(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
  return `${Math.floor(seconds / 86400)}d ${Math.floor((seconds % 86400) / 3600)}h`;
}

// Format numbers with K/M suffix
function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

export default function WatchersPage() {
  const [selectedWatcher, setSelectedWatcher] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'running' | 'stopped' | 'error'>('all');
  
  const { data: watchers, isLoading, refetch } = useWatchers();
  const { data: summary } = useWatcherSummary();
  const { data: logs } = useWatcherLogs(selectedWatcher || '', 50);
  const { startWatcher, stopWatcher, restartWatcher, startAll, stopAll } = useWatcherActions();

  // Auto-refresh every 10 seconds
  useEffect(() => {
    const interval = setInterval(refetch, 10000);
    return () => clearInterval(interval);
  }, [refetch]);

  // Filter watchers
  const filteredWatchers = watchers?.filter(w => 
    filter === 'all' ? true : w.status === filter
  ) || [];

  const runningCount = summary?.running || 0;
  const totalCount = summary?.total || 0;
  const totalLogs = summary?.total_logs || 0;
  const totalProcessed = summary?.total_processed || 0;

  return (
    <div className="flex min-h-screen bg-gradient-to-br from-background via-background to-muted/20">
      <Sidebar />
      <div className="ml-72 flex-1 flex flex-col">
        <Header 
          title="PM2 Services" 
          subtitle="Process management"
          actions={
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="gap-2 px-3 py-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                Dry Run
              </Badge>
              <Badge variant="outline" className="gap-2 px-3 py-1.5 font-mono">
                <Activity className="h-3 w-3" />
                {new Date().toLocaleTimeString()}
              </Badge>
            </div>
          }
        />
        
        <main className="flex-1 overflow-y-auto p-8">
          <div className="space-y-6">
            {/* Stats Row */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <motion.div 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0 }}
              >
                <Card className="border-muted/50 bg-gradient-to-br from-emerald-500/10 to-emerald-500/5">
                  <CardContent className="py-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Active Watchers</p>
                        <p className="text-3xl font-bold tracking-tight">{runningCount}/{totalCount}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {totalCount - runningCount} stopped
                        </p>
                      </div>
                      <div className="p-3 rounded-2xl bg-emerald-500/20">
                        <Activity className="h-6 w-6 text-emerald-500" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card className="border-muted/50 bg-gradient-to-br from-blue-500/10 to-blue-500/5">
                  <CardContent className="py-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Logs Today</p>
                        <p className="text-3xl font-bold tracking-tight">{formatNumber(totalLogs)}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Total log entries
                        </p>
                      </div>
                      <div className="p-3 rounded-2xl bg-blue-500/20">
                        <Terminal className="h-6 w-6 text-blue-500" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <Card className="border-muted/50 bg-gradient-to-br from-purple-500/10 to-purple-500/5">
                  <CardContent className="py-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">Items Processed</p>
                        <p className="text-3xl font-bold tracking-tight">{formatNumber(totalProcessed)}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          All time
                        </p>
                      </div>
                      <div className="p-3 rounded-2xl bg-purple-500/20">
                        <TrendingUp className="h-6 w-6 text-purple-500" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>

              <motion.div 
                initial={{ opacity: 0, y: 20 }} 
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <Card className="border-muted/50 bg-gradient-to-br from-orange-500/10 to-orange-500/5">
                  <CardContent className="py-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-1">System Status</p>
                        <p className="text-2xl font-bold tracking-tight">
                          {summary?.health === 'healthy' ? 'All Systems Operational' : 'Degraded'}
                        </p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {summary?.error || 0} errors detected
                        </p>
                      </div>
                      <div className="p-3 rounded-2xl bg-orange-500/20">
                        {summary?.health === 'healthy' ? (
                          <CheckCircle className="h-6 w-6 text-orange-500" />
                        ) : (
                          <AlertCircle className="h-6 w-6 text-orange-500" />
                        )}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            </div>

            {/* Action Bar */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button 
                  onClick={() => startAll.mutate()} 
                  disabled={startAll.isPending || runningCount === totalCount}
                  className="gap-2 bg-emerald-600 hover:bg-emerald-700"
                >
                  {startAll.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  Start All
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => stopAll.mutate()}
                  disabled={stopAll.isPending || runningCount === 0}
                  className="gap-2"
                >
                  {stopAll.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <StopCircle className="h-4 w-4" />
                  )}
                  Stop All
                </Button>
                <Button 
                  variant="outline" 
                  onClick={() => refetch()}
                  className="gap-2"
                >
                  <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
                  Refresh
                </Button>
              </div>

              {/* Filter Tabs */}
              <div className="flex items-center gap-1 p-1 rounded-lg bg-muted/50">
                {(['all', 'running', 'stopped', 'error'] as const).map((f) => (
                  <Button
                    key={f}
                    variant={filter === f ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setFilter(f)}
                    className={cn(
                      "capitalize",
                      filter === f && "bg-primary text-primary-foreground"
                    )}
                  >
                    {f}
                  </Button>
                ))}
              </div>
            </div>

            {/* Watchers Grid */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <AnimatePresence mode="popLayout">
                {isLoading ? (
                  <Card className="col-span-full">
                    <CardContent className="py-16 text-center">
                      <Loader2 className="h-8 w-8 animate-spin mx-auto text-muted-foreground" />
                      <p className="text-muted-foreground mt-4">Loading watchers...</p>
                    </CardContent>
                  </Card>
                ) : !filteredWatchers.length ? (
                  <Card className="col-span-full">
                    <CardContent className="py-16 text-center">
                      <Eye className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                      <p className="text-muted-foreground">No watchers found</p>
                    </CardContent>
                  </Card>
                ) : (
                  filteredWatchers.map((watcher, i) => {
                    const Icon = WATCHER_ICONS[watcher.id] || Eye;
                    const statusConf = STATUS_CONFIG[watcher.status] || STATUS_CONFIG.stopped;
                    const StatusIcon = statusConf.icon;
                    const colorClass = WATCHER_COLORS[watcher.id] || 'text-gray-500 bg-gray-500/10';

                    return (
                      <motion.div
                        key={watcher.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        transition={{ delay: i * 0.05 }}
                      >
                        <Card 
                          className={cn(
                            "group relative overflow-hidden transition-all duration-300 hover:shadow-xl hover:shadow-primary/5 cursor-pointer border-muted/50",
                            selectedWatcher === watcher.id && "ring-2 ring-primary shadow-lg shadow-primary/10"
                          )}
                          onClick={() => setSelectedWatcher(watcher.id === selectedWatcher ? null : watcher.id)}
                        >
                          {/* Status indicator bar */}
                          <div className={cn(
                            "absolute top-0 left-0 right-0 h-1",
                            watcher.status === 'running' && "bg-emerald-500",
                            watcher.status === 'stopped' && "bg-gray-500",
                            watcher.status === 'error' && "bg-red-500",
                          )} />

                          <CardHeader className="pb-3">
                            <div className="flex items-start justify-between">
                              <div className="flex items-center gap-3">
                                <div className={cn("p-2.5 rounded-xl", colorClass)}>
                                  <Icon className="h-5 w-5" />
                                </div>
                                <div>
                                  <CardTitle className="text-base font-semibold">{watcher.name}</CardTitle>
                                  <CardDescription className="text-xs mt-0.5">
                                    {watcher.description || watcher.script}
                                  </CardDescription>
                                </div>
                              </div>
                              <Badge 
                                variant="outline" 
                                className={cn(
                                  "gap-1.5 px-2.5 py-0.5 text-xs font-medium capitalize border",
                                  statusConf.bg,
                                  statusConf.color
                                )}
                              >
                                {statusConf.pulse && (
                                  <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
                                )}
                                <StatusIcon className="h-3 w-3" />
                                {statusConf.label}
                              </Badge>
                            </div>
                          </CardHeader>

                          <CardContent className="space-y-4">
                            {/* Metrics Row */}
                            <div className="grid grid-cols-3 gap-3">
                              <div className="space-y-1">
                                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                  <Cpu className="h-3 w-3" />
                                  CPU
                                </div>
                                <p className="text-sm font-semibold">
                                  {watcher.status === 'running' ? `${watcher.cpu_percent}%` : '—'}
                                </p>
                              </div>
                              <div className="space-y-1">
                                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                  <HardDrive className="h-3 w-3" />
                                  RAM
                                </div>
                                <p className="text-sm font-semibold">
                                  {watcher.status === 'running' ? `${watcher.memory_mb}M` : '—'}
                                </p>
                              </div>
                              <div className="space-y-1">
                                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                                  <Activity className="h-3 w-3" />
                                  Uptime
                                </div>
                                <p className="text-sm font-semibold">
                                  {watcher.uptime_seconds ? formatUptime(watcher.uptime_seconds) : '—'}
                                </p>
                              </div>
                            </div>

                            {/* Stats Row */}
                            <div className="flex items-center justify-between text-xs">
                              <div className="flex items-center gap-4">
                                <span className="text-muted-foreground">
                                  <span className="font-semibold text-foreground">{watcher.items_processed || 0}</span> processed
                                </span>
                                <span className="text-muted-foreground">
                                  <span className="font-semibold text-foreground">{watcher.logs_today || 0}</span> logs
                                </span>
                              </div>
                              {watcher.pid && (
                                <span className="text-muted-foreground font-mono">
                                  PID: {watcher.pid}
                                </span>
                              )}
                            </div>

                            {/* Last Log */}
                            {watcher.last_log && (
                              <div className="pt-3 border-t border-muted/50">
                                <p className="text-xs text-muted-foreground line-clamp-2 font-mono">
                                  {watcher.last_log}
                                </p>
                              </div>
                            )}

                            {/* Action Buttons */}
                            <div className="flex items-center gap-2 pt-3 border-t border-muted/50">
                              {watcher.status === 'running' ? (
                                <>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="flex-1 gap-1.5 text-xs"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      stopWatcher.mutate(watcher.id);
                                    }}
                                    disabled={stopWatcher.isPending}
                                  >
                                    <StopCircle className="h-3.5 w-3.5" />
                                    Stop
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    className="flex-1 gap-1.5 text-xs"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      restartWatcher.mutate(watcher.id);
                                    }}
                                    disabled={restartWatcher.isPending}
                                  >
                                    <RotateCcw className="h-3.5 w-3.5" />
                                    Restart
                                  </Button>
                                </>
                              ) : (
                                <Button
                                  size="sm"
                                  variant="default"
                                  className="flex-1 gap-1.5 text-xs bg-emerald-600 hover:bg-emerald-700"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    startWatcher.mutate(watcher.id);
                                  }}
                                  disabled={startWatcher.isPending}
                                >
                                  <Play className="h-3.5 w-3.5" />
                                  Start
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                className="gap-1.5 text-xs"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  // Could open logs in new panel or modal
                                }}
                              >
                                <Terminal className="h-3.5 w-3.5" />
                                Logs
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })
                )}
              </AnimatePresence>
            </div>

            {/* Live Logs Panel - Shows when watcher is selected */}
            <AnimatePresence>
              {selectedWatcher && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 20 }}
                >
                  <Card className="border-muted/50 bg-gradient-to-br from-muted/30 to-muted/10">
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-emerald-500/10">
                            <Terminal className="h-5 w-5 text-emerald-500" />
                          </div>
                          <div>
                            <CardTitle className="text-base">
                              Live Logs — {watchers?.find(w => w.id === selectedWatcher)?.name}
                            </CardTitle>
                            <CardDescription className="text-xs">
                              Real-time log output (auto-refreshing)
                            </CardDescription>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="gap-2">
                            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                            Live
                          </Badge>
                          <Button
                            size="icon"
                            variant="ghost"
                            onClick={() => setSelectedWatcher(null)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-[400px] w-full rounded-md border border-muted/50 bg-black/50 p-4">
                        <div className="space-y-1 font-mono text-xs">
                          {!logs?.length ? (
                            <p className="text-muted-foreground text-center py-8">
                              No logs found for today
                            </p>
                          ) : (
                            logs.map((entry, idx) => (
                              <div 
                                key={idx} 
                                className={cn(
                                  "py-1.5 px-2 rounded flex gap-3 hover:bg-white/5 transition-colors",
                                  entry.status === 'error' && "text-red-400",
                                  entry.status === 'success' && "text-emerald-400",
                                  entry.status !== 'error' && entry.status !== 'success' && "text-gray-300"
                                )}
                              >
                                <span className="text-muted-foreground shrink-0 select-none">
                                  [{entry.time}]
                                </span>
                                <span className="break-all flex-1">{entry.message}</span>
                              </div>
                            ))
                          )}
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </main>
      </div>
    </div>
  );
}
