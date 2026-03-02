/**
 * Activity Log Types
 * Type definitions for system activity logs
 */

/**
 * Types of activity events
 */
export type ActivityEventType =
  | 'task_created'
  | 'task_updated'
  | 'plan_generated'
  | 'system_started'
  | 'system_error'
  | 'whatsapp_message_sent'
  | 'whatsapp_message_received'
  | 'email_received'
  | 'email_sent';

/**
 * Activity log entry
 */
export interface ActivityLog {
  id: string;            // UUID v4
  timestamp: string;     // ISO-8601 datetime
  eventType: ActivityEventType;
  message: string;       // 1-500 characters
  metadata?: Record<string, unknown>;  // Optional structured data
}

/**
 * Query parameters for activity log retrieval
 */
export interface ActivityLogQuery {
  limit?: number;        // Default: 50, Max: 100
  offset?: number;       // Default: 0
}
