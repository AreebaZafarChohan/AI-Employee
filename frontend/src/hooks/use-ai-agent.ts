import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/lib/api-client';

export interface AgentStatus {
  gemini: string;
  grok: string;
  platforms: Record<string, string>;
  supported: string[];
}

export interface GenerateResult {
  content: string;
  platform: string;
  topic: string;
  provider: string;
  charCount: number;
  maxChars: number;
}

export interface PostResult {
  filename: string;
  platform: string;
  posted: boolean;
  method: string;
  savedTo: string;
  error: string | null;
}

export interface PostHistoryItem {
  filename: string;
  platform: string;
  status: string;
  created_at: string;
  source: string;
  content_preview: string;
}

export function useAgentStatus() {
  return useQuery<AgentStatus>({
    queryKey: ['ai-agent', 'status'],
    queryFn: () => apiGet<AgentStatus>('/ai-agent/status'),
    refetchInterval: 30000,
  });
}

export function useGenerateContent() {
  return useMutation<GenerateResult, Error, { platform: string; topic: string }>({
    mutationFn: (body) => apiPost<GenerateResult>('/ai-agent/generate', body),
  });
}

export function usePostContent() {
  const qc = useQueryClient();
  return useMutation<PostResult, Error, { platform: string; content: string }>({
    mutationFn: (body) => apiPost<PostResult>('/ai-agent/post', body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ai-agent', 'history'] });
    },
  });
}

export function usePostHistory(limit = 50, platform?: string) {
  const params = new URLSearchParams({ limit: String(limit) });
  if (platform) params.set('platform', platform);
  return useQuery<PostHistoryItem[]>({
    queryKey: ['ai-agent', 'history', limit, platform],
    queryFn: () => apiGet<PostHistoryItem[]>(`/ai-agent/history?${params}`),
    refetchInterval: 10000,
  });
}
