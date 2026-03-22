import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface CommandResult {
  task_id: string;
  filename: string;
  status: string;
  platforms: string[];
  topic: string;
  message: string;
}

export interface VaultItem {
  filename: string;
  path: string;
  channel: string;
  title: string;
  status: string;
  createdAt: string;
  content: string;
  platform?: string;
  topic?: string;
}

export function useSendCommand() {
  return useMutation<CommandResult, Error, { command: string }>({
    mutationFn: async (body) => {
      const { data } = await axios.post(`${API_BASE_URL}/agent/command`, body);
      return data.data;
    },
  });
}

export function useVaultItems(folder: string) {
  return useQuery<VaultItem[]>({
    queryKey: ['vault', folder],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE_URL}/vault/${folder}`);
      return data.data;
    },
    refetchInterval: 5000,
  });
}

export function useApproveFile() {
  const qc = useQueryClient();
  return useMutation<any, Error, { filename: string }>({
    mutationFn: async (body) => {
      const { data } = await axios.post(`${API_BASE_URL}/vault/approve`, body);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vault'] });
    },
  });
}

export function useRejectFile() {
  const qc = useQueryClient();
  return useMutation<any, Error, { filename: string }>({
    mutationFn: async (body) => {
      const { data } = await axios.post(`${API_BASE_URL}/vault/reject`, body);
      return data.data;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['vault'] });
    },
  });
}

export function useVaultCounts() {
  return useQuery<Record<string, number>>({
    queryKey: ['vault', 'counts'],
    queryFn: async () => {
      const { data } = await axios.get(`${API_BASE_URL}/vault/counts`);
      return data.data;
    },
    refetchInterval: 10000,
  });
}
