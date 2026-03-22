'use client';

import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/lib/api-client';

export interface MemoryItem {
  id: string;
  content: string;
  source: string;
  agentName: string;
  similarityScore: number;
  createdAt: string;
  metadata: Record<string, unknown>;
}

export interface MemorySearchResponse {
  items: MemoryItem[];
  total: number;
}

export const memoryKeys = {
  all: ['memory'] as const,
  search: (query: string, limit: number, offset: number) =>
    ['memory', 'search', query, limit, offset] as const,
  detail: (id: string) => ['memory', id] as const,
};

export function useMemorySearch(query: string, limit = 20, offset = 0) {
  return useQuery({
    queryKey: memoryKeys.search(query, limit, offset),
    queryFn: () =>
      apiGet<MemorySearchResponse>(
        `/api/memory/search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`
      ),
    enabled: query.trim().length > 0,
  });
}

export function useMemoryDetail(id: string | null) {
  return useQuery({
    queryKey: memoryKeys.detail(id ?? ''),
    queryFn: () => apiGet<MemoryItem>(`/api/memory/${id}`),
    enabled: !!id,
  });
}
