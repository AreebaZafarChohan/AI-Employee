/**
 * System Routes
 * Defines system-level endpoints (health, state)
 */

import { Router } from 'express';
import { systemController } from '../controllers/system.controller';

const router = Router();

/**
 * @route   GET /api/v1/system/state
 * @desc    Get current system state
 * @access  Public
 */
router.get('/state', systemController.getState.bind(systemController));

/**
 * @route   GET /api/v1/system/health
 * @desc    Get system health status
 * @access  Public
 */
router.get('/health', systemController.getHealth.bind(systemController));

export default router;
