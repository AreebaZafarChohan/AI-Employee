import { Worker, Job } from 'bullmq';
import IORedis from 'ioredis';
import { GoalRepository } from '../models/goal_model';
import { TaskRepository } from '../models/task_model';
import { PlannerAgent } from '../agents/planner_agent';
import { logger } from '../lib/logger';
import dotenv from 'dotenv';

dotenv.config();

const redisUrl = process.env.REDIS_URL || 'redis://localhost:6379';
const connection = new IORedis(redisUrl, { maxRetriesPerRequest: null });

export class DecompositionWorker {
  constructor(
    private goalRepo: GoalRepository = new GoalRepository(),
    private taskRepo: TaskRepository = new TaskRepository(),
    private plannerAgent: PlannerAgent = new PlannerAgent()
  ) {}

  async process(job: Job) {
    const { goalId } = job.data;
    logger.info(`Processing decomposition for goal: ${goalId}`);

    const goal = await this.goalRepo.findById(goalId);
    if (!goal) {
      logger.error(`Goal ${goalId} not found during decomposition`);
      return;
    }

    try {
      // 1. Run PlannerAgent
      const response = await this.plannerAgent.run(goal.description || goal.title);

      // 2. Parse Tasks
      const tasks = this.plannerAgent.parseTasks(response.content);

      // 3. Store Tasks
      const formattedTasks = tasks.map((t: any) => ({
        goalId: goal.id,
        title: t.title,
        description: t.description,
        order: t.order,
        dependsOn: t.dependsOn || [],
        assignedAgent: t.assignedAgent,
      }));

      await this.taskRepo.createMany(formattedTasks);

      // 4. Update Goal State
      await this.goalRepo.updateState(goalId, 'PENDING_APPROVAL');

      logger.info(`Decomposition complete for goal: ${goalId}. Tasks created: ${tasks.length}`);
    } catch (error) {
      logger.error(`Failed to decompose goal: ${goalId}`, error);
      throw error;
    }
  }
}

// Start worker
const decompositionProcessor = new DecompositionWorker();
const worker = new Worker('decomposition', (job) => decompositionProcessor.process(job), {
  connection: connection as any,
});

worker.on('completed', (job) => {
  logger.info(`Decomposition job ${job.id} completed`);
});

worker.on('failed', (job, err) => {
  logger.error(`Decomposition job ${job?.id} failed`, err);
});
