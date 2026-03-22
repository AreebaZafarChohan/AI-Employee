import { GoalRepository } from '../models/goal_model';
import { TaskRepository } from '../models/task_model';
import { decompositionQueue, executionQueue } from '../workers/queues';
import { logger } from '../lib/logger';

export class GoalService {
  constructor(
    private goalRepo: GoalRepository = new GoalRepository(),
    private taskRepo: TaskRepository = new TaskRepository()
  ) {}

  async submitGoal(data: { title: string; description?: string; priority?: number }) {
    logger.info(`Submitting goal: ${data.title}`);
    const goal = await this.goalRepo.create(data);

    // Add to decomposition queue
    await decompositionQueue.add('decompose', { goalId: goal.id });

    return goal;
  }

  async getGoalPlan(goalId: string) {
    const goal = await this.goalRepo.findById(goalId);
    if (!goal) throw new Error('Goal not found');
    return goal;
  }

  async approvePlan(goalId: string) {
    logger.info(`Approving plan for goal: ${goalId}`);
    const goal = await this.goalRepo.updateState(goalId, 'ACTIVE');

    // Start executing tasks with no dependencies
    const tasks = await this.taskRepo.findByGoalId(goalId);
    for (const task of tasks) {
      if (!task.dependsOn || task.dependsOn.length === 0) {
        await executionQueue.add('execute-task', { taskId: task.id });
      }
    }

    return goal;
  }

  async getGoalStatus(goalId: string) {
    return await this.goalRepo.findById(goalId);
  }
}
