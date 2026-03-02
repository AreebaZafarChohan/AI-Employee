/**
 * Plan Integration Tests
 * Tests for Plan API endpoints (with mocked Prisma)
 */

import request from 'supertest';
import { createApp } from '../../src/app';
import { Express } from 'express';

// Mock prisma
jest.mock('../../src/models', () => {
  return {
    prisma: {
      plan: {
        findUnique: jest.fn(),
        findMany: jest.fn(),
        create: jest.fn(),
        update: jest.fn(),
        delete: jest.fn(),
        count: jest.fn(),
      },
      planStep: {
        findMany: jest.fn(),
      },
      task: {
        findUnique: jest.fn(),
      },
      activityLog: {
        create: jest.fn(),
      },
      $connect: jest.fn(),
      $disconnect: jest.fn(),
    },
  };
});

// Mock task service
jest.mock('../../src/services/task.service', () => ({
  taskService: {
    getTask: jest.fn(),
  },
}));

// Mock AI provider
jest.mock('../../src/ai', () => ({
  createAIProvider: () => ({
    getName: () => 'mock',
    generatePlan: jest.fn().mockResolvedValue([
      { title: 'Step 1', description: 'First step', estimatedDuration: 30 },
      { title: 'Step 2', description: 'Second step', estimatedDuration: 45 },
    ]),
  }),
}));

import { prisma } from '../../src/models';
import { taskService } from '../../src/services/task.service';

let app: Express;
let baseUrl: string;

const mockTask = {
  id: 'task-id',
  title: 'Test Task',
  description: 'Test',
  status: 'Pending',
  createdAt: new Date(),
  updatedAt: new Date(),
  completedAt: null,
};

const mockPlan = {
  id: 'plan-id',
  taskId: 'task-id',
  status: 'Active',
  createdAt: new Date(),
  updatedAt: new Date(),
  steps: [
    { id: 'step-1', order: 1, title: 'Step 1', description: 'First step', estimatedDuration: 30, completed: false },
  ],
};

beforeAll(() => {
  app = createApp() as Express;
  baseUrl = '/api/v1/plans';
});

beforeEach(() => {
  jest.clearAllMocks();
  (taskService.getTask as jest.Mock).mockResolvedValue(mockTask);
});

describe('Plan API Integration Tests', () => {
  describe('POST /api/v1/tasks/:taskId/plans', () => {
    it('should generate a plan for a task', async () => {
      (prisma.plan.findUnique as jest.Mock).mockResolvedValue(null);
      (prisma.plan.create as jest.Mock).mockResolvedValue(mockPlan);

      const response = await request(app)
        .post(`/api/v1/tasks/${mockTask.id}/plans`)
        .expect(201);

      expect(response.body.data).toBeDefined();
      expect(response.body.data.taskId).toBe(mockTask.id);
      expect(response.body.data.steps).toBeDefined();
    });

    it('should return 404 for non-existent task', async () => {
      (taskService.getTask as jest.Mock).mockRejectedValue({ code: 'NOT_FOUND', statusCode: 404 });

      const fakeId = '00000000-0000-0000-0000-000000000000';
      const response = await request(app)
        .post(`/api/v1/tasks/${fakeId}/plans`)
        .expect(404);

      expect(response.body.error).toBeDefined();
    });

    it('should return error if plan already exists', async () => {
      (prisma.plan.findUnique as jest.Mock).mockResolvedValue({ id: 'existing' });

      const response = await request(app)
        .post(`/api/v1/tasks/${mockTask.id}/plans`)
        .expect(500);

      expect(response.body.error).toBeDefined();
    });
  });

  describe('GET /api/v1/plans', () => {
    it('should list all plans', async () => {
      (prisma.plan.findMany as jest.Mock).mockResolvedValue([mockPlan]);
      (prisma.plan.count as jest.Mock).mockResolvedValue(1);

      const response = await request(app).get(baseUrl).expect(200);

      expect(response.body.data).toBeDefined();
      expect(Array.isArray(response.body.data)).toBe(true);
    });

    it('should filter plans by status', async () => {
      (prisma.plan.findMany as jest.Mock).mockResolvedValue([mockPlan]);
      (prisma.plan.count as jest.Mock).mockResolvedValue(1);

      const response = await request(app)
        .get(`${baseUrl}?status=Active`)
        .expect(200);

      expect(response.body.data).toBeDefined();
    });
  });

  describe('GET /api/v1/plans/:id', () => {
    it('should get plan by ID', async () => {
      (prisma.plan.findUnique as jest.Mock).mockResolvedValue(mockPlan);

      const response = await request(app).get(`${baseUrl}/${mockPlan.id}`).expect(200);

      expect(response.body.data).toBeDefined();
      expect(response.body.data.id).toBe(mockPlan.id);
    });

    it('should return 404 for non-existent plan', async () => {
      (prisma.plan.findUnique as jest.Mock).mockResolvedValue(null);

      const fakeId = '00000000-0000-0000-0000-000000000000';
      const response = await request(app).get(`${baseUrl}/${fakeId}`).expect(404);

      expect(response.body.error).toBeDefined();
    });
  });

  describe('PATCH /api/v1/plans/:id/status', () => {
    it('should update plan status', async () => {
      (prisma.plan.findUnique as jest.Mock).mockResolvedValue(mockPlan);
      const updatedPlan = { ...mockPlan, status: 'Completed' };
      (prisma.plan.update as jest.Mock).mockResolvedValue(updatedPlan);

      const response = await request(app)
        .patch(`${baseUrl}/${mockPlan.id}/status`)
        .send({ status: 'Completed' })
        .expect(200);

      expect(response.body.data.status).toBe('Completed');
    });

    it('should return 400 for invalid status', async () => {
      const response = await request(app)
        .patch(`${baseUrl}/${mockPlan.id}/status`)
        .send({ status: 'Invalid' })
        .expect(400);

      expect(response.body.error).toBeDefined();
    });
  });

  describe('DELETE /api/v1/plans/:id', () => {
    it('should delete plan successfully', async () => {
      (prisma.plan.findUnique as jest.Mock).mockResolvedValue(mockPlan);
      (prisma.plan.delete as jest.Mock).mockResolvedValue({});

      await request(app).delete(`${baseUrl}/${mockPlan.id}`).expect(204);
    });

    it('should return 404 for non-existent plan', async () => {
      (prisma.plan.findUnique as jest.Mock).mockResolvedValue(null);

      const fakeId = '00000000-0000-0000-0000-000000000000';
      const response = await request(app).delete(`${baseUrl}/${fakeId}`).expect(404);

      expect(response.body.error).toBeDefined();
    });
  });
});
