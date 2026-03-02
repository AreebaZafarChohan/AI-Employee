/**
 * AI Provider Interface
 * Abstract interface for AI plan generation
 */

import { TaskContext, PlanStep } from './types';

export interface AIProvider {
  /**
   * Generate a plan for a given task
   * @param task - The task context
   * @returns Array of plan steps
   */
  generatePlan(task: TaskContext): Promise<PlanStep[]>;

  /**
   * Get the provider name
   */
  getName(): string;
}

export default AIProvider;
