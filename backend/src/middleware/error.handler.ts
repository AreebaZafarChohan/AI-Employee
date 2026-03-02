/**
 * Global Error Handling Middleware
 * Catches and formats all errors consistently
 */

import { Request, Response, NextFunction } from 'express';
import { AppError, ValidationError } from '../utils/errors';
import logger from '../utils/logger';
import config from '../config/env';

interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: unknown[];
  };
}

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction
): void {
  // Log the error
  logger.error('Error occurred:', {
    name: err.name,
    message: err.message,
    stack: config.NODE_ENV === 'development' ? err.stack : undefined,
    path: req.path,
    method: req.method,
  });

  // Handle AppError instances
  if (err instanceof AppError) {
    const response: ErrorResponse = {
      error: {
        code: err.code,
        message: err.message,
      },
    };

    // Add validation details if available
    if (err instanceof ValidationError && 'details' in err) {
      response.error.details = (err as ValidationError & { details: unknown[] }).details;
    }

    res.status(err.statusCode).json(response);
    return;
  }

  // Handle Prisma errors
  if (err.name === 'PrismaClientKnownRequestError') {
    const response: ErrorResponse = {
      error: {
        code: 'DATABASE_ERROR',
        message: 'Database operation failed',
      },
    };
    res.status(500).json(response);
    return;
  }

  // Handle unknown errors
  const response: ErrorResponse = {
    error: {
      code: 'INTERNAL_ERROR',
      message: config.NODE_ENV === 'production' ? 'Internal server error' : err.message,
    },
  };

  res.status(500).json(response);
}

export default errorHandler;
