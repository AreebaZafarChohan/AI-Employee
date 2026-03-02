/**
 * PlanService Unit Tests
 * Tests for PlanService business logic
 */

import { PlanService } from '../../../src/services/plan.service';
import { prisma } from '../../../src/models';
import { NotFoundError } from '../../../src/utils/errors';

// Mock prisma and dependencies
jest.mock('../../../src/models', () => ({
  prisma: {
    plan: {
      findUnique: jest.fn(),
      findMany: jest.fn(),
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
      count: jest.fn(),
    },
    activityLog: {
      create: jest.fn(),
    },
  },
}));

jest.mock('../../../src/services/task.service', () => ({
  taskService: {
    getTask: jest.fn(),
  },
}));

jest.mock('../../../src/ai', () => ({
  createAIProvider: () => ({
    getName: () => 'mock',
    generatePlan: jest.fn().mockResolvedValue([
      { title: 'Step 1', description: 'First step', estimatedDuration: 30 },
      { title: 'Step 2', description: 'Second step', estimatedDuration: 45 },
    ]),
  }),
}));

const mockPrisma = prisma as unknown as {
  plan: {
    findUnique: jest.Mock;
    findMany: jest.Mock;
    create: jest.Mock;
    update: jest.Mock;
    delete: jest.Mock;
    count: jest.Mock;
  };
  activityLog: {
    create: jest.Mock;
  };
};

describe('PlanService', () => {
  let planService: PlanService;

  beforeEach(() => {
    planService = new PlanService();
    jest.clearAllMocks();
  });

  describe('generatePlan', () => {
    const mockTask = {
      id: 'task-id',
      title: 'Test Task',
      description: 'Test Description',
      status: 'Pending',
      createdAt: new Date(),
      updatedAt: new Date(),
      completedAt: null,
    };

    beforeEach(() => {
      // Import and mock taskService
      const { taskService } = require('../../../src/services/task.service');
      taskService.getTask.mockResolvedValue(mockTask);
    });

    it('should generate a plan with steps', async () => {
      mockPrisma.plan.findUnique.mockResolvedValue(null); // No existing plan

      const mockPlan = {
        id: 'plan-id',
        taskId: 'task-id',
        status: 'Active',
        createdAt: new Date(),
        updatedAt: new Date(),
        steps: [
          { id: 'step-1', order: 1, title: 'Step 1', description: 'First step' },
          { id: 'step-2', order: 2, title: 'Step 2', description: 'Second step' },
        ],
      };

      mockPrisma.plan.create.mockResolvedValue(mockPlan);

      const result = await planService.generatePlan('task-id');

      expect(result).toBeDefined();
      expect(result.taskId).toBe('task-id');
      expect(result.steps.length).toBeGreaterThan(0);
      expect(mockPrisma.plan.create).toHaveBeenCalled();
    });

    it('should throw error if plan already exists', async () => {
      mockPrisma.plan.findUnique.mockResolvedValue({ id: 'existing-plan-id' });

      await expect(planService.generatePlan('task-id')).rejects.toThrow(
        'Plan already exists for this task'
      );
    });
  });

  describe('getPlan', () => {
    it('should return plan with steps', async () => {
      const mockPlan = {
        id: 'plan-id',
        taskId: 'task-id',
        status: 'Active',
        createdAt: new Date(),
        updatedAt: new Date(),
        steps: [
          { id: 'step-1', order: 1, title: 'Step 1', description: 'First step' },
        ],
      };

      mockPrisma.plan.findUnique.mockResolvedValue(mockPlan);

      const result = await planService.getPlan('plan-id');

      expect(result).toEqual(mockPlan);
      expect(mockPrisma.plan.findUnique).toHaveBeenCalledWith({
        where: { id: 'plan-id' },
        include: { steps: { orderBy: { order: 'asc' } } },
      });
    });

    it('should throw NotFoundError for non-existent plan', async () => {
      mockPrisma.plan.findUnique.mockResolvedValue(null);

      await expect(planService.getPlan('fake-id')).rejects.toThrow(NotFoundError);
    });
  });

  describe('getPlans', () => {
    it('should return plans with pagination', async () => {
      const mockPlans = [
        {
          id: 'plan-1',
          taskId: 'task-1',
          status: 'Active',
          createdAt: new Date(),
          updatedAt: new Date(),
          steps: [],
          task: { title: 'Task 1' },
        },
      ];

      mockPrisma.plan.findMany.mockResolvedValue(mockPlans);
      mockPrisma.plan.count.mockResolvedValue(1);

      const result = await planService.getPlans({ page: 1, pageSize: 20 });

      expect(result.plans).toBeDefined();
      expect(result.total).toBe(1);
    });

    it('should filter by status', async () => {
      mockPrisma.plan.findMany.mockResolvedValue([]);
      mockPrisma.plan.count.mockResolvedValue(0);

      await planService.getPlans({ status: 'Active' });

      expect(mockPrisma.plan.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: { status: 'Active' },
        })
      );
    });
  });

  describe('updatePlanStatus', () => {
    const mockPlan = {
      id: 'plan-id',
      taskId: 'task-id',
      status: 'Draft',
      createdAt: new Date(),
      updatedAt: new Date(),
      steps: [],
    };

    beforeEach(() => {
      mockPrisma.plan.findUnique.mockResolvedValue(mockPlan);
    });

    it('should update plan status', async () => {
      const updatedPlan = { ...mockPlan, status: 'Active' as const };
      mockPrisma.plan.update.mockResolvedValue(updatedPlan);

      const result = await planService.updatePlanStatus('plan-id', 'Active');

      expect(result.status).toBe('Active');
      expect(mockPrisma.plan.update).toHaveBeenCalled();
    });

    it('should throw NotFoundError for non-existent plan', async () => {
      mockPrisma.plan.findUnique.mockResolvedValue(null);

      await expect(planService.updatePlanStatus('fake-id', 'Active')).rejects.toThrow(
        NotFoundError
      );
    });
  });

  describe('deletePlan', () => {
    const mockPlan = {
      id: 'plan-id',
      taskId: 'task-id',
      status: 'Draft',
    };

    beforeEach(() => {
      mockPrisma.plan.findUnique.mockResolvedValue(mockPlan);
    });

    it('should delete plan successfully', async () => {
      mockPrisma.plan.delete.mockResolvedValue({});

      await planService.deletePlan('plan-id');

      expect(mockPrisma.plan.delete).toHaveBeenCalledWith({
        where: { id: 'plan-id' },
      });
    });

    it('should throw NotFoundError for non-existent plan', async () => {
      mockPrisma.plan.findUnique.mockResolvedValue(null);

      await expect(planService.deletePlan('fake-id')).rejects.toThrow(NotFoundError);
    });
  });
});
