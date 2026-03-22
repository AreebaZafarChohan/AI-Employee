import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api-client';

export interface WatcherInfo {
  id: string;
  name: string;
  script: string;
  status: 'running' | 'stopped' | 'error' | 'unknown';
  pid?: number;
  cpu_percent?: number;
  memory_mb?: number;
  restart_count?: number;
  uptime_seconds?: number;
  lastLog?: string;
  lastLogTime?: string;
  logsToday: number;
  itemsProcessed: number;
  icon?: string;
  color?: string;
  description?: string;
}

export interface WatcherSummary {
  total: number;
  running: number;
  stopped: number;
  error: number;
  total_logs: number;
  total_processed: number;
  health: 'healthy' | 'degraded';
}

export interface WatcherLogEntry {
  time: string;
  message: string;
  status?: string;
}

export interface WatcherActionResult {
  success: boolean;
  watcher_id?: string;
  pid?: number;
  message?: string;
  error?: string;
}

/**
 * Get list of all watchers with their status
 */
export function useWatchers() {
  return useQuery<WatcherInfo[]>({
    queryKey: ['watchers'],
    queryFn: () => apiGet<WatcherInfo[]>('/watchers').then(res => res.data),
    refetchInterval: 10000, // Refresh every 10 seconds
  });
}

/**
 * Get summary statistics for all watchers
 */
export function useWatcherSummary() {
  return useQuery<WatcherSummary>({
    queryKey: ['watchers', 'summary'],
    queryFn: () => apiGet<WatcherSummary>('/watchers/summary').then(res => res.data),
    refetchInterval: 10000,
  });
}

/**
 * Get logs for a specific watcher
 */
export function useWatcherLogs(id: string, limit = 100) {
  return useQuery<WatcherLogEntry[]>({
    queryKey: ['watchers', id, 'logs'],
    queryFn: () => apiGet<WatcherLogEntry[]>(`/watchers/${id}/logs?limit=${limit}`).then(res => res.data),
    enabled: !!id,
    refetchInterval: 5000, // Refresh logs every 5 seconds
  });
}

/**
 * Hook to start a watcher
 */
export function useStartWatcher() {
  const qc = useQueryClient();
  return useMutation<WatcherActionResult, Error, string>({
    mutationFn: (id) => apiPost<WatcherActionResult>(`/watchers/${id}/start`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchers'] });
      qc.invalidateQueries({ queryKey: ['watchers', 'summary'] });
    },
  });
}

/**
 * Hook to stop a watcher
 */
export function useStopWatcher() {
  const qc = useQueryClient();
  return useMutation<WatcherActionResult, Error, string>({
    mutationFn: (id) => apiPost<WatcherActionResult>(`/watchers/${id}/stop`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchers'] });
      qc.invalidateQueries({ queryKey: ['watchers', 'summary'] });
    },
  });
}

/**
 * Hook to restart a watcher
 */
export function useRestartWatcher() {
  const qc = useQueryClient();
  return useMutation<WatcherActionResult, Error, string>({
    mutationFn: (id) => apiPost<WatcherActionResult>(`/watchers/${id}/restart`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchers'] });
      qc.invalidateQueries({ queryKey: ['watchers', 'summary'] });
    },
  });
}

/**
 * Hook to start all watchers
 */
export function useStartAllWatchers() {
  const qc = useQueryClient();
  return useMutation<any, Error>({
    mutationFn: () => apiPost('/watchers/start-all'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchers'] });
      qc.invalidateQueries({ queryKey: ['watchers', 'summary'] });
    },
  });
}

/**
 * Hook to stop all watchers
 */
export function useStopAllWatchers() {
  const qc = useQueryClient();
  return useMutation<any, Error>({
    mutationFn: () => apiPost('/watchers/stop-all'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['watchers'] });
      qc.invalidateQueries({ queryKey: ['watchers', 'summary'] });
    },
  });
}

/**
 * Combined hook for all watcher actions
 */
export function useWatcherActions() {
  return {
    startWatcher: useStartWatcher(),
    stopWatcher: useStopWatcher(),
    restartWatcher: useRestartWatcher(),
    startAll: useStartAllWatchers(),
    stopAll: useStopAllWatchers(),
  };
}
