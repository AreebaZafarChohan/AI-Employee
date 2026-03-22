/**
 * Plan Service
 * Business logic for plan management and AI-powered plan generation
 */

import { prisma } from '../models';
import type { PlanWithSteps } from '../models/plan.model';
import type { PlanStatus } from '../models/plan.model';
import { NotFoundError, ServiceUnavailableError } from '../utils/errors';
import logger from '../utils/logger';
import { createAIProvider, TaskContext } from '../ai';
import { taskService } from './task.service';

export class PlanService {
  /**
   * Generate a plan for a task using AI
   */
  async generatePlan(taskId: string): Promise<PlanWithSteps> {
    // Verify task exists
    const task = await taskService.getTask(taskId);

    // Check if plan already exists
    const existingPlan = await prisma.plan.findUnique({
      where: { taskId },
    });

    if (existingPlan) {
      throw new Error('Plan already exists for this task');
    }

    // Get AI provider
    const aiProvider = createAIProvider();

    try {
      // Prepare task context for AI
      const taskContext: TaskContext = {
        id: task.id,
        title: task.title,
        description: task.description,
      };

      logger.info('Generating plan with AI:', { provider: aiProvider.getName(), taskId });

      // Log AI invocation
      await this.logActivity('ai.invoked', `AI plan generation started for task: ${task.title}`, {
        taskId,
        provider: aiProvider.getName(),
      });

      // Generate plan steps via AI
      const steps = await aiProvider.generatePlan(taskContext);

      logger.info('AI plan generated:', { taskId, stepCount: steps.length });

      // Log AI completion
      await this.logActivity('ai.completed', `AI plan generation completed for task: ${task.title}`, {
        taskId,
        stepCount: steps.length,
      });

      // Create plan with steps
      const plan = await prisma.plan.create({
        data: {
          taskId,
          status: 'Active',
          steps: {
            create: steps.map((step, index) => ({
              order: index + 1,
              title: step.title,
              description: step.description,
              estimatedDuration: step.estimatedDuration,
              completed: false,
            })),
          },
        },
        include: {
          steps: {
            orderBy: { order: 'asc' },
          },
        },
      });

      logger.info('Plan created:', { planId: plan.id, taskId });
      await this.logActivity('plan.generated', `Plan generated for task: ${task.title}`, {
        planId: plan.id,
        taskId,
        stepCount: steps.length,
      });

      return plan as PlanWithSteps;
    } catch (error) {
      logger.error('AI plan generation failed:', { taskId, error });

      await this.logActivity('ai.failed', `AI plan generation failed for task: ${task.title}`, {
        taskId,
        error: error instanceof Error ? error.message : 'Unknown error',
      });

      throw new ServiceUnavailableError('AI service is temporarily unavailable');
    }
  }

  /**
   * Get plan by ID with steps
   */
  async getPlan(id: string): Promise<PlanWithSteps> {
    const plan = await prisma.plan.findUnique({
      where: { id },
      include: {
        steps: {
          orderBy: { order: 'asc' },
        },
      },
    });

    if (!plan) {
      throw new NotFoundError('Plan');
    }

    return plan as PlanWithSteps;
  }

  /**
   * Get plan by task ID
   */
  async getPlanByTask(taskId: string): Promise<PlanWithSteps | null> {
    const plan = await prisma.plan.findUnique({
      where: { taskId },
      include: {
        steps: {
          orderBy: { order: 'asc' },
        },
      },
    });

    return plan as PlanWithSteps | null;
  }

  /**
   * Get all plans with optional filtering
   */
  async getPlans(filters?: {
    status?: PlanStatus;
    page?: number;
    pageSize?: number;
  }): Promise<{ plans: PlanWithSteps[]; total: number; page: number; pageSize: number }> {
    const { status, page = 1, pageSize = 20 } = filters || {};

    const where = status ? { status } : {};

    const [plans, total] = await Promise.all([
      prisma.plan.findMany({
        where,
        include: {
          steps: {
            orderBy: { order: 'asc' },
          },
          task: {
            select: { title: true },
          },
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * pageSize,
        take: pageSize,
      }),
      prisma.plan.count({ where }),
    ]);

    // Add task title to plans
    const plansWithTaskTitle = plans.map((p) => ({
      ...p,
      taskTitle: p.task?.title || 'Unknown',
    })) as unknown as PlanWithSteps[];

    return { plans: plansWithTaskTitle, total, page, pageSize };
  }

  /**
   * Update plan status
   */
  async updatePlanStatus(id: string, newStatus: PlanStatus): Promise<PlanWithSteps> {
    // Verify plan exists
    await this.getPlan(id);

    const plan = await prisma.plan.update({
      where: { id },
      data: { status: newStatus },
      include: {
        steps: {
          orderBy: { order: 'asc' },
        },
      },
    });

    logger.info('Plan status updated:', { planId: id, newStatus });
    await this.logActivity('plan.updated', `Plan status updated to ${newStatus}`, {
      planId: id,
      newStatus,
    });

    return plan as PlanWithSteps;
  }

  /**
   * Delete plan
   */
  async deletePlan(id: string): Promise<void> {
    // Verify plan exists
    const plan = await this.getPlan(id);

    await prisma.plan.delete({
      where: { id },
    });

    logger.info('Plan deleted:', { planId: id });
    await this.logActivity('plan.deleted', `Plan deleted`, { planId: id, taskId: plan.taskId });
  }

  /**
   * Log activity for plan operations
   */
  private async logActivity(
    type: string,
    description: string,
    metadata?: Record<string, unknown>
  ): Promise<void> {
    try {
      await prisma.activityLog.create({
        data: {
          type,
          description,
          metadata: metadata ? JSON.parse(JSON.stringify(metadata)) : undefined,
        },
      });
    } catch (error) {
      logger.warn('Failed to log activity:', { type, error });
    }
  }
}

export const planService = new PlanService();
export default planService;
