/**
 * AI Provider Factory
 * Creates AI provider instances based on configuration
 */

import AIProvider from './provider';
import { TaskContext, PlanStep } from './types';
import { MockAIProvider } from './providers/mock.provider';
import config from '../config/env';

/**
 * Anthropic AI Provider
 * Uses Claude API for plan generation
 */
class AnthropicAIProvider implements AIProvider {
  constructor(private apiKey: string) {}

  getName(): string {
    return 'anthropic';
  }

  async generatePlan(task: TaskContext): Promise<PlanStep[]> {
    // TODO: Implement actual Anthropic API call
    // For now, return mock data
    console.log('Anthropic AI would generate plan for:', task.title, 'API key:', this.apiKey ? 'set' : 'not set');

    return [
      {
        title: 'Understand task requirements',
        description: `Analyze: ${task.title}${task.description ? ` - ${task.description}` : ''}`,
        estimatedDuration: 15,
      },
      {
        title: 'Plan approach',
        description: 'Define the strategy and steps needed',
        estimatedDuration: 20,
      },
      {
        title: 'Execute',
        description: 'Implement the solution',
        estimatedDuration: 60,
      },
    ];
  }
}

/**
 * Create AI Provider based on configuration
 */
export function createAIProvider(): AIProvider {
  const providerType = config.AI_PROVIDER;

  switch (providerType) {
    case 'anthropic':
      if (!config.AI_API_KEY) {
        console.warn('Anthropic API key not set, falling back to mock provider');
        return new MockAIProvider();
      }
      return new AnthropicAIProvider(config.AI_API_KEY);
    default:
      console.warn(`Unknown AI provider "${providerType}", using mock provider`);
      return new MockAIProvider();
  }
}

export { MockAIProvider };
export default createAIProvider;
