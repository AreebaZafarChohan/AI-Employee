/**
 * Approval Routes — Silver Tier
 */

import { Router } from 'express';
import { approvalController } from '../controllers/approval.controller';

const router = Router();

/**
 * @route   GET /api/v1/approvals/metrics
 * @desc    Get pending approval metrics
 */
router.get('/metrics', approvalController.getMetrics.bind(approvalController));

export default router;
