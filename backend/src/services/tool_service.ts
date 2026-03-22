import { ToolRepository } from '../models/tool_model';
import { RiskAssessmentAgent } from '../agents/risk_agent';
import { logger } from '../lib/logger';

export class ToolManager {
  constructor(
    private toolRepo: ToolRepository = new ToolRepository(),
    private riskAgent: RiskAssessmentAgent = new RiskAssessmentAgent()
  ) {}

  async requestToolExecution(agentExecutionId: string, toolName: string, args: any) {
    logger.info(`Requesting execution for tool: ${toolName}`);

    // 1. Assess Risk
    const assessmentRes = await this.riskAgent.run(toolName, args);
    const assessment = this.riskAgent.parseResult(assessmentRes.content);

    // 2. Log Tool Invocation
    const invocation = await this.toolRepo.create({
      agentExecutionId,
      toolName,
      arguments: args,
      riskScore: assessment.riskScore,
    });

    if (assessment.requiresApproval) {
      logger.warn(`Tool ${toolName} requires human approval (Risk Score: ${assessment.riskScore})`);
      return { status: 'PENDING_APPROVAL', invocationId: invocation.id };
    }

    // 3. Execute Tool (Simulation)
    const result = await this.executeTool(toolName, args);
    await this.toolRepo.updateStatus(invocation.id, 'EXECUTED', result);

    return { status: 'EXECUTED', result, invocationId: invocation.id };
  }

  async approveTool(invocationId: string) {
    const invocation = await this.toolRepo.findById(invocationId);
    if (!invocation) throw new Error('Tool invocation not found');

    logger.info(`Approving tool invocation: ${invocation.toolName}`);

    // Execute Tool (Simulation)
    const result = await this.executeTool(invocation.toolName, invocation.arguments);
    await this.toolRepo.updateStatus(invocationId, 'EXECUTED', result);

    return { status: 'EXECUTED', result };
  }

  private async executeTool(toolName: string, _args: any) {
    // In a real implementation, this would call the MCP bridge or the actual tool.
    logger.info(`Executing tool: ${toolName}`);
    return { success: true, data: `Mock result for ${toolName}` };
  }
}
