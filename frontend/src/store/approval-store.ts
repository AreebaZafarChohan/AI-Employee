/**
 * Approval Store - Manages pending approvals across all services
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export type ApprovalType = 'gmail' | 'whatsapp' | 'linkedin' | 'file' | 'payment' | 'post';
export type ApprovalStatus = 'pending' | 'approved' | 'rejected';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface ApprovalItem {
  id: string;
  type: ApprovalType;
  status: ApprovalStatus;
  riskLevel: RiskLevel;
  title: string;
  description: string;
  sender?: string;
  recipient?: string;
  subject?: string;
  content?: string;
  confidence?: number;
  createdAt: string;
  expiresAt?: string;
  metadata?: Record<string, unknown>;
}

interface ApprovalState {
  items: ApprovalItem[];
  isLoading: boolean;
  error: string | null;
  stats: {
    pending: number;
    approved: number;
    rejected: number;
    expired: number;
  };
}

interface ApprovalActions {
  setItems: (items: ApprovalItem[]) => void;
  addItem: (item: ApprovalItem) => void;
  updateItem: (id: string, updates: Partial<ApprovalItem>) => void;
  removeItem: (id: string) => void;
  approveItem: (id: string) => Promise<void>;
  rejectItem: (id: string, reason?: string) => Promise<void>;
  clearExpired: () => void;
  fetchPending: () => Promise<void>;
  reset: () => void;
}

const initialState: ApprovalState = {
  items: [],
  isLoading: false,
  error: null,
  stats: {
    pending: 0,
    approved: 0,
    rejected: 0,
    expired: 0,
  },
};

export const useApprovalStore = create<ApprovalState & ApprovalActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      setItems: (items) => {
        const pending = items.filter((i) => i.status === 'pending').length;
        const approved = items.filter((i) => i.status === 'approved').length;
        const rejected = items.filter((i) => i.status === 'rejected').length;
        const now = new Date().toISOString();
        const expired = items.filter(
          (i) => i.expiresAt && i.expiresAt < now && i.status === 'pending'
        ).length;

        set({
          items,
          stats: { pending, approved, rejected, expired },
        });
      },

      addItem: (item) =>
        set((state) => ({
          items: [item, ...state.items],
          stats: {
            ...state.stats,
            pending: state.stats.pending + 1,
          },
        })),

      updateItem: (id, updates) =>
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id ? { ...item, ...updates } : item
          ),
        })),

      removeItem: (id) =>
        set((state) => {
          const item = state.items.find((i) => i.id === id);
          return {
            items: state.items.filter((i) => i.id !== id),
            stats: {
              ...state.stats,
              [item?.status || 'pending']: state.stats[item?.status || 'pending'] - 1,
            },
          };
        }),

      approveItem: async (id) => {
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id ? { ...item, status: 'approved' } : item
          ),
          stats: {
            ...state.stats,
            pending: state.stats.pending - 1,
            approved: state.stats.approved + 1,
          },
        }));
        // API call will be added later
      },

      rejectItem: async (id, reason) => {
        set((state) => ({
          items: state.items.map((item) =>
            item.id === id ? { ...item, status: 'rejected', metadata: { ...item.metadata, rejectReason: reason } } : item
          ),
          stats: {
            ...state.stats,
            pending: state.stats.pending - 1,
            rejected: state.stats.rejected + 1,
          },
        }));
        // API call will be added later
      },

      clearExpired: () => {
        const now = new Date().toISOString();
        set((state) => {
          const expired = state.items.filter(
            (i) => i.expiresAt && i.expiresAt < now && i.status === 'pending'
          );
          return {
            items: state.items.filter(
              (i) => !(i.expiresAt && i.expiresAt < now && i.status === 'pending')
            ),
            stats: {
              ...state.stats,
              pending: state.stats.pending - expired.length,
              expired: state.stats.expired + expired.length,
            },
          };
        });
      },

      fetchPending: async () => {
        set({ isLoading: true, error: null });
        try {
          // API call will be added later
          // Mock data for now
          await new Promise((resolve) => setTimeout(resolve, 500));
          set({ isLoading: false });
        } catch (error) {
          set({
            isLoading: false,
            error: error instanceof Error ? error.message : 'Failed to fetch pending approvals',
          });
        }
      },

      reset: () => set(initialState),
    }),
    { name: 'ApprovalStore' }
  )
);
