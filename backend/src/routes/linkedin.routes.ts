/**
 * LinkedIn Routes
 * Defines all LinkedIn-related endpoints
 */

import { Router } from 'express';
import { linkedInController } from '../controllers/linkedin.controller';

const router = Router();

/**
 * @route   GET /api/v1/linkedin/connections
 * @desc    Get LinkedIn connections
 * @access  Public
 */
router.get('/connections', linkedInController.getConnections.bind(linkedInController));

/**
 * @route   GET /api/v1/linkedin/messages
 * @desc    Get LinkedIn messages
 * @access  Public
 */
router.get('/messages', linkedInController.getMessages.bind(linkedInController));

/**
 * @route   GET /api/v1/linkedin/posts
 * @desc    Get LinkedIn posts
 * @access  Public
 */
router.get('/posts', linkedInController.getPosts.bind(linkedInController));

/**
 * @route   POST /api/v1/linkedin/posts
 * @desc    Create/schedule a LinkedIn post
 * @access  Public
 */
router.post('/posts', linkedInController.createPost.bind(linkedInController));

/**
 * @route   GET /api/v1/linkedin/status
 * @desc    Get LinkedIn service status
 * @access  Public
 */
router.get('/status', linkedInController.getStatus.bind(linkedInController));

export default router;
