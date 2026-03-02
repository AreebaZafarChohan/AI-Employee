/**
 * Plan Routes
 * Defines all plan-related endpoints
 */

import { Router } from 'express';
import { planController } from '../controllers/plan.controller';
import { validateRequest } from '../middleware/validation';
import { PlanStatusUpdateSchema } from '../validators/plan.validator';

const router = Router();

/**
 * @route   POST /api/v1/tasks/:taskId/plans
 * @desc    Generate a plan for a task
 * @access  Public
 */
router.post(
  '/tasks/:taskId/plans',
  planController.generatePlan.bind(planController)
);

/**
 * @route   GET /api/v1/plans
 * @desc    List all plans
 * @access  Public
 */
router.get('/', planController.listPlans.bind(planController));

/**
 * @route   GET /api/v1/plans/:id
 * @desc    Get plan by ID
 * @access  Public
 */
router.get('/:id', planController.getPlan.bind(planController));

/**
 * @route   PATCH /api/v1/plans/:id/status
 * @desc    Update plan status
 * @access  Public
 */
router.patch(
  '/:id/status',
  validateRequest(PlanStatusUpdateSchema),
  planController.updatePlanStatus.bind(planController)
);

/**
 * @route   DELETE /api/v1/plans/:id
 * @desc    Delete plan
 * @access  Public
 */
router.delete('/:id', planController.deletePlan.bind(planController));

export default router;
