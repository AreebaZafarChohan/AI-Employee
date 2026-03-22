/**
 * Route Aggregator
 * Combines all API routes under versioned paths
 */

import { Router } from 'express';
import taskRoutes from './task.routes';
import goalRoutes from '../api/goal_routes';
import costRoutes from '../api/cost_routes';
import toolRoutes from '../api/tool_routes';
import metricsRoutes from '../api/metrics_routes';
import planRoutes from './plan.routes';
import activityRoutes from './activity.routes';
import systemRoutes from './system.routes';
import mcpRoutes from './mcp.routes';
import auditRoutes from './audit.routes';
import approvalRoutes from './approval.routes';
import whatsappRoutes from './whatsapp.routes';
import linkedinRoutes from './linkedin.routes';
import filesRoutes from './files.routes';
import vaultRoutes from './vault.routes';
import salesRoutes from './sales.routes';
import watcherRoutes from './watcher.routes';
import aiAgentRoutes from './ai-agent.routes';

const router = Router();

// API v1 routes
const apiV1Router = Router();

// Mount routes
apiV1Router.use('/goals', goalRoutes);
apiV1Router.use('/cost', costRoutes);
apiV1Router.use('/tools', toolRoutes);
apiV1Router.use('/metrics', metricsRoutes);
apiV1Router.use('/tasks', taskRoutes);
apiV1Router.use('/plans', planRoutes);
apiV1Router.use('/activity-logs', activityRoutes);
apiV1Router.use('/system', systemRoutes);
apiV1Router.use('/system', mcpRoutes);
apiV1Router.use('/audit-logs', auditRoutes);
apiV1Router.use('/approvals', approvalRoutes);
apiV1Router.use('/whatsapp', whatsappRoutes);
apiV1Router.use('/linkedin', linkedinRoutes);
apiV1Router.use('/files', filesRoutes);
apiV1Router.use('/vault', vaultRoutes);
apiV1Router.use('/sales', salesRoutes);
apiV1Router.use('/watchers', watcherRoutes);
apiV1Router.use('/ai-agent', aiAgentRoutes);

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
        mcpHealth: '/api/v1/system/mcp-health',
      },
      auditLogs: '/api/v1/audit-logs',
      approvals: '/api/v1/approvals/metrics',
      whatsapp: {
        messages: '/api/v1/whatsapp/messages',
        send: '/api/v1/whatsapp/send',
        status: '/api/v1/whatsapp/status',
      },
      linkedin: {
        connections: '/api/v1/linkedin/connections',
        messages: '/api/v1/linkedin/messages',
        posts: '/api/v1/linkedin/posts',
        status: '/api/v1/linkedin/status',
      },
      sales: {
        leads: '/api/v1/sales/leads',
        pipeline: '/api/v1/sales/pipeline',
        discover: '/api/v1/sales/discover',
        invoices: '/api/v1/sales/invoices',
        payments: '/api/v1/sales/payments',
      },
      files: {
        pending: '/api/v1/files/pending',
        stats: '/api/v1/files/stats',
      },
      watchers: '/api/v1/watchers',
      aiAgent: {
        status: '/api/v1/ai-agent/status',
        generate: '/api/v1/ai-agent/generate',
        post: '/api/v1/ai-agent/post',
        history: '/api/v1/ai-agent/history',
      },
    },
  });
});

export default router;
