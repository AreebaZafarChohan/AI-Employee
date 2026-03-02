'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getNeedsAction,
  getPending,
  getApproved,
  getRejected,
  getDone,
  getVaultCounts,
  approveFile,
  rejectFile,
  getSystemHealth,
} from '@/lib/vault-api';
import { toast } from '@/components/ui/use-toast';
import type { VaultItem, VaultChannel } from '@/types/vault';

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const vaultKeys = {
  all: ['vault'] as const,
  needsAction: ['vault', 'needs-action'] as const,
  pending: ['vault', 'pending'] as const,
  approved: ['vault', 'approved'] as const,
  rejected: ['vault', 'rejected'] as const,
  done: ['vault', 'done'] as const,
  counts: ['vault', 'counts'] as const,
  systemHealth: ['system', 'health'] as const,
};

const REFETCH_INTERVAL = 5000;

// ---------------------------------------------------------------------------
// Data hooks
// ---------------------------------------------------------------------------

export function useNeedsAction() {
  return useQuery({
    queryKey: vaultKeys.needsAction,
    queryFn: getNeedsAction,
    refetchInterval: REFETCH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

export function usePending() {
  return useQuery({
    queryKey: vaultKeys.pending,
    queryFn: getPending,
    refetchInterval: REFETCH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

export function useApproved() {
  return useQuery({
    queryKey: vaultKeys.approved,
    queryFn: getApproved,
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useRejected() {
  return useQuery({
    queryKey: vaultKeys.rejected,
    queryFn: getRejected,
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useVaultDone() {
  return useQuery({
    queryKey: vaultKeys.done,
    queryFn: getDone,
    refetchInterval: REFETCH_INTERVAL,
  });
}

export function useVaultCounts() {
  return useQuery({
    queryKey: vaultKeys.counts,
    queryFn: getVaultCounts,
    refetchInterval: REFETCH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

export function useSystemHealth() {
  return useQuery({
    queryKey: vaultKeys.systemHealth,
    queryFn: getSystemHealth,
    refetchInterval: REFETCH_INTERVAL,
    refetchIntervalInBackground: true,
  });
}

// ---------------------------------------------------------------------------
// Filtered data hooks
// ---------------------------------------------------------------------------

function useFilteredPending(channel: VaultChannel) {
  const query = usePending();
  const filtered = query.data?.filter((item) => item.channel === channel) ?? [];
  return { ...query, data: filtered };
}

export function useWhatsAppPending() {
  return useFilteredPending('whatsapp');
}

export function useGmailPending() {
  return useFilteredPending('gmail');
}

export function useLinkedInPending() {
  return useFilteredPending('linkedin');
}

// ---------------------------------------------------------------------------
// Mutation hooks
// ---------------------------------------------------------------------------

function useInvalidateVault() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: vaultKeys.all });
    queryClient.invalidateQueries({ queryKey: vaultKeys.counts });
  };
}

export function useApproveFile() {
  const invalidate = useInvalidateVault();

  return useMutation({
    mutationFn: (filename: string) => approveFile(filename),
    onSuccess: (data) => {
      invalidate();
      toast({
        title: 'Approved',
        description: `${data.filename} has been approved.`,
        variant: 'success',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Approval failed',
        description: error.message,
        variant: 'error',
      });
    },
  });
}

export function useRejectFile() {
  const invalidate = useInvalidateVault();

  return useMutation({
    mutationFn: (filename: string) => rejectFile(filename),
    onSuccess: (data) => {
      invalidate();
      toast({
        title: 'Rejected',
        description: `${data.filename} has been rejected.`,
        variant: 'error',
      });
    },
    onError: (error: Error) => {
      toast({
        title: 'Rejection failed',
        description: error.message,
        variant: 'error',
      });
    },
  });
}
