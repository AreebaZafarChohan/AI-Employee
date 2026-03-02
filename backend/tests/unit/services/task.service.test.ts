/**
 * TaskService Unit Tests
 * Tests for TaskService business logic
 */

import { TaskService } from '../../../src/services/task.service';
import { prisma } from '../../../src/models';
import { NotFoundError, ConflictError } from '../../../src/utils/errors';
import { TaskStatus } from '@prisma/client';

// Mock prisma client
jest.mock('../../../src/models', () => ({
  prisma: {
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
    },
  },
}));

const mockPrisma = prisma as unknown as {
  task: {
    create: jest.Mock;
    findUnique: jest.Mock;
    findMany: jest.Mock;
    update: jest.Mock;
    delete: jest.Mock;
    count: jest.Mock;
  };
  activityLog: {
    create: jest.Mock;
  };
};

describe('TaskService', () => {
  let taskService: TaskService;

  beforeEach(() => {
    taskService = new TaskService();
    jest.clearAllMocks();
  });

  describe('createTask', () => {
    it('should create a task successfully', async () => {
      const taskData = { title: 'Test Task', description: 'Test Desc' };
      const mockTask = {
        id: 'test-id',
        ...taskData,
        status: 'Pending',
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt: null,
      };

      mockPrisma.task.create.mockResolvedValue(mockTask);

      const result = await taskService.createTask(taskData);

      expect(result).toEqual(mockTask);
      expect(mockPrisma.task.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          title: taskData.title,
          description: taskData.description,
        }),
      });
    });
  });

  describe('getTask', () => {
    it('should return a task by ID', async () => {
      const mockTask = {
        id: 'test-id',
        title: 'Test Task',
        status: 'Pending',
        createdAt: new Date(),
        updatedAt: new Date(),
        completedAt: null,
      };

      mockPrisma.task.findUnique.mockResolvedValue(mockTask);

      const result = await taskService.getTask('test-id');

      expect(result).toEqual(mockTask);
      expect(mockPrisma.task.findUnique).toHaveBeenCalledWith({
        where: { id: 'test-id' },
      });
    });

    it('should throw NotFoundError for non-existent task', async () => {
      mockPrisma.task.findUnique.mockResolvedValue(null);

      await expect(taskService.getTask('fake-id')).rejects.toThrow(NotFoundError);
    });
  });

  describe('getTasks', () => {
    it('should return tasks with pagination', async () => {
      const mockTasks = [
        { id: '1', title: 'Task 1', status: 'Pending', createdAt: new Date(), updatedAt: new Date(), completedAt: null },
        { id: '2', title: 'Task 2', status: 'InProgress', createdAt: new Date(), updatedAt: new Date(), completedAt: null },
      ];

      mockPrisma.task.findMany.mockResolvedValue(mockTasks);
      mockPrisma.task.count.mockResolvedValue(2);

      const result = await taskService.getTasks({ page: 1, pageSize: 20 });

      expect(result.tasks).toEqual(mockTasks);
      expect(result.total).toBe(2);
    });

    it('should filter by status', async () => {
      mockPrisma.task.findMany.mockResolvedValue([]);
      mockPrisma.task.count.mockResolvedValue(0);

      await taskService.getTasks({ status: 'Pending' });

      expect(mockPrisma.task.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { status: 'Pending' },
        })
      );
    });
  });

  describe('updateTaskStatus', () => {
    const existingTask = {
      id: 'test-id',
      title: 'Test Task',
      status: 'Pending' as TaskStatus,
      createdAt: new Date(),
      updatedAt: new Date(),
      completedAt: null,
    };

    beforeEach(() => {
      mockPrisma.task.findUnique.mockResolvedValue(existingTask);
    });

    it('should transition from Pending to InProgress', async () => {
      const updatedTask = { ...existingTask, status: 'InProgress' as TaskStatus };
      mockPrisma.task.update.mockResolvedValue(updatedTask);

      const result = await taskService.updateTaskStatus('test-id', 'InProgress');

      expect(result.status).toBe('InProgress');
      expect(mockPrisma.task.update).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            status: 'InProgress',
          }),
        })
      );
    });

    it('should transition from InProgress to Done and set completedAt', async () => {
      const inProgressTask = { ...existingTask, status: 'InProgress' as TaskStatus };
      mockPrisma.task.findUnique.mockResolvedValue(inProgressTask);

      const updatedTask = {
        ...inProgressTask,
        status: 'Done' as TaskStatus,
        completedAt: new Date(),
      };
      mockPrisma.task.update.mockResolvedValue(updatedTask);

      const result = await taskService.updateTaskStatus('test-id', 'Done');

      expect(result.status).toBe('Done');
      expect(result.completedAt).toBeDefined();
    });

    it('should throw ConflictError for invalid transition (Pending to Done)', async () => {
      await expect(taskService.updateTaskStatus('test-id', 'Done')).rejects.toThrow(
        ConflictError
      );
    });

    it('should throw ConflictError for Done to any status', async () => {
      const doneTask = { ...existingTask, status: 'Done' as TaskStatus };
      mockPrisma.task.findUnique.mockResolvedValue(doneTask);

      await expect(taskService.updateTaskStatus('test-id', 'Pending')).rejects.toThrow(
        ConflictError
      );
    });
  });

  describe('deleteTask', () => {
    it('should delete a task successfully', async () => {
      mockPrisma.task.findUnique.mockResolvedValue({ id: 'test-id' });
      mockPrisma.task.delete.mockResolvedValue({});

      await taskService.deleteTask('test-id');

      expect(mockPrisma.task.delete).toHaveBeenCalledWith({
        where: { id: 'test-id' },
      });
    });

    it('should throw NotFoundError for non-existent task', async () => {
      mockPrisma.task.findUnique.mockResolvedValue(null);

      await expect(taskService.deleteTask('fake-id')).rejects.toThrow(NotFoundError);
    });
  });
});
