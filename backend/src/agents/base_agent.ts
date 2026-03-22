import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export interface AgentResponse {
  content: string;
  thought?: string;
  usage?: {
    promptTokens: number;
    completionTokens: number;
    totalTokens: number;
  };
}

export abstract class BaseAgent {
  protected name: string;
  protected model: string;

  constructor(name: string, model: string = 'gpt-4') {
    this.name = name;
    this.model = model;
  }

  abstract run(input: string, context?: any): Promise<AgentResponse>;

  protected async logExecution(taskId: string, reasoning: string, output: string, status: 'SUCCESS' | 'FAILURE') {
    return await prisma.agentExecution.create({
      data: {
        taskId,
        agentName: this.name,
        reasoning,
        output,
        status,
      },
    });
  }

  getName(): string {
    return this.name;
  }
}
