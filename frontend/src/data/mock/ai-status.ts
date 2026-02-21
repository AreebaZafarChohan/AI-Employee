import { AiStatus } from '../types/ai-status';

export const MOCK_AI_STATUS: AiStatus = {
  id: 'status-001',
  type: 'Thinking',
  updatedAt: new Date('2026-02-21T10:30:00Z'),
  message: 'Analyzing user requirements...',
  startedAt: new Date('2026-02-21T10:28:00Z')
};

export const MOCK_AI_STATUS_IDLE: AiStatus = {
  id: 'status-002',
  type: 'Idle',
  updatedAt: new Date('2026-02-21T09:00:00Z'),
  message: 'Ready for new tasks'
};

export const MOCK_AI_STATUS_PLANNING: AiStatus = {
  id: 'status-003',
  type: 'Planning',
  updatedAt: new Date('2026-02-21T11:00:00Z'),
  message: 'Creating structured plan...',
  startedAt: new Date('2026-02-21T10:55:00Z')
};

/**
 * Get current AI status (mock implementation)
 * @returns Promise resolving to AI status
 */
export async function getAiStatus(): Promise<AiStatus> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_AI_STATUS;
}

/**
 * Get all mock AI statuses (for testing different states)
 * @returns Array of mock AI statuses
 */
export function getAllMockStatuses(): AiStatus[] {
  return [MOCK_AI_STATUS, MOCK_AI_STATUS_IDLE, MOCK_AI_STATUS_PLANNING];
}
