import { Router, Request, Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { logger } from '../lib/logger';

const router = Router();
const prisma = new PrismaClient();

router.get('/metrics', async (_req: Request, res: Response) => {
  try {
    const goalCount = await prisma.goal.count();
    const taskCount = await prisma.task.count();
    const executionCount = await prisma.agentExecution.count();

    const goalsByState = await prisma.goal.groupBy({
      by: ['state'],
      _count: true,
    });

    const tasksByStatus = await prisma.task.groupBy({
      by: ['status'],
      _count: true,
    });

    res.json({
      summary: {
        goals: goalCount,
        tasks: taskCount,
        executions: executionCount,
      },
      goalsByState,
      tasksByStatus,
    });
  } catch (error) {
    logger.error('API Error: GET /metrics', error);
    res.status(500).json({ error: 'Failed to fetch metrics' });
  }
});

export default router;
