/**
 * Watcher Routes
 */
import { Router } from 'express';
import { watcherController } from '../controllers/watcher.controller';

const router = Router();

router.get('/', (req, res) => watcherController.getWatchers(req, res));
router.get('/:id/logs', (req, res) => watcherController.getWatcherLogs(req, res));
router.post('/:id/start', (req, res) => watcherController.startWatcher(req, res));
router.post('/start-all', (req, res) => watcherController.startAll(req, res));

export default router;
