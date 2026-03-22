/**
 * Audit Log Routes — Silver Tier
 */

import { Router } from 'express';
import { auditController } from '../controllers/audit.controller';

const router = Router();

/**
 * @route   GET /api/v1/audit-logs
 * @desc    Get audit log entries from vault
 */
router.get('/', auditController.getAuditLogs.bind(auditController));

export default router;
