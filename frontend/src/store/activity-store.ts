/**
 * Activity Store - Real-time activity feed
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export type ActivityType =
  | 'email_received'
  | 'email_sent'
  | 'whatsapp_received'
  | 'whatsapp_sent'
  | 'linkedin_connection'
  | 'linkedin_message'
  | 'file_processed'
  | 'approval_created'
  | 'approval_approved'
  | 'approval_rejected'
  | 'task_completed'
  | 'error'
  | 'system';

export type ActivitySeverity = 'info' | 'success' | 'warning' | 'error';

export interface Activity {
  id: string;
  type: ActivityType;
  severity: ActivitySeverity;
  title: string;
  description: string;
  service: 'gmail' | 'whatsapp' | 'linkedin' | 'filesystem' | 'system';
  timestamp: string;
  metadata?: Record<string, unknown>;
  read: boolean;
}

interface ActivityState {
  activities: Activity[];
  unreadCount: number;
  isLoading: boolean;
  isConnected: boolean;
  lastUpdate: string | null;
}

interface ActivityActions {
  addActivity: (activity: Omit<Activity, 'id' | 'timestamp' | 'read'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  clearActivities: () => void;
  fetchActivities: () => Promise<void>;
  setConnected: (connected: boolean) => void;
  reset: () => void;
}

const initialState: ActivityState = {
  activities: [],
  unreadCount: 0,
  isLoading: false,
  isConnected: false,
  lastUpdate: null,
};

export const useActivityStore = create<ActivityState & ActivityActions>()(
  devtools(
    (set, get) => ({
      ...initialState,

      addActivity: (activity) => {
        const newActivity: Activity = {
          ...activity,
          id: `activity-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
          timestamp: new Date().toISOString(),
          read: false,
        };

        set((state) => ({
          activities: [newActivity, ...state.activities].slice(0, 500), // Keep last 500
          unreadCount: state.unreadCount + 1,
          lastUpdate: newActivity.timestamp,
        }));
      },

      markAsRead: (id) =>
        set((state) => ({
          activities: state.activities.map((a) =>
            a.id === id ? { ...a, read: true } : a
          ),
          unreadCount: Math.max(0, state.unreadCount - 1),
        })),

      markAllAsRead: () =>
        set((state) => ({
          activities: state.activities.map((a) => ({ ...a, read: true })),
          unreadCount: 0,
        })),

      clearActivities: () =>
        set({
          activities: [],
          unreadCount: 0,
        }),

      fetchActivities: async () => {
        set({ isLoading: true });
        try {
          // API call will be added later
          await new Promise((resolve) => setTimeout(resolve, 500));
          
          // Mock activities for demo
          const mockActivities: Activity[] = [
            {
              id: 'act-1',
              type: 'email_received',
              severity: 'info',
              title: 'New Email Received',
              description: 'Invoice #2026-001 from Client',
              service: 'gmail',
              timestamp: new Date(Date.now() - 60000).toISOString(),
              read: false,
            },
            {
              id: 'act-2',
              type: 'approval_created',
              severity: 'warning',
              title: 'Approval Required',
              description: 'Payment approval needed for $500',
              service: 'gmail',
              timestamp: new Date(Date.now() - 300000).toISOString(),
              read: false,
            },
            {
              id: 'act-3',
              type: 'whatsapp_received',
              severity: 'info',
              title: 'WhatsApp Message',
              description: 'New message from Contact',
              service: 'whatsapp',
              timestamp: new Date(Date.now() - 600000).toISOString(),
              read: true,
            },
            {
              id: 'act-4',
              type: 'task_completed',
              severity: 'success',
              title: 'Task Completed',
              description: 'Email draft sent successfully',
              service: 'gmail',
              timestamp: new Date(Date.now() - 900000).toISOString(),
              read: true,
            },
            {
              id: 'act-5',
              type: 'linkedin_connection',
              severity: 'success',
              title: 'New Connection',
              description: 'John Doe accepted your connection request',
              service: 'linkedin',
              timestamp: new Date(Date.now() - 1800000).toISOString(),
              read: true,
            },
          ];

          set({
            activities: mockActivities,
            unreadCount: mockActivities.filter((a) => !a.read).length,
            isLoading: false,
            lastUpdate: new Date().toISOString(),
          });
        } catch (error) {
          set({
            isLoading: false,
            isConnected: false,
          });
        }
      },

      setConnected: (connected) =>
        set({
          isConnected: connected,
        }),

      reset: () => set(initialState),
    }),
    { name: 'ActivityStore' }
  )
);
