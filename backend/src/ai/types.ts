/**
 * AI Provider Types
 * Common types for AI provider interface
 */

export interface PlanStep {
  title: string;
  description: string;
  estimatedDuration?: number | null;
}

export interface TaskContext {
  id: string;
  title: string;
  description?: string | null;
}

export interface AIProviderResponse {
  steps: PlanStep[];
  provider: string;
  timestamp: Date;
}
