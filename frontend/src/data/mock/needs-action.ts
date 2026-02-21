import { NeedsActionItem, ActionItemType, ActionItemPriority } from '../types/needs-action';

export const MOCK_NEEDS_ACTION: NeedsActionItem[] = [
  {
    id: 'action-001',
    type: 'InputRequired',
    priority: 'high',
    createdAt: new Date('2026-02-21T09:00:00Z'),
    title: 'Provide budget approval',
    description: 'Review and approve the Q1 marketing budget proposal',
    context: 'The marketing team is waiting for budget confirmation to proceed with campaign planning.',
    relatedPlanId: 'plan-001',
    dueDate: new Date('2026-02-23T17:00:00Z')
  },
  {
    id: 'action-002',
    type: 'DecisionNeeded',
    priority: 'medium',
    createdAt: new Date('2026-02-20T14:00:00Z'),
    title: 'Choose launch date',
    description: 'Select preferred launch date from proposed options',
    context: 'Three launch dates have been proposed based on market analysis.'
  },
  {
    id: 'action-003',
    type: 'ReviewRequired',
    priority: 'low',
    createdAt: new Date('2026-02-19T11:00:00Z'),
    title: 'Review design mockups',
    description: 'Review and provide feedback on the new website design mockups',
    context: 'Design team has completed the initial mockups for the homepage and product pages.'
  },
  {
    id: 'action-004',
    type: 'ConfirmationNeeded',
    priority: 'urgent',
    createdAt: new Date('2026-02-21T08:00:00Z'),
    title: 'Confirm meeting attendance',
    description: 'Confirm your attendance for the stakeholder meeting on Monday',
    dueDate: new Date('2026-02-22T12:00:00Z')
  }
];

/**
 * Get all needs action items (mock implementation)
 * @returns Promise resolving to array of action items
 */
export async function getNeedsActionItems(): Promise<NeedsActionItem[]> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_NEEDS_ACTION;
}

/**
 * Get action item by ID (mock implementation)
 * @param id - Action item ID to retrieve
 * @returns Promise resolving to action item or undefined
 */
export async function getActionItemById(id: string): Promise<NeedsActionItem | undefined> {
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_NEEDS_ACTION.find(item => item.id === id);
}

/**
 * Get action items by priority (mock implementation)
 * @param priority - Priority level to filter by
 * @returns Promise resolving to filtered array of action items
 */
export async function getActionItemsByPriority(priority: ActionItemPriority): Promise<NeedsActionItem[]> {
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_NEEDS_ACTION.filter(item => item.priority === priority);
}

/**
 * Get action items by type (mock implementation)
 * @param type - Action item type to filter by
 * @returns Promise resolving to filtered array of action items
 */
export async function getActionItemsByType(type: ActionItemType): Promise<NeedsActionItem[]> {
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_NEEDS_ACTION.filter(item => item.type === type);
}
