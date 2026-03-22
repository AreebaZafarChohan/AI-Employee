import { Request, Response, NextFunction } from 'express';
import { logger } from '../lib/logger';

export const errorHandler = (err: any, req: Request, res: Response, _next: NextFunction) => {
  const status = err.status || 500;
  const message = err.message || 'Internal Server Error';

  logger.error('Unhandled Exception', err, {
    url: req.url,
    method: req.method,
    status,
  });

  res.status(status).json({
    status: 'ERROR',
    message,
    ...(process.env.NODE_ENV === 'development' ? { stack: err.stack } : {}),
  });
};
