/**
 * Task Integration Tests
 * Tests for Task API endpoints (with mocked Prisma)
 */

import request from 'supertest';
import { createApp } from '../../src/app';
import { Express } from 'express';

// Mock prisma before importing app
jest.mock('../../src/models', () => {
  const mockPrisma = {
    task: {
      create: jest.fn(),
      findUnique: jest.fn(),
      findMany: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
      count: jest.fn(),
    },
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
let baseUrl: string;

const mockTask = {
  id: 'test-task-id',
  title: 'Test Task',
  description: 'Test description',
  status: 'Pending',
  createdAt: new Date(),
  updatedAt: new Date(),
  completedAt: null,
};

beforeAll(() => {
  app = createApp() as Express;
  baseUrl = '/api/v1/tasks';
});

beforeEach(() => {
  jest.clearAllMocks();
});

describe('Task API Integration Tests', () => {
  describe('POST /api/v1/tasks', () => {
    it('should create a new task successfully', async () => {
      (prisma.task.create as jest.Mock).mockResolvedValue(mockTask);

      const response = await request(app)
        .post(baseUrl)
        .send({ title: mockTask.title, description: mockTask.description })
        .expect(201);

      expect(response.body.data).toBeDefined();
      expect(response.body.data.title).toBe(mockTask.title);
      expect(response.body.data.status).toBe('Pending');
    });

    it('should return 400 if title is missing', async () => {
      const response = await request(app)
        .post(baseUrl)
        .send({ description: 'No title' })
        .expect(400);

      expect(response.body.error).toBeDefined();
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
    });
  });

  describe('GET /api/v1/tasks', () => {
    it('should list all tasks', async () => {
      (prisma.task.findMany as jest.Mock).mockResolvedValue([mockTask]);
      (prisma.task.count as jest.Mock).mockResolvedValue(1);

      const response = await request(app).get(baseUrl).expect(200);

      expect(response.body.data).toBeDefined();
      expect(Array.isArray(response.body.data)).toBe(true);
      expect(response.body.meta.total).toBe(1);
    });

    it('should filter tasks by status', async () => {
      (prisma.task.findMany as jest.Mock).mockResolvedValue([mockTask]);
      (prisma.task.count as jest.Mock).mockResolvedValue(1);

      const response = await request(app)
        .get(`${baseUrl}?status=Pending`)
        .expect(200);

      expect(response.body.data).toBeDefined();
    });
  });

  describe('GET /api/v1/tasks/:id', () => {
    it('should get task by ID', async () => {
      (prisma.task.findUnique as jest.Mock).mockResolvedValue(mockTask);

      const response = await request(app).get(`${baseUrl}/${mockTask.id}`).expect(200);

      expect(response.body.data).toBeDefined();
      expect(response.body.data.id).toBe(mockTask.id);
    });

    it('should return 404 for non-existent task', async () => {
      (prisma.task.findUnique as jest.Mock).mockResolvedValue(null);

      const fakeId = '00000000-0000-0000-0000-000000000000';
      const response = await request(app).get(`${baseUrl}/${fakeId}`).expect(404);

      expect(response.body.error).toBeDefined();
      expect(response.body.error.code).toBe('NOT_FOUND');
    });
  });

  describe('PATCH /api/v1/tasks/:id/status', () => {
    it('should update task status', async () => {
      const taskId = 'update-status-task-id';
      const updatedTask = { 
        id: taskId,
        title: 'Test Task',
        description: 'Test description',
        status: 'InProgress',
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt: null,
      };
      // Mock task to return Pending status (can transition to InProgress)
      const pendingTask = { 
        id: taskId,
        title: 'Test Task',
        description: 'Test description',
        status: 'Pending',
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt: null,
      };
      
      // Setup mock chain for all calls
      (prisma.task.findUnique as jest.Mock).mockResolvedValue(pendingTask);
      (prisma.activityLog.create as jest.Mock).mockResolvedValue({ id: 'log-1' });
      (prisma.task.update as jest.Mock).mockResolvedValue(updatedTask);

      const response = await request(app)
        .patch(`${baseUrl}/${taskId}/status`)
        .send({ status: 'In Progress' })
        .expect(200);

      expect(response.body.data.status).toBe('InProgress');
    });

    it('should return 409 for invalid status transition', async () => {
      const pendingTask = { ...mockTask, status: 'Pending' };
      (prisma.task.findUnique as jest.Mock).mockResolvedValue(pendingTask);

      const response = await request(app)
        .patch(`${baseUrl}/${mockTask.id}/status`)
        .send({ status: 'Done' })
        .expect(409);

      expect(response.body.error).toBeDefined();
      expect(response.body.error.code).toBe('INVALID_TRANSITION');
    });
  });

  describe('DELETE /api/v1/tasks/:id', () => {
    it('should delete task successfully', async () => {
      (prisma.task.findUnique as jest.Mock).mockResolvedValue(mockTask);
      (prisma.task.delete as jest.Mock).mockResolvedValue({});

      await request(app).delete(`${baseUrl}/${mockTask.id}`).expect(204);
    });

    it('should return 404 for deleting non-existent task', async () => {
      (prisma.task.findUnique as jest.Mock).mockResolvedValue(null);

      const fakeId = '00000000-0000-0000-0000-000000000000';
      const response = await request(app).delete(`${baseUrl}/${fakeId}`).expect(404);

      expect(response.body.error).toBeDefined();
    });
  });
});
