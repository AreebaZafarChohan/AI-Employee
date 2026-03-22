import { BaseAgent, AgentResponse } from './base_agent';
import { logger } from '../lib/logger';

export class PlannerAgent extends BaseAgent {
  constructor(model: string = 'gpt-4') {
    super('Planner', model);
  }

  async run(goalDescription: string): Promise<AgentResponse> {
    logger.info(`PlannerAgent starting decomposition for goal: ${goalDescription.substring(0, 50)}...`);

    // In a real implementation, this would call an LLM API
    // For this prototype, we'll simulate a response or use a dummy JSON
    // based on the PLANNER_PROMPT requirements.

    try {
      // Simulate LLM Call
      const simulatedResponse = {
        tasks: [
          {
            title: 'Initial Research',
            description: `Research about ${goalDescription}`,
            order: 0,
            dependsOn: [],
            assignedAgent: 'Researcher',
          },
          {
            title: 'Content Drafting',
            description: 'Draft the initial version based on research results.',
            order: 1,
            dependsOn: [0],
            assignedAgent: 'DraftingAgent',
          },
          {
            title: 'Final Review',
            description: 'Review and polish the final content.',
            order: 2,
            dependsOn: [1],
            assignedAgent: 'ReviewerAgent',
          },
        ],
      };

      const content = JSON.stringify(simulatedResponse);

      return {
        content,
        thought: 'I have decomposed the goal into three sequential tasks based on common project management patterns.',
        usage: {
          promptTokens: 150,
          completionTokens: 200,
          totalTokens: 350,
        },
      };
    } catch (error) {
      logger.error('PlannerAgent decomposition failed', error);
      throw error;
    }
  }

  parseTasks(responseContent: string): any[] {
    try {
      const data = JSON.parse(responseContent);
      return data.tasks || [];
    } catch (error) {
      logger.error('Failed to parse tasks from PlannerAgent response', error);
      return [];
    }
  }
}
