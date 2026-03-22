/**
 * AI Agent Routes
 */
import { Router } from 'express';
import { aiAgentController } from '../controllers/ai-agent.controller';

const router = Router();

router.get('/status', (req, res) => aiAgentController.getStatus(req, res));
router.post('/generate', (req, res) => aiAgentController.generateContent(req, res));
router.post('/post', (req, res) => aiAgentController.postContent(req, res));
router.get('/history', (req, res) => aiAgentController.getHistory(req, res));

export default router;
