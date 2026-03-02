/**
 * Activity Log Integration Tests
 * Tests for Activity Log API endpoints (with mocked Prisma)
 */

import request from 'supertest';
import { createApp } from '../../src/app';
import { Express } from 'express';

// Mock prisma
jest.mock('../../src/models', () => {
  const mockPrisma = {
    activityLog: {
      create: jest.fn(),
      findMany: jest.fn(),
      count: jest.fn(),
    },
    $connect: jest.fn(),
    $disconnect: jest.fn(),
  };
  return { prisma: mockPrisma };
});

import { prisma } from '../../src/models';

let app: Express;

const mockLogs = [
  {
    id: 'log-1',
    type: 'task.created',
    description: 'Task created',
    timestamp: new Date(),
    metadata: { taskId: 'test-id' },
  },
  {
    id: 'log-2',
    type: 'state.changed',
    description: 'State changed',
    timestamp: new Date(),
    metadata: { from: 'Idle', to: 'Thinking' },
  },
];

beforeAll(() => {
  app = createApp() as Express;
});

beforeEach(() => {
  jest.clearAllMocks();
});

describe('Activity Log API Integration Tests', () => {
  describe('GET /api/v1/activity-logs', () => {
    it('should list activity logs', async () => {
      (prisma.activityLog.findMany as jest.Mock).mockResolvedValue(mockLogs);
      (prisma.activityLog.count as jest.Mock).mockResolvedValue(2);

      const response = await request(app)
        .get('/api/v1/activity-logs')
        .expect(200);

      expect(response.body.data).toBeDefined();
      expect(Array.isArray(response.body.data)).toBe(true);
      expect(response.body.meta.total).toBe(2);
    });

    it('should filter by type', async () => {
      (prisma.activityLog.findMany as jest.Mock).mockResolvedValue([mockLogs[0]]);
      (prisma.activityLog.count as jest.Mock).mockResolvedValue(1);

      const response = await request(app)
        .get('/api/v1/activity-logs?type=task.created')
        .expect(200);

      expect(response.body.data).toBeDefined();
      response.body.data.forEach((log: { type: string }) => {
        expect(log.type).toBe('task.created');
      });
    });

    it('should support pagination', async () => {
      (prisma.activityLog.findMany as jest.Mock).mockResolvedValue(mockLogs.slice(0, 1));
      (prisma.activityLog.count as jest.Mock).mockResolvedValue(2);

      const response = await request(app)
        .get('/api/v1/activity-logs?page=1&pageSize=10')
        .expect(200);

      expect(response.body.data.length).toBeLessThanOrEqual(10);
      expect(response.body.meta.pageSize).toBe(10);
    });

    it('should return logs in descending chronological order', async () => {
      (prisma.activityLog.findMany as jest.Mock).mockResolvedValue(mockLogs);
      (prisma.activityLog.count as jest.Mock).mockResolvedValue(2);

      const response = await request(app).get('/api/v1/activity-logs').expect(200);

      expect(response.body.data).toBeDefined();
      if (response.body.data.length > 1) {
        const timestamps = response.body.data.map(
          (log: { timestamp: string }) => new Date(log.timestamp).getTime()
        );
        for (let i = 1; i < timestamps.length; i++) {
          expect(timestamps[i]).toBeLessThanOrEqual(timestamps[i - 1]);
        }
      }
    });
  });
});
