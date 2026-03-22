import { Router, Request, Response } from 'express';
import { CostMonitoringService } from '../services/cost_service';
import { logger } from '../lib/logger';

const router = Router();
const costService = new CostMonitoringService();

// 1. Get Cost Threshold Status
router.get('/threshold', async (_req: Request, res: Response) => {
  try {
    const status = await costService.getStatus();
    res.json(status);
  } catch (error) {
    logger.error('API Error: GET /cost/threshold', error);
    res.status(500).json({ error: 'Failed to fetch cost status' });
  }
});

// 2. Set Cost Threshold
router.post('/threshold', async (req: Request, res: Response) => {
  try {
    const { threshold_usd } = req.body;
    if (typeof threshold_usd !== 'number') {
      return res.status(400).json({ error: 'threshold_usd must be a number' });
    }

    await costService.setThreshold(threshold_usd);
    res.json({ message: 'Cost threshold updated', threshold_usd });
  } catch (error) {
    logger.error('API Error: POST /cost/threshold', error);
    res.status(500).json({ error: 'Failed to update cost threshold' });
  }
});

export default router;
