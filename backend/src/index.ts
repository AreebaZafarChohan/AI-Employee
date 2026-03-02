/**
 * Application Entry Point
 * Starts the Express server
 */

import { createApp } from './app';
import config from './config/env';
import logger from './utils/logger';
import { prisma } from './models';

async function bootstrap() {
  const app = createApp();

  try {
    // Test database connection
    await prisma.$connect();
    logger.info('Database connected successfully');

    // Start server
    app.listen(config.PORT, config.HOST, () => {
      logger.info(`Server running on http://${config.HOST}:${config.PORT}`);
      logger.info(`Environment: ${config.NODE_ENV}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', { error });
    process.exit(1);
  }
}

// Handle graceful shutdown
process.on('SIGINT', async () => {
  logger.info('Shutting down gracefully...');
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  logger.info('Shutting down gracefully...');
  await prisma.$disconnect();
  process.exit(0);
});

// Start application
bootstrap();
