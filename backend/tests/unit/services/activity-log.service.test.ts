/**
 * ActivityLogService Unit Tests
 * Tests for ActivityLogService business logic
 */

import { ActivityLogService } from '../../../src/services/activity-log.service';
import { prisma } from '../../../src/models';

// Mock prisma client
jest.mock('../../../src/models', () => ({
  prisma: {
    activityLog: {
      create: jest.fn(),
      findMany: jest.fn(),
      count: jest.fn(),
    },
  },
}));

const mockPrisma = prisma as unknown as {
  activityLog: {
    create: jest.Mock;
    findMany: jest.Mock;
    count: jest.Mock;
  };
};

describe('ActivityLogService', () => {
  let activityLogService: ActivityLogService;

  beforeEach(() => {
    activityLogService = new ActivityLogService();
    jest.clearAllMocks();
  });

  describe('logActivity', () => {
    it('should create an activity log entry', async () => {
      const logData = {
        type: 'task.created',
        description: 'Task created for testing',
        metadata: { taskId: 'test-id' },
      };

      const mockLog = {
        id: 'log-id',
        ...logData,
        timestamp: new Date(),
      };

      mockPrisma.activityLog.create.mockResolvedValue(mockLog);

      const result = await activityLogService.logActivity(logData);

      expect(result).toEqual(mockLog);
      expect(mockPrisma.activityLog.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          type: logData.type,
          description: logData.description,
          metadata: expect.any(Object),
        }),
      });
    });
  });

  describe('getActivityLogs', () => {
    it('should return activity logs with pagination', async () => {
      const mockLogs = [
        {
          id: 'log-1',
          type: 'task.created',
          description: 'Task created',
          timestamp: new Date(),
          metadata: null,
        },
        {
          id: 'log-2',
          type: 'state.changed',
          description: 'State changed',
          timestamp: new Date(),
          metadata: null,
        },
      ];

      mockPrisma.activityLog.findMany.mockResolvedValue(mockLogs);
      mockPrisma.activityLog.count.mockResolvedValue(2);

      const result = await activityLogService.getActivityLogs({ page: 1, pageSize: 50 });

      expect(result.logs).toEqual(mockLogs);
      expect(result.total).toBe(2);
      expect(result.page).toBe(1);
      expect(result.pageSize).toBe(50);
    });

    it('should filter by type', async () => {
      mockPrisma.activityLog.findMany.mockResolvedValue([]);
      mockPrisma.activityLog.count.mockResolvedValue(0);

      await activityLogService.getActivityLogs({ type: 'task.created' });

      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { type: 'task.created' },
        })
      );
    });

    it('should filter by time range', async () => {
      const startTime = new Date('2024-01-01');
      const endTime = new Date('2024-01-02');

      mockPrisma.activityLog.findMany.mockResolvedValue([]);
      mockPrisma.activityLog.count.mockResolvedValue(0);

      await activityLogService.getActivityLogs({ startTime, endTime });

      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            timestamp: expect.objectContaining({
              gte: startTime,
              lte: endTime,
            }),
          }),
        })
      );
    });

    it('should order by timestamp descending', async () => {
      mockPrisma.activityLog.findMany.mockResolvedValue([]);
      mockPrisma.activityLog.count.mockResolvedValue(0);

      await activityLogService.getActivityLogs({});

      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          orderBy: { timestamp: 'desc' },
        })
      );
    });

    it('should limit pageSize to 1000', async () => {
      mockPrisma.activityLog.findMany.mockResolvedValue([]);
      mockPrisma.activityLog.count.mockResolvedValue(0);

      await activityLogService.getActivityLogs({ pageSize: 2000 });

      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          take: 1000,
        })
      );
    });
  });

  describe('getRecentActivity', () => {
    it('should return recent activity logs', async () => {
      const mockLogs = [
        { id: 'log-1', type: 'task.created', description: 'Recent task', timestamp: new Date() },
      ];

      mockPrisma.activityLog.findMany.mockResolvedValue(mockLogs);

      const result = await activityLogService.getRecentActivity(10);

      expect(result).toEqual(mockLogs);
      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          orderBy: { timestamp: 'desc' },
          take: 10,
        })
      );
    });

    it('should limit to 1000 items maximum', async () => {
      mockPrisma.activityLog.findMany.mockResolvedValue([]);

      await activityLogService.getRecentActivity(2000);

      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          take: 1000,
        })
      );
    });
  });

  describe('getActivityByType', () => {
    it('should return activity logs by type', async () => {
      const mockLogs = [
        { id: 'log-1', type: 'task.created', description: 'Task created', timestamp: new Date() },
      ];

      mockPrisma.activityLog.findMany.mockResolvedValue(mockLogs);

      const result = await activityLogService.getActivityByType('task.created', 10);

      expect(result).toEqual(mockLogs);
      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { type: 'task.created' },
          orderBy: { timestamp: 'desc' },
          take: 10,
        })
      );
    });
  });

  describe('getActivityInTimeRange', () => {
    it('should return activity logs in time range', async () => {
      const startTime = new Date('2024-01-01');
      const endTime = new Date('2024-01-02');
      const mockLogs = [
        {
          id: 'log-1',
          type: 'task.created',
          description: 'Task created',
          timestamp: new Date('2024-01-01T12:00:00Z'),
        },
      ];

      mockPrisma.activityLog.findMany.mockResolvedValue(mockLogs);

      const result = await activityLogService.getActivityInTimeRange(startTime, endTime);

      expect(result).toEqual(mockLogs);
      expect(mockPrisma.activityLog.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: {
            timestamp: {
              gte: startTime,
              lte: endTime,
            },
          },
          orderBy: { timestamp: 'desc' },
        })
      );
    });
  });
});
