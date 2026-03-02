/**
 * Vault Types
 * Types for vault items, approval flows, and system health
 */

export type VaultStatus = 'pending' | 'approved' | 'rejected' | 'done' | 'needs_action';

export type VaultChannel = 'whatsapp' | 'gmail' | 'linkedin' | 'plan' | 'general';

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface VaultItem {
  filename: string;
  title: string;
  status: VaultStatus;
  channel: VaultChannel;
  risk_level: RiskLevel;
  created_at: string;
  updated_at?: string;
  metadata: VaultItemMetadata;
  body_preview: string;
}

export interface VaultItemMetadata {
  sender?: string;
  from?: string;
  to?: string;
  subject?: string;
  message_preview?: string;
  snippet?: string;
  type?: string;
  priority?: string;
  risk_score?: number;
  [key: string]: unknown;
}

export interface SystemHealth {
  watcher_running: boolean;
  last_scan_time: string | null;
  last_action: string | null;
  queue_size: number;
  watchers: {
    gmail: WatcherStatus;
    whatsapp: WatcherStatus;
    linkedin: WatcherStatus;
  };
}

export interface WatcherStatus {
  running: boolean;
  last_scan: string | null;
  items_processed: number;
}

export interface ApprovalRequest {
  filename: string;
}

export interface ApprovalResponse {
  success: boolean;
  message: string;
  filename: string;
  new_status: VaultStatus;
}

export interface VaultCounts {
  needs_action: number;
  pending: number;
  approved: number;
  rejected: number;
  done: number;
}
