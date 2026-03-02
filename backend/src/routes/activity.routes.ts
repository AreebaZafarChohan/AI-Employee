/**
 * Activity Log Routes
 * Defines all activity log endpoints
 */

import { Router } from 'express';
import { activityLogController } from '../controllers/activity.controller';

const router = Router();

/**
 * @route   GET /api/v1/activity-logs
 * @desc    List activity logs with optional filtering
 * @access  Public
 */
router.get('/', activityLogController.listActivityLogs.bind(activityLogController));

/**
 * @route   POST /api/v1/activity-logs
 * @desc    Create a new activity log entry (used by external watchers/scripts)
 * @access  Public
 */
router.post('/', activityLogController.createActivityLog.bind(activityLogController));

export default router;
