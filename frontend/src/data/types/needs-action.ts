/**
 * Types of action items
 * - InputRequired: User needs to provide information
 * - DecisionNeeded: User needs to make a choice
 * - ReviewRequired: User needs to review and approve
 * - ConfirmationNeeded: User needs to confirm an action
 */
export type ActionItemType = 'InputRequired' | 'DecisionNeeded' | 'ReviewRequired' | 'ConfirmationNeeded';

/**
 * Priority levels for action items
 */
export type ActionItemPriority = 'low' | 'medium' | 'high' | 'urgent';

/**
 * Represents an item requiring user action
 */
export interface NeedsActionItem {
  /** Unique identifier for the action item */
  id: string;

  /** Type of action required */
  type: ActionItemType;

  /** Priority level */
  priority: ActionItemPriority;

  /** When the item was created */
  createdAt: Date;

  /** Brief title describing what's needed */
  title: string;

  /** Detailed description of what's needed from user */
  description: string;

  /** Optional context or background information */
  context?: string;

  /** Optional related plan ID */
  relatedPlanId?: string;

  /** Optional due date */
  dueDate?: Date;

  /** Optional metadata for specific action types */
  metadata?: Record<string, unknown>;
}

/**
 * Maps priority to color variants
 */
export const PRIORITY_VARIANTS: Record<ActionItemPriority, string> = {
  'low': 'text-muted-foreground',
  'medium': 'text-blue-500',
  'high': 'text-orange-500',
  'urgent': 'text-red-500'
};

/**
 * Maps action item type to icon names
 */
export const ACTION_ITEM_ICONS: Record<ActionItemType, string> = {
  'InputRequired': 'message-square',
  'DecisionNeeded': 'scale',
  'ReviewRequired': 'eye',
  'ConfirmationNeeded': 'check-circle'
};
