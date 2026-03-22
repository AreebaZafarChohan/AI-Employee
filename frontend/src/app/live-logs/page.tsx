'use client';

import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollText, RefreshCw, Filter, Mail, MessageSquare, FileText, CheckCircle, XCircle, Clock, AlertTriangle, Bell, Zap } from 'lucide-react';
import { API_BASE_URL } from '@/lib/api-config';
import { cn } from '@/lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

interface ActivityLog {
  id: string;
  timestamp: string;
  source: 'gmail' | 'whatsapp' | 'vault' | 'orchestrator' | 'lex' | 'system';
  action?: string;
  event_type?: string;
  status?: string;
  agent?: string;
  details?: Record<string, unknown>;
  target?: string;
  description?: string;
}

const SOURCE_CONFIG: Record<string, { icon: any; color: string; label: string }> = {
  gmail: { icon: Mail, color: 'bg-red-100 text-red-600 dark:bg-red-900/30', label: 'Gmail' },
  whatsapp: { icon: MessageSquare, color: 'bg-green-100 text-green-600 dark:bg-green-900/30', label: 'WhatsApp' },
  vault: { icon: FileText, color: 'bg-blue-100 text-blue-600 dark:bg-blue-900/30', label: 'Vault' },
  orchestrator: { icon: Zap, color: 'bg-purple-100 text-purple-600 dark:bg-purple-900/30', label: 'Orchestrator' },
  lex: { icon: Bell, color: 'bg-orange-100 text-orange-600 dark:bg-orange-900/30', label: 'LEX' },
  system: { icon: Bell, color: 'bg-gray-100 text-gray-600 dark:bg-gray-900/30', label: 'System' },
};

const STATUS_CONFIG: Record<string, { color: string; icon: any }> = {
  success: { color: 'text-green-600 bg-green-100', icon: CheckCircle },
  failure: { color: 'text-red-600 bg-red-100', icon: XCircle },
  error: { color: 'text-red-600 bg-red-100', icon: AlertTriangle },
  pending: { color: 'text-yellow-600 bg-yellow-100', icon: Clock },
  start: { color: 'text-blue-600 bg-blue-100', icon: Zap },
};

export default function LiveLogsPage() {
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval] = useState(5000); // 5 seconds

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/audit-logs/activity?limit=100`);
      if (res.ok) {
        const json = await res.json();
        setLogs(json.data || []);
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    if (autoRefresh) {
      const interval = setInterval(fetchLogs, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const filteredLogs = filter === 'all' 
    ? logs 
    : logs.filter(log => log.source === filter);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 60) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  const getStatusIcon = (status?: string) => {
    if (!status) return null;
    const config = STATUS_CONFIG[status.toLowerCase()];
    if (!config) return null;
    const Icon = config.icon;
    return <Icon className={cn("h-3.5 w-3.5", config.color)} />;
  };

  const getSourceBadge = (log: ActivityLog) => {
    const config = SOURCE_CONFIG[log.source] || SOURCE_CONFIG.system;
    const Icon = config.icon;
    return (
      <Badge variant="outline" className={cn("gap-1", config.color)}>
        <Icon className="h-3 w-3" />
        {config.label}
      </Badge>
    );
  };

  const getLogDescription = (log: ActivityLog) => {
    // Gmail logs
    if (log.source === 'gmail' && log.action === 'start') {
      return `Gmail Watcher ${log.status === 'success' ? 'started' : 'stopped'}`;
    }
    if (log.agent === 'gmail_watcher') {
      return `Gmail: ${log.action || 'Activity detected'}`;
    }
    
    // WhatsApp logs
    if (log.source === 'whatsapp') {
      return `WhatsApp: ${log.action || log.event_type || 'Activity'}`;
    }
    
    // Orchestrator logs
    if (log.source === 'orchestrator') {
      return `Orchestrator: ${log.action || 'Processing task'}`;
    }
    
    // LEX logs
    if (log.source === 'lex') {
      return `LEX: ${log.action || log.event_type || 'Decision made'}`;
    }
    
    // Generic
    return log.description || log.action || log.event_type || 'System activity';
  };

  return (
    <div className="container mx-auto py-8 px-4 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-purple-100 dark:bg-purple-900/30">
            <ScrollText className="h-6 w-6 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Live Activity Logs</h1>
            <p className="text-sm text-muted-foreground">
              Real-time monitoring of all AI Employee activities
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="text-xs"
          >
            <RefreshCw className={cn("h-3.5 w-3.5 mr-1", autoRefresh && "animate-spin")} />
            {autoRefresh ? 'Auto-refresh ON' : 'Auto-refresh OFF'}
          </Button>
          <Button variant="outline" size="icon" onClick={fetchLogs} disabled={isLoading}>
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        <Button
          variant={filter === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setFilter('all')}
          className="text-xs whitespace-nowrap"
        >
          All ({logs.length})
        </Button>
        {Object.entries(SOURCE_CONFIG).map(([key, config]) => {
          const count = logs.filter(l => l.source === key).length;
          const Icon = config.icon;
          return (
            <Button
              key={key}
              variant={filter === key ? 'default' : 'outline'}
              size="sm"
              onClick={() => setFilter(key)}
              className="text-xs whitespace-nowrap gap-1"
            >
              <Icon className="h-3.5 w-3.5" />
              {config.label} ({count})
            </Button>
          );
        })}
      </div>

      {/* Logs Feed */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center gap-2">
            <ScrollText className="h-5 w-5" />
            Activity Feed
            <Badge variant="outline" className="ml-auto text-xs">
              {filteredLogs.length} events
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="max-h-[700px] overflow-y-auto space-y-2">
            <AnimatePresence mode="wait">
              {isLoading && logs.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-12 text-muted-foreground"
                >
                  <RefreshCw className="h-8 w-8 mx-auto mb-3 animate-spin" />
                  <p>Loading activity logs...</p>
                </motion.div>
              ) : filteredLogs.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-12 text-muted-foreground"
                >
                  <ScrollText className="h-12 w-12 mx-auto mb-3 opacity-20" />
                  <p>No activity logs found</p>
                </motion.div>
              ) : (
                filteredLogs.map((log, index) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: index * 0.03 }}
                    className="flex items-start gap-3 p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                  >
                    {/* Source Icon */}
                    <div className="flex-shrink-0">
                      {getSourceBadge(log)}
                    </div>

                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xs text-muted-foreground">
                          {formatTime(log.timestamp)}
                        </span>
                        {getStatusIcon(log.status)}
                        {log.target && (
                          <Badge variant="outline" className="text-xs">
                            {log.target}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm font-medium truncate">
                        {getLogDescription(log)}
                      </p>
                      {log.details && Object.keys(log.details).length > 0 && (
                        <pre className="mt-1 text-xs text-muted-foreground bg-muted/50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(log.details, null, 2)}
                        </pre>
                      )}
                    </div>
                  </motion.div>
                ))
              )}
            </AnimatePresence>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
