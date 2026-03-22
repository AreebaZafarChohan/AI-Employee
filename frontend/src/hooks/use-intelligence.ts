'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api-client';

export interface HeatmapCell {
  agent: string;
  hour: number;
  intensity: number; // 0-1
}

export interface TimelineEntry {
  id: string;
  agent: string;
  task: string;
  start: string;
  end: string;
  status: 'running' | 'completed' | 'failed';
}

export interface QueueInfo {
  name: string;
  depth: number;
  rate: number; // items/min
  status: 'healthy' | 'warning' | 'critical';
}

export function useHeatmap() {
  return useQuery({
    queryKey: ['intelligence', 'heatmap'],
    queryFn: () => apiGet<HeatmapCell[]>('/api/intelligence/heatmap'),
  });
}

export function useTimeline() {
  return useQuery({
    queryKey: ['intelligence', 'timeline'],
    queryFn: () => apiGet<TimelineEntry[]>('/api/intelligence/timeline'),
  });
}

export function useQueueHealth() {
  return useQuery({
    queryKey: ['intelligence', 'queues'],
    queryFn: () => apiGet<QueueInfo[]>('/api/intelligence/queues'),
  });
}
