/**
 * Files Routes
 * Defines all file-related endpoints for vault management
 */

import { Router } from 'express';
import { filesController } from '../controllers/files.controller';

const router = Router();

/**
 * @route   GET /api/v1/files/pending
 * @desc    Get all pending files from Pending_Approval
 * @access  Public
 */
router.get('/pending', filesController.getPending.bind(filesController));

/**
 * @route   GET /api/v1/files/stats
 * @desc    Get file statistics across all folders
 * @access  Public
 */
router.get('/stats', filesController.getStats.bind(filesController));

/**
 * @route   GET /api/v1/files/:path
 * @desc    Get specific file details
 * @access  Public
 */
router.get('/:path', filesController.getFile.bind(filesController));

/**
 * @route   POST /api/v1/files/:path/approve
 * @desc    Approve a file (move to Approved)
 * @access  Public
 */
router.post('/:path/approve', filesController.approve.bind(filesController));

/**
 * @route   POST /api/v1/files/reject
 * @desc    Reject a file (move to Rejected)
 * @access  Public
 */
router.post('/reject', filesController.reject.bind(filesController));

export default router;
