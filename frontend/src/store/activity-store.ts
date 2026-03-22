/**
 * Activity Store - Real-time activity feed
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { API_BASE_URL } from '@/lib/api-config';

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

// Map backend log sources to frontend activity types
const mapBackendLogToActivity = (log: any): Activity => {
  const source = log.source || log.agent || 'system';
  const action = log.action || log.event_type || 'activity';
  const status = log.status || 'success';
  
  // Determine type and severity based on source and action
  let type: ActivityType = 'system';
  let severity: ActivitySeverity = 'info';
  let service: 'gmail' | 'whatsapp' | 'linkedin' | 'filesystem' | 'system' = 'system';
  
  if (source.includes('gmail') || log.agent === 'gmail_watcher') {
    service = 'gmail';
    type = action.includes('send') ? 'email_sent' : 'email_received';
  } else if (source.includes('whatsapp') || log.agent === 'whatsapp_watcher') {
    service = 'whatsapp';
    type = 'whatsapp_received';
  } else if (source.includes('linkedin')) {
    service = 'linkedin';
    type = 'linkedin_connection';
  } else if (source.includes('orchestrator')) {
    type = 'task_completed';
    severity = status === 'success' ? 'success' : 'error';
  } else if (source.includes('lex')) {
    type = 'system';
  }
  
  if (status === 'error' || status === 'failure') {
    severity = 'error';
  } else if (status === 'success' && type === 'task_completed') {
    severity = 'success';
  } else if (action.includes('approval') || action.includes('pending')) {
    severity = 'warning';
    type = 'approval_created';
  }

  // Generate unique ID with better uniqueness guarantee
  const uniqueSuffix = `${Date.now()}-${Math.random().toString(36).substr(2, 11)}`;
  return {
    id: log.id || `log-${log.timestamp}-${uniqueSuffix}`,
    type,
    severity,
    title: `${service.charAt(0).toUpperCase() + service.slice(1)} ${action}`,
    description: log.details ? JSON.stringify(log.details) : `${action} - ${status}`,
    service,
    timestamp: log.timestamp,
    metadata: log,
    read: false,
  };
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
          const response = await fetch(`${API_BASE_URL}/audit-logs/activity?limit=50`);
          if (response.ok) {
            const json = await response.json();
            const logs = json.data || [];
            const activities = logs.map(mapBackendLogToActivity);
            
            set({
              activities,
              unreadCount: activities.filter((a) => !a.read).length,
              isLoading: false,
              lastUpdate: new Date().toISOString(),
              isConnected: true,
            });
          } else {
            throw new Error('Failed to fetch activities');
          }
        } catch (error) {
          console.error('Failed to fetch activities:', error);
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
