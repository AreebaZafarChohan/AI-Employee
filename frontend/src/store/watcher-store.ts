/**
 * Watcher Store - 24/7 Orchestrator State
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export type WatcherStatus = 'running' | 'paused' | 'stopped' | 'error';

export interface WatcherState {
  status: WatcherStatus;
  lastSync: string | null;
  queueSize: number;
  processingSpeed: number; // items per minute
  uptime: number; // seconds
  errorLogs: ErrorLog[];
  services: ServiceStatus[];
}

export interface ErrorLog {
  id: string;
  timestamp: string;
  service: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
}

export interface ServiceStatus {
  name: string;
  status: 'active' | 'inactive' | 'error';
  lastActivity: string | null;
  itemsProcessed: number;
}

interface WatcherActions {
  setWatcherStatus: (status: WatcherStatus) => void;
  setLastSync: (timestamp: string) => void;
  setQueueSize: (size: number) => void;
  setProcessingSpeed: (speed: number) => void;
  setUptime: (uptime: number) => void;
  addErrorLog: (log: ErrorLog) => void;
  clearErrorLogs: () => void;
  updateService: (serviceName: string, status: Partial<ServiceStatus>) => void;
  startWatcher: () => Promise<void>;
  stopWatcher: () => Promise<void>;
  pauseWatcher: () => Promise<void>;
  restartWatcher: () => Promise<void>;
  fetchWatcherStatus: () => Promise<void>;
  reset: () => void;
}

const initialState: WatcherState = {
  status: 'stopped',
  lastSync: null,
  queueSize: 0,
  processingSpeed: 0,
  uptime: 0,
  errorLogs: [],
  services: [
    { name: 'Gmail', status: 'inactive', lastActivity: null, itemsProcessed: 0 },
    { name: 'WhatsApp', status: 'inactive', lastActivity: null, itemsProcessed: 0 },
    { name: 'LinkedIn', status: 'inactive', lastActivity: null, itemsProcessed: 0 },
    { name: 'FileSystem', status: 'inactive', lastActivity: null, itemsProcessed: 0 },
  ],
};

export const useWatcherStore = create<WatcherState & WatcherActions>()(
  devtools(
    persist(
      (set, get) => ({
        ...initialState,

        setWatcherStatus: (status) => set({ status }),
        
        setLastSync: (timestamp) => set({ lastSync: timestamp }),
        
        setQueueSize: (size) => set({ queueSize: size }),
        
        setProcessingSpeed: (speed) => set({ processingSpeed: speed }),
        
        setUptime: (uptime) => set({ uptime }),
        
        addErrorLog: (log) =>
          set((state) => ({
            errorLogs: [log, ...state.errorLogs].slice(0, 100), // Keep last 100 errors
          })),
        
        clearErrorLogs: () => set({ errorLogs: [] }),
        
        updateService: (serviceName, status) =>
          set((state) => ({
            services: state.services.map((s) =>
              s.name === serviceName ? { ...s, ...status } : s
            ),
          })),

        startWatcher: async () => {
          try {
            // API call will be added later
            set({ status: 'running' });
          } catch (error) {
            console.error('Failed to start watcher:', error);
          }
        },

        stopWatcher: async () => {
          try {
            // API call will be added later
            set({ status: 'stopped' });
          } catch (error) {
            console.error('Failed to stop watcher:', error);
          }
        },

        pauseWatcher: async () => {
          try {
            // API call will be added later
            set({ status: 'paused' });
          } catch (error) {
            console.error('Failed to pause watcher:', error);
          }
        },

        restartWatcher: async () => {
          try {
            set({ status: 'stopped' });
            // API call will be added later
            set({ status: 'running' });
          } catch (error) {
            console.error('Failed to restart watcher:', error);
          }
        },

        fetchWatcherStatus: async () => {
          try {
            // API call will be added later
            // Mock update for now
            set({
              lastSync: new Date().toISOString(),
              uptime: get().uptime + 5,
            });
          } catch (error) {
            console.error('Failed to fetch watcher status:', error);
          }
        },

        reset: () => set(initialState),
      }),
      {
        name: 'watcher-storage',
        partialize: (state) => ({
          status: state.status,
          services: state.services,
        }),
      }
    ),
    { name: 'WatcherStore' }
  )
);
