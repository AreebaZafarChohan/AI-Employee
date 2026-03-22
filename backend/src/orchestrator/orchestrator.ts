import { PrismaClient } from '@prisma/client';
import { decompositionQueue, executionQueue } from '../workers/queues';
import { MemoryService } from '../services/memory_service';
import { logger } from '../lib/logger';

const prisma = new PrismaClient();

export class Orchestrator {
  private prisma: PrismaClient;
  private memoryService: MemoryService;

  constructor() {
    this.prisma = prisma;
    this.memoryService = new MemoryService();
  }

  async submitGoal(title: string, description: string, priority: number = 1) {
    logger.info(`Orchestrator: Submitting goal: ${title}`);

    // Recall context for planning
    const recalledContext = await this.memoryService.recallContext(description);

    const goal = await this.prisma.goal.create({
      data: {
        title,
        description,
        priority,
        state: 'PENDING_PLAN',
        metadata: { recalledContext },
      },
    });

    // Add to decomposition queue
    await decompositionQueue.add('decompose', { goalId: goal.id });

    return goal;
  }

  async getGoalStatus(goalId: string) {
    return await this.prisma.goal.findUnique({
      where: { id: goalId },
      include: { tasks: true },
    });
  }

  async approvePlan(goalId: string) {
    const goal = await this.prisma.goal.update({
      where: { id: goalId },
      data: { state: 'ACTIVE' },
    });

    // Trigger execution of first set of tasks (those with no dependencies)
    const tasks = await this.prisma.task.findMany({
      where: { goalId, status: 'PENDING' },
      orderBy: { order: 'asc' },
    });

    for (const task of tasks) {
      if (task.dependsOn.length === 0) {
        await executionQueue.add('execute-task', { taskId: task.id });
      }
    }

    return goal;
  }

  async pauseExecution(goalId: string) {
    return await this.prisma.goal.update({
      where: { id: goalId },
      data: { state: 'PAUSED' },
    });
  }
}
