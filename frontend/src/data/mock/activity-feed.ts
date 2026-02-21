import { ActivityFeedItem } from '../types/activity';

export const MOCK_ACTIVITY_FEED: ActivityFeedItem[] = [
  {
    id: 'activity-001',
    type: 'PlanCreated',
    timestamp: new Date('2026-02-21T10:30:00Z'),
    title: 'New plan created',
    description: 'AI Employee created a new plan for Q1 Marketing Strategy',
    relatedEntityId: 'plan-001',
    relatedEntityType: 'plan',
    icon: 'file-text'
  },
  {
    id: 'activity-002',
    type: 'StatusChanged',
    timestamp: new Date('2026-02-21T10:28:00Z'),
    title: 'AI status changed',
    description: 'AI Employee is now Thinking',
    icon: 'cpu'
  },
  {
    id: 'activity-003',
    type: 'ActionItemCreated',
    timestamp: new Date('2026-02-21T09:00:00Z'),
    title: 'Action item created',
    description: 'Budget approval required for Q1 marketing',
    relatedEntityId: 'action-001',
    relatedEntityType: 'action-item',
    icon: 'alert-circle'
  },
  {
    id: 'activity-004',
    type: 'PlanCompleted',
    timestamp: new Date('2026-02-20T16:00:00Z'),
    title: 'Plan completed',
    description: 'Customer Feedback Analysis plan marked as done',
    relatedEntityId: 'plan-003',
    relatedEntityType: 'plan',
    icon: 'check-circle'
  },
  {
    id: 'activity-005',
    type: 'ActionItemResolved',
    timestamp: new Date('2026-02-20T14:30:00Z'),
    title: 'Action item resolved',
    description: 'Vendor selection decision completed',
    relatedEntityId: 'action-005',
    relatedEntityType: 'action-item',
    icon: 'check-square'
  },
  {
    id: 'activity-006',
    type: 'PlanUpdated',
    timestamp: new Date('2026-02-20T11:00:00Z'),
    title: 'Plan updated',
    description: 'Product Launch Timeline plan was updated',
    relatedEntityId: 'plan-002',
    relatedEntityType: 'plan',
    icon: 'edit'
  }
];

/**
 * Get activity feed (mock implementation)
 * @param limit - Maximum number of items to return
 * @returns Promise resolving to array of activity items
 */
export async function getActivityFeed(limit: number = 10): Promise<ActivityFeedItem[]> {
  // Simulate API delay
  await new Promise(resolve => setTimeout(resolve, 100));
  return MOCK_ACTIVITY_FEED.slice(0, limit);
}

/**
 * Get recent activity (mock implementation)
 * @param hours - Number of hours to look back
 * @returns Promise resolving to array of recent activity items
 */
export async function getRecentActivity(hours: number = 24): Promise<ActivityFeedItem[]> {
  await new Promise(resolve => setTimeout(resolve, 100));
  const cutoff = new Date(Date.now() - hours * 60 * 60 * 1000);
  return MOCK_ACTIVITY_FEED.filter(item => item.timestamp >= cutoff);
}
