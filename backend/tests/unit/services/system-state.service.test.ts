/**
 * SystemStateService Unit Tests
 * Tests for SystemStateService business logic
 */

import { SystemStateService } from '../../../src/services/system-state.service';
import { prisma } from '../../../src/models';
import { ConflictError } from '../../../src/utils/errors';
import { SystemStateEnum } from '@prisma/client';

// Mock prisma client
jest.mock('../../../src/models', () => ({
  prisma: {
    systemState: {
      findUnique: jest.fn(),
      update: jest.fn(),
      create: jest.fn(),
    },
    activityLog: {
      create: jest.fn(),
    },
    $queryRaw: jest.fn(),
  },
}));

const mockPrisma = prisma as unknown as {
  systemState: {
    findUnique: jest.Mock;
    update: jest.Mock;
    create: jest.Mock;
  };
  activityLog: {
    create: jest.Mock;
  };
  $queryRaw: jest.Mock;
};

describe('SystemStateService', () => {
  let systemStateService: SystemStateService;

  beforeEach(() => {
    systemStateService = new SystemStateService();
    jest.clearAllMocks();
  });

  describe('getState', () => {
    it('should return current system state', async () => {
      const mockState = {
        id: 'system-state-singleton',
        state: 'Idle' as SystemStateEnum,
        lastActivity: new Date(),
        updatedAt: new Date(),
      };

      mockPrisma.systemState.findUnique.mockResolvedValue(mockState);

      const result = await systemStateService.getState();

      expect(result).toEqual(mockState);
      expect(mockPrisma.systemState.findUnique).toHaveBeenCalledWith({
        where: { id: 'system-state-singleton' },
      });
    });

    it('should initialize state if it does not exist', async () => {
      mockPrisma.systemState.findUnique.mockResolvedValue(null);

      const mockInitialState = {
        id: 'system-state-singleton',
        state: 'Idle' as SystemStateEnum,
        lastActivity: new Date(),
        updatedAt: new Date(),
      };

      mockPrisma.systemState.create.mockResolvedValue(mockInitialState);

      const result = await systemStateService.getState();

      expect(result.state).toBe('Idle');
      expect(mockPrisma.systemState.create).toHaveBeenCalled();
    });
  });

  describe('setState', () => {
    const currentState = {
      id: 'system-state-singleton',
      state: 'Idle' as SystemStateEnum,
      lastActivity: new Date(),
      updatedAt: new Date(),
    };

    beforeEach(() => {
      mockPrisma.systemState.findUnique.mockResolvedValue(currentState);
    });

    it('should transition from Idle to Thinking', async () => {
      const updatedState = { ...currentState, state: 'Thinking' as SystemStateEnum };
      mockPrisma.systemState.update.mockResolvedValue(updatedState);

      const result = await systemStateService.setState('Thinking');

      expect(result.state).toBe('Thinking');
      expect(mockPrisma.systemState.update).toHaveBeenCalledWith(
        expect.objectContaining({
          data: expect.objectContaining({
            state: 'Thinking',
          }),
        })
      );
    });

    it('should transition from Thinking to Planning', async () => {
      const thinkingState = { ...currentState, state: 'Thinking' as SystemStateEnum };
      mockPrisma.systemState.findUnique.mockResolvedValue(thinkingState);

      const updatedState = { ...thinkingState, state: 'Planning' as SystemStateEnum };
      mockPrisma.systemState.update.mockResolvedValue(updatedState);

      const result = await systemStateService.setState('Planning');

      expect(result.state).toBe('Planning');
    });

    it('should transition from Planning to Idle', async () => {
      const planningState = { ...currentState, state: 'Planning' as SystemStateEnum };
      mockPrisma.systemState.findUnique.mockResolvedValue(planningState);

      const updatedState = { ...planningState, state: 'Idle' as SystemStateEnum };
      mockPrisma.systemState.update.mockResolvedValue(updatedState);

      const result = await systemStateService.setState('Idle');

      expect(result.state).toBe('Idle');
    });

    it('should throw ConflictError for invalid transition (Idle to Planning)', async () => {
      await expect(systemStateService.setState('Planning')).rejects.toThrow(ConflictError);
    });

    it('should throw ConflictError for invalid transition (Thinking to Idle)', async () => {
      const thinkingState = { ...currentState, state: 'Thinking' as SystemStateEnum };
      mockPrisma.systemState.findUnique.mockResolvedValue(thinkingState);

      await expect(systemStateService.setState('Idle')).rejects.toThrow(ConflictError);
    });
  });

  describe('startThinking', () => {
    it('should transition to Thinking state', async () => {
      const currentState = {
        id: 'system-state-singleton',
        state: 'Idle' as SystemStateEnum,
        lastActivity: new Date(),
      };

      const updatedState = { ...currentState, state: 'Thinking' as SystemStateEnum };

      mockPrisma.systemState.findUnique.mockResolvedValue(currentState);
      mockPrisma.systemState.update.mockResolvedValue(updatedState);

      const result = await systemStateService.startThinking();

      expect(result.state).toBe('Thinking');
    });
  });

  describe('startPlanning', () => {
    it('should transition to Planning state', async () => {
      const currentState = {
        id: 'system-state-singleton',
        state: 'Thinking' as SystemStateEnum,
        lastActivity: new Date(),
      };

      const updatedState = { ...currentState, state: 'Planning' as SystemStateEnum };

      mockPrisma.systemState.findUnique.mockResolvedValue(currentState);
      mockPrisma.systemState.update.mockResolvedValue(updatedState);

      const result = await systemStateService.startPlanning();

      expect(result.state).toBe('Planning');
    });
  });

  describe('returnToIdle', () => {
    it('should transition to Idle state', async () => {
      const currentState = {
        id: 'system-state-singleton',
        state: 'Planning' as SystemStateEnum,
        lastActivity: new Date(),
      };

      const updatedState = { ...currentState, state: 'Idle' as SystemStateEnum };

      mockPrisma.systemState.findUnique.mockResolvedValue(currentState);
      mockPrisma.systemState.update.mockResolvedValue(updatedState);

      const result = await systemStateService.returnToIdle();

      expect(result.state).toBe('Idle');
    });
  });

  describe('getHealth', () => {
    it('should return health status with database check', async () => {
      mockPrisma.$queryRaw.mockResolvedValue([{ '1': 1 }]);

      const result = await systemStateService.getHealth();

      expect(result.status).toBeDefined();
      expect(result.uptime).toBeDefined();
      expect(result.timestamp).toBeDefined();
      expect(result.checks.database).toBe('up');
    });

    it('should return unhealthy status if database is down', async () => {
      mockPrisma.$queryRaw.mockRejectedValue(new Error('DB connection failed'));

      const result = await systemStateService.getHealth();

      expect(result.status).toBe('unhealthy');
      expect(result.checks.database).toBe('down');
    });
  });
});
