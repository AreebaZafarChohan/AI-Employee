/**
 * System State Model Type Definitions
 * TypeScript types for SystemState entity
 */

import { SystemState } from '@prisma/client';

export type SystemStateEnum = 'Idle' | 'Thinking' | 'Planning' | string;
export type { SystemState };

export interface SystemStateUpdateInput {
  state?: SystemStateEnum;
  lastActivity?: Date;
}

// Valid state transitions
export const STATE_TRANSITIONS: Record<SystemStateEnum, SystemStateEnum[]> = {
  Idle: ['Thinking'],
  Thinking: ['Planning'],
  Planning: ['Idle'],
};
