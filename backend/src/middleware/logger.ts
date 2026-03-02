/**
 * Request Logging Middleware
 * Logs all incoming requests with timing information
 */

import { Request, Response, NextFunction } from 'express';
import logger from '../utils/logger';

interface RequestWithStartTime extends Request {
  startTime?: number;
}

export function requestLogger(req: RequestWithStartTime, res: Response, next: NextFunction): void {
  req.startTime = Date.now();

  // Log when response finishes
  res.on('finish', () => {
    const duration = req.startTime ? Date.now() - req.startTime : 0;
    logger.info('Request completed:', {
      method: req.method,
      path: req.path,
      status: res.statusCode,
      duration: `${duration}ms`,
      ip: req.ip,
    });
  });

  next();
}

export default requestLogger;
