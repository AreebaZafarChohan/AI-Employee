/**
 * Activity Log Controller
 * HTTP request handlers for activity log endpoints
 */

import { Request, Response, NextFunction } from 'express';
import { activityLogService } from '../services/activity-log.service';

export class ActivityLogController {
  /**
   * List activity logs
   * GET /api/v1/activity-logs
   */
  async listActivityLogs(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { type, startTime, endTime, page, pageSize } = req.query;

      const filters: Record<string, unknown> = {
        page: page ? Number(page) : 1,
        pageSize: pageSize ? Number(pageSize) : 50,
      };

      if (type) {
        filters.type = type as string;
      }

      if (startTime) {
        filters.startTime = new Date(startTime as string);
      }

      if (endTime) {
        filters.endTime = new Date(endTime as string);
      }

      const result = await activityLogService.getActivityLogs(filters);

      res.status(200).json({
        data: result.logs,
        meta: {
          total: result.total,
          page: result.page,
          pageSize: result.pageSize,
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Create an activity log entry
   * POST /api/v1/activity-logs
   */
  async createActivityLog(req: Request, res: Response, next: NextFunction): Promise<void> {
    try {
      const { type, description, metadata } = req.body as {
        type?: string;
        description?: string;
        metadata?: Record<string, unknown>;
      };

      if (!type || !description) {
        res.status(400).json({
          error: { code: 'VALIDATION_ERROR', message: 'type and description are required' },
        });
        return;
      }

      const activity = await activityLogService.logActivity({ type, description, metadata });

      res.status(201).json({ data: activity });
    } catch (error) {
      next(error);
    }
  }
}

export const activityLogController = new ActivityLogController();
export default activityLogController;
