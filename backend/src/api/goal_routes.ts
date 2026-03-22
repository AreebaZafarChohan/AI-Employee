import { Router, Request, Response } from 'express';
import { GoalService } from '../services/goal_service';
import { logger } from '../lib/logger';

const router = Router();
const goalService = new GoalService();

// 1. Submit a Goal
router.post('/goals', async (req: Request, res: Response): Promise<void> => {
  try {
    const { title, description, priority } = req.body;
    if (!title) {
      res.status(400).json({ error: 'Title is required' });
      return;
    }

    const goal = await goalService.submitGoal({ title, description, priority });
    res.status(201).json(goal);
  } catch (error) {
    logger.error('API Error: POST /goals', error);
    res.status(500).json({ error: 'Failed to submit goal' });
  }
});

// 2. Get Goal Plan (Tasks)
router.get('/goals/:id/plan', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const goal = await goalService.getGoalPlan(id);
    res.json(goal);
  } catch (error) {
    logger.error(`API Error: GET /goals/${req.params.id}/plan`, error);
    res.status(404).json({ error: 'Goal not found' });
  }
});

// 3. Approve Plan
router.post('/goals/:id/plan', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const { action } = req.body;

    if (action !== 'APPROVE') {
      return res.status(400).json({ error: 'Only APPROVE action is supported currently' });
    }

    const goal = await goalService.approvePlan(id);
    res.json({ message: 'Plan approved and execution started', goal });
  } catch (error) {
    logger.error(`API Error: POST /goals/${req.params.id}/plan`, error);
    res.status(500).json({ error: 'Failed to approve plan' });
  }
});

// 4. Get Goal Status
router.get('/goals/:id', async (req: Request, res: Response) => {
  try {
    const { id } = req.params;
    const goal = await goalService.getGoalStatus(id);
    if (!goal) return res.status(404).json({ error: 'Goal not found' });
    res.json(goal);
  } catch (error) {
    logger.error(`API Error: GET /goals/${req.params.id}`, error);
    res.status(500).json({ error: 'Failed to fetch goal status' });
  }
});

export default router;
