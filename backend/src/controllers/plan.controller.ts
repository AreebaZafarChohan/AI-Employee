/**
 * Plan Controller
 * HTTP request handlers for plan endpoints
 */

import { Request, Response, NextFunction } from 'express';
import { planService } from '../services/plan.service';
import { PlanStatusUpdateInput } from '../validators/plan.validator';
import { Plan } from '@prisma/client';

/**
 * Map backend PascalCase status to frontend kebab-case
 */
function mapPlanStatus(status: string): string {
  const mapping: Record<string, string> = {
    'Draft': 'draft',
    'Active': 'active',
    'Completed': 'completed',
    'Archived': 'archived',
  };
  return mapping[status] ?? status.toLowerCase();
}

/**
 * Map backend plan to frontend shape with converted status
 */
function mapPlanForResponse(plan: Plan): Record<string, unknown> {
  const { status, ...rest } = plan as unknown as Plan & { status: string };
  return {
    ...rest,
    status: mapPlanStatus(status),
  };
}

export class PlanController {
  /**
   * Generate a plan for a task
   * POST /api/v1/tasks/:taskId/plans
   */
  async generatePlan(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { taskId } = req.params;
      const plan = await planService.generatePlan(taskId);

      res.status(201).json({
        data: mapPlanForResponse(plan),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Get plan by ID
   * GET /api/v1/plans/:id
   */
  async getPlan(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const plan = await planService.getPlan(id);

      res.status(200).json({
        data: mapPlanForResponse(plan),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * List all plans
   * GET /api/v1/plans
   */
  async listPlans(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { status, page, pageSize } = req.query;
      const result = await planService.getPlans({
        status: status as 'Draft' | 'Active' | 'Completed' | 'Archived',
        page: Number(page),
        pageSize: Number(pageSize),
      });

      res.status(200).json({
        data: result.plans.map(mapPlanForResponse),
        meta: {
          total: result.total,
          page: page ? Number(page) : 1,
          pageSize: pageSize ? Number(pageSize) : 20,
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Update plan status
   * PATCH /api/v1/plans/:id/status
   */
  async updatePlanStatus(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      const { status } = req.body as PlanStatusUpdateInput;
      const plan = await planService.updatePlanStatus(id, status as 'Draft' | 'Active' | 'Completed' | 'Archived');

      res.status(200).json({
        data: mapPlanForResponse(plan),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Delete plan
   * DELETE /api/v1/plans/:id
   */
  async deletePlan(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { id } = req.params;
      await planService.deletePlan(id);

      res.status(204).send();
    } catch (error) {
      next(error);
    }
  }
}

export const planController = new PlanController();
export default planController;
