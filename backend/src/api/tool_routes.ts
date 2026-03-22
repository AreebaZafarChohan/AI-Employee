import { Router, Request, Response } from 'express';
import { ToolManager } from '../services/tool_service';
import { logger } from '../lib/logger';

const router = Router();
const toolManager = new ToolManager();

// 1. Get Pending Tool Approvals
router.get('/approvals', async (_req: Request, res: Response) => {
  try {
    const { ToolRepository } = require('../models/tool_model');
    const repo = new ToolRepository();
    const pending = await repo.getPendingApprovals();
    res.json(pending);
  } catch (error) {
    logger.error('API Error: GET /tools/approvals', error);
    res.status(500).json({ error: 'Failed to fetch pending tool approvals' });
  }
});

// 2. Approve Tool Invocation
router.post('/approvals/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { action } = req.body;

    if (action === 'REJECT') {
      const { ToolRepository } = require('../models/tool_model');
      const repo = new ToolRepository();
      await repo.updateStatus(id, 'REJECTED');
      return res.json({ message: 'Tool invocation rejected' });
    }

    if (action !== 'APPROVE') {
      return res.status(400).json({ error: 'Action must be APPROVE or REJECT' });
    }

    const result = await toolManager.approveTool(id);
    res.json(result);
  } catch (error) {
    logger.error(`API Error: POST /tools/approvals/${req.params.id}`, error);
    res.status(500).json({ error: 'Failed to approve tool invocation' });
  }
});

export default router;
