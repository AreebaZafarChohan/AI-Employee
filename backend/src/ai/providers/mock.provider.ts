/**
 * Mock AI Provider
 * Used for testing and development when no AI API key is configured
 */

import AIProvider from '../provider';
import { TaskContext, PlanStep } from '../types';

export class MockAIProvider implements AIProvider {
  getName(): string {
    return 'mock';
  }

  async generatePlan(_task: TaskContext): Promise<PlanStep[]> {
    // Simulate AI delay
    await new Promise((resolve) => setTimeout(resolve, 500));

    return [
      {
        title: 'Analyze the task requirements',
        description: 'Break down the task into key components and understand the goals',
        estimatedDuration: 15,
      },
      {
        title: 'Research and gather information',
        description: 'Collect necessary resources and information to complete the task',
        estimatedDuration: 30,
      },
      {
        title: 'Create implementation plan',
        description: 'Define specific steps and approach for completing the task',
        estimatedDuration: 20,
      },
      {
        title: 'Execute the plan',
        description: 'Implement the solution following the defined steps',
        estimatedDuration: 60,
      },
      {
        title: 'Review and validate',
        description: 'Verify the results meet the requirements and quality standards',
        estimatedDuration: 15,
      },
    ];
  }
}
