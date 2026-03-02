/**
 * System State Types
 * Type definitions for AI agent status
 */

/**
 * Agent status values
 */
export type AgentStatus = 'idle' | 'processing' | 'working' | 'error';

/**
 * Current state of the AI agent
 */
export interface SystemState {
  status: AgentStatus;
  lastActivityAt: string;    // ISO-8601 datetime
  currentTaskId: string | null;  // UUID v4 or null if idle
}
