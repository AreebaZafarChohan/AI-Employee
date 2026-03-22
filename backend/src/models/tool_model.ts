import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export class ToolRepository {
  async create(data: { agentExecutionId: string; toolName: string; arguments: any; riskScore?: number }) {
    return await prisma.toolInvocation.create({
      data: {
        agentExecutionId: data.agentExecutionId,
        toolName: data.toolName,
        arguments: data.arguments,
        riskScore: data.riskScore,
        status: data.riskScore && data.riskScore > 0.7 ? 'PENDING_APPROVAL' : 'EXECUTED',
      },
    });
  }

  async updateStatus(id: string, status: string, result?: any) {
    return await prisma.toolInvocation.update({
      where: { id },
      data: { status, result },
    });
  }

  async getPendingApprovals() {
    return await prisma.toolInvocation.findMany({
      where: { status: 'PENDING_APPROVAL' },
    });
  }

  async findById(id: string) {
    return await prisma.toolInvocation.findUnique({
      where: { id },
    });
  }
}
