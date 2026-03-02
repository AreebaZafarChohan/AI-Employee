/**
 * Express App Configuration
 * Configures and exports the Express application
 */

import express, { Application } from 'express';
import cors from 'cors';
import { getCorsOptions } from './config/cors';
import { requestLogger, errorHandler } from './middleware';
import routes from './routes';

export function createApp(): Application {
  const app = express();

  // CORS configuration
  app.use(cors(getCorsOptions()));

  // Body parsing middleware
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  // Request logging
  app.use(requestLogger);

  // API routes
  app.use(routes);

  // 404 handler for unknown routes
  app.use((_req, res) => {
    res.status(404).json({
      error: {
        code: 'NOT_FOUND',
        message: 'Route not found',
      },
    });
  });

  // Global error handler
  app.use(errorHandler);

  return app;
}

export default createApp;
