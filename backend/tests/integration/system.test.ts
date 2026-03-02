/**
 * System Integration Tests
 * Tests for System API endpoints (with mocked Prisma)
 */

import request from 'supertest';
import { createApp } from '../../src/app';
import { Express } from 'express';

// Mock prisma
jest.mock('../../src/models', () => {
  const mockPrisma = {
    systemState: {
      findUnique: jest.fn(),
      update: jest.fn(),
      create: jest.fn(),
    },
    activityLog: {
      create: jest.fn(),
    },
    $queryRaw: jest.fn(),
    $connect: jest.fn(),
    $disconnect: jest.fn(),
  };
  return { prisma: mockPrisma };
});

import { prisma } from '../../src/models';

let app: Express;

beforeAll(() => {
  app = createApp() as Express;
});

beforeEach(() => {
  jest.clearAllMocks();
});

describe('System API Integration Tests', () => {
  describe('GET /api/v1/system/state', () => {
    it('should return current system state', async () => {
      const mockState = {
        id: 'system-state-singleton',
        state: 'Idle',
        lastActivity: new Date(),
        updatedAt: new Date(),
      };
      (prisma.systemState.findUnique as jest.Mock).mockResolvedValue(mockState);

      const response = await request(app).get('/api/v1/system/state').expect(200);

      expect(response.body.data).toBeDefined();
      expect(response.body.data.state).toBe('Idle');
      expect(response.body.data.lastActivity).toBeDefined();
    });

    it('should return state in correct format', async () => {
      const mockState = {
        id: 'system-state-singleton',
        state: 'Idle',
        lastActivity: new Date(),
      };
      (prisma.systemState.findUnique as jest.Mock).mockResolvedValue(mockState);

      const response = await request(app).get('/api/v1/system/state').expect(200);

      expect(response.body).toHaveProperty('data');
      expect(response.body).toHaveProperty('meta');
    });
  });

  describe('GET /api/v1/system/health', () => {
    it('should return health status', async () => {
      (prisma.$queryRaw as jest.Mock).mockResolvedValue([{ '1': 1 }]);

      const response = await request(app).get('/api/v1/system/health').expect(200);

      expect(response.body.data).toBeDefined();
      expect(response.body.data.status).toBe('healthy');
      expect(response.body.data.checks.database).toBe('up');
    });

    it('should return unhealthy status if database is down', async () => {
      (prisma.$queryRaw as jest.Mock).mockRejectedValue(new Error('DB down'));

      const response = await request(app).get('/api/v1/system/health').expect(503);

      expect(response.body.data.status).toBe('unhealthy');
      expect(response.body.data.checks.database).toBe('down');
    });
  });
});
