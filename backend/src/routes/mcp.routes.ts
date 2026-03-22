/**
 * MCP Routes — Silver Tier
 */

import { Router } from 'express';
import { mcpController } from '../controllers/mcp.controller';

const router = Router();

/**
 * @route   GET /api/v1/system/mcp-health
 * @desc    Get MCP server health status
 */
router.get('/mcp-health', mcpController.getMcpHealth.bind(mcpController));

export default router;
