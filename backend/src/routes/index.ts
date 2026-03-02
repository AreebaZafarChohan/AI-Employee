/**
 * Route Aggregator
 * Combines all API routes under versioned paths
 */

import { Router } from 'express';
import taskRoutes from './task.routes';
import planRoutes from './plan.routes';
import activityRoutes from './activity.routes';
import systemRoutes from './system.routes';

const router = Router();

// API v1 routes
const apiV1Router = Router();

// Mount routes
apiV1Router.use('/tasks', taskRoutes);
apiV1Router.use('/plans', planRoutes);
apiV1Router.use('/activity-logs', activityRoutes);
apiV1Router.use('/system', systemRoutes);

// Mount versioned API
router.use('/api/v1', apiV1Router);

// Root route
router.get('/', (_req, res) => {
  res.json({
    name: 'AI Employee Backend API',
    version: 'v1',
    endpoints: {
      tasks: '/api/v1/tasks',
      plans: '/api/v1/plans',
      activityLogs: '/api/v1/activity-logs',
      system: {
        state: '/api/v1/system/state',
        health: '/api/v1/system/health',
      },
    },
  });
});

export default router;
