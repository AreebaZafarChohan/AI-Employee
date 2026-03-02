/**
 * Activity Log Service
 * Business logic for activity logging and querying
 */

import { prisma } from '../models';
import { ActivityLog } from '@prisma/client';
import { ActivityLogCreateInput, ActivityLogQuery } from '../models/activity-log.model';
import logger from '../utils/logger';

export class ActivityLogService {
  /**
   * Create a new activity log entry
   */
  async logActivity(data: ActivityLogCreateInput): Promise<ActivityLog> {
    const activity = await prisma.activityLog.create({
      data: {
        type: data.type,
        description: data.description,
        metadata: data.metadata ? JSON.parse(JSON.stringify(data.metadata)) : undefined,
      },
    });

    logger.debug('Activity logged:', { type: data.type, id: activity.id });

    return activity;
  }

  /**
   * Get activity logs with filtering and pagination
   */
  async getActivityLogs(filters?: ActivityLogQuery): Promise<{
    logs: ActivityLog[];
    total: number;
    page: number;
    pageSize: number;
  }> {
    const {
      type,
      startTime,
      endTime,
      page = 1,
      pageSize = 50,
    } = filters || {};

    // Build where clause
    const where: Record<string, unknown> = {};

    if (type) {
      where.type = type;
    }

    if (startTime || endTime) {
      where.timestamp = {};
      if (startTime) {
        (where.timestamp as Record<string, Date>).gte = startTime;
      }
      if (endTime) {
        (where.timestamp as Record<string, Date>).lte = endTime;
      }
    }

    const [logs, total] = await Promise.all([
      prisma.activityLog.findMany({
        where,
        orderBy: { timestamp: 'desc' },
        skip: (page - 1) * pageSize,
        take: Math.min(pageSize, 1000), // Max 1000 items per page
      }),
      prisma.activityLog.count({ where }),
    ]);

    return { logs, total, page, pageSize };
  }

  /**
   * Get recent activity logs
   */
  async getRecentActivity(limit: number = 100): Promise<ActivityLog[]> {
    const logs = await prisma.activityLog.findMany({
      orderBy: { timestamp: 'desc' },
      take: Math.min(limit, 1000),
    });

    return logs;
  }

  /**
   * Get activity logs by type
   */
  async getActivityByType(type: string, limit: number = 100): Promise<ActivityLog[]> {
    const logs = await prisma.activityLog.findMany({
      where: { type },
      orderBy: { timestamp: 'desc' },
      take: Math.min(limit, 1000),
    });

    return logs;
  }

  /**
   * Get activity logs in time range
   */
  async getActivityInTimeRange(startTime: Date, endTime: Date): Promise<ActivityLog[]> {
    const logs = await prisma.activityLog.findMany({
      where: {
        timestamp: {
          gte: startTime,
          lte: endTime,
        },
      },
      orderBy: { timestamp: 'desc' },
    });

    return logs;
  }
}

export const activityLogService = new ActivityLogService();
export default activityLogService;
