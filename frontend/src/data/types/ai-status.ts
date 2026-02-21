/**
 * AI Employee operational states
 * - Idle: No active processing, waiting for input
 * - Thinking: Actively processing or analyzing
 * - Planning: Creating a structured plan
 */
export type AiStatusType = 'Idle' | 'Thinking' | 'Planning';

/**
 * AI Status visual variants for UI components
 */
export type AiStatusVariant = 'default' | 'processing' | 'active';

/**
 * Represents the current state of the AI Employee
 */
export interface AiStatus {
  /** Unique identifier for the status record */
  id: string;

  /** Current operational state */
  type: AiStatusType;

  /** When the status was last updated */
  updatedAt: Date;

  /** Optional human-readable message about current activity */
  message?: string;

  /** Optional timestamp of when current state started */
  startedAt?: Date;
}

/**
 * Maps AI status types to UI variants
 */
export const AI_STATUS_VARIANTS: Record<AiStatusType, AiStatusVariant> = {
  'Idle': 'default',
  'Thinking': 'processing',
  'Planning': 'active'
};
