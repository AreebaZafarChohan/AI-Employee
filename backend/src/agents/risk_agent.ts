import { BaseAgent, AgentResponse } from './base_agent';
import { logger } from '../lib/logger';

export class RiskAssessmentAgent extends BaseAgent {
  constructor(model: string = 'gpt-4') {
    super('RiskAssessor', model);
  }

  async run(toolName: string, _args: any): Promise<AgentResponse> {
    logger.info(`RiskAssessmentAgent evaluating tool: ${toolName}`);

    try {
      // In a real implementation, this would call an LLM with the prompt and tool details.
      // Here we simulate the risk scoring based on tool names.

      let riskScore = 0.1;
      let reasoning = 'Read-only operation.';

      if (toolName.includes('delete') || toolName.includes('write') || toolName.includes('send')) {
        riskScore = 0.8;
        reasoning = 'State-changing or external communication operation detected.';
      } else if (toolName.includes('update') || toolName.includes('edit')) {
        riskScore = 0.5;
        reasoning = 'State-changing but likely reversible.';
      }

      const content = JSON.stringify({
        riskScore,
        reasoning,
        requiresApproval: riskScore > 0.7,
      });

      return {
        content,
        thought: 'I have evaluated the risk based on the tool name and standard safety heuristics.',
      };
    } catch (error) {
      logger.error('RiskAssessmentAgent evaluation failed', error);
      throw error;
    }
  }

  parseResult(responseContent: string): { riskScore: number; requiresApproval: boolean; reasoning: string } {
    try {
      return JSON.parse(responseContent);
    } catch (error) {
      logger.error('Failed to parse RiskAssessmentAgent response', error);
      return { riskScore: 1.0, requiresApproval: true, reasoning: 'Parsing failed, defaulting to high risk.' };
    }
  }
}
