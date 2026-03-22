import { PrismaClient } from '@prisma/client';
import { Decimal } from '@prisma/client/runtime/library';

const prisma = new PrismaClient();

export class CostRepository {
  async create(data: { agentExecutionId?: string; modelName: string; tokensIn: number; tokensOut: number; estimatedCostUsd: number }) {
    return await prisma.costLog.create({
      data: {
        agentExecutionId: data.agentExecutionId,
        modelName: data.modelName,
        tokensIn: data.tokensIn,
        tokensOut: data.tokensOut,
        estimatedCostUsd: new Decimal(data.estimatedCostUsd),
      },
    });
  }

  async getTotalCost() {
    const result = await prisma.costLog.aggregate({
      _sum: {
        estimatedCostUsd: true,
      },
    });
    return result._sum.estimatedCostUsd || new Decimal(0);
  }

  async getThreshold() {
    const state = await prisma.systemState.findUnique({
      where: { id: 'cost_threshold' },
    });
    return state ? parseFloat(state.state) : 0;
  }

  async setThreshold(threshold: number) {
    return await prisma.systemState.upsert({
      where: { id: 'cost_threshold' },
      update: { state: threshold.toString(), lastActivity: new Date() },
      create: { id: 'cost_threshold', state: threshold.toString(), lastActivity: new Date() },
    });
  }
}
