import { BaseAgent, AgentResponse } from './base_agent';
import { logger } from '../lib/logger';

export class MemoryAgent extends BaseAgent {
  constructor(model: string = 'gpt-4') {
    super('MemoryRetriever', model);
  }

  async run(taskDescription: string, memoryContexts: string[]): Promise<AgentResponse> {
    logger.info(`MemoryAgent summarizing context for task: ${taskDescription.substring(0, 50)}...`);

    try {
      if (memoryContexts.length === 0) {
        return { content: 'No relevant historical memory found.' };
      }

      // In a real implementation, this would call an LLM with the context and the prompt.
      // Here we simulate the summarization/selection.

      const summary = `Relevant past context includes: ${memoryContexts.join('; ')}`;

      return {
        content: summary,
        thought: 'I have consolidated the relevant memories to provide historical context for this task.',
      };
    } catch (error) {
      logger.error('MemoryAgent recall summary failed', error);
      throw error;
    }
  }
}
