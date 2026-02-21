/**
 * Types of activity events
 */
export type ActivityType =
  | 'PlanCreated'
  | 'PlanUpdated'
  | 'PlanCompleted'
  | 'StatusChanged'
  | 'ActionItemCreated'
  | 'ActionItemResolved'
  | 'SystemEvent';

/**
 * Represents an activity feed entry
 */
export interface ActivityFeedItem {
  /** Unique identifier for the activity */
  id: string;

  /** Type of activity */
  type: ActivityType;

  /** When the activity occurred */
  timestamp: Date;

  /** Brief description of what happened */
  title: string;

  /** Optional detailed description */
  description?: string;

  /** Optional related entity ID (plan, action item, etc.) */
  relatedEntityId?: string;

  /** Optional related entity type */
  relatedEntityType?: 'plan' | 'action-item' | 'status';

  /** Optional icon name for the activity */
  icon?: string;
}

/**
 * Groups activity items by date for display
 */
export interface ActivityGroup {
  /** Date label (e.g., "Today", "Yesterday", "Feb 20, 2026") */
  label: string;

  /** Activities for this date */
  items: ActivityFeedItem[];
}
