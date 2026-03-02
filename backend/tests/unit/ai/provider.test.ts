/**
 * AI Provider Tests
 * Tests for AI provider abstraction and factory
 */

import { createAIProvider, MockAIProvider } from '../../../src/ai/factory';
import { TaskContext } from '../../../src/ai/types';

// Mock config
jest.mock('../../../src/config/env', () => ({
  __esModule: true,
  default: {
    AI_PROVIDER: 'mock',
    AI_API_KEY: '',
    NODE_ENV: 'test',
    LOG_LEVEL: 'debug',
    DATABASE_URL: 'postgresql://test:test@localhost:5432/test',
    CORS_ORIGIN: '*',
    CORS_METHODS: 'GET,POST,PUT,PATCH,DELETE',
    CORS_HEADERS: 'Content-Type,Authorization',
    PORT: '3000',
    HOST: '0.0.0.0',
  },
}));

describe('AI Provider', () => {
  describe('createAIProvider', () => {
    it('should create a mock provider when AI_PROVIDER is mock', () => {
      const provider = createAIProvider();
      expect(provider).toBeDefined();
      expect(provider.getName()).toBe('mock');
    });

    it('should return provider with generatePlan method', () => {
      const provider = createAIProvider();
      expect(typeof provider.generatePlan).toBe('function');
    });
  });

  describe('MockAIProvider', () => {
    let provider: MockAIProvider;

    beforeEach(() => {
      provider = new MockAIProvider();
    });

    it('should return mock as provider name', () => {
      expect(provider.getName()).toBe('mock');
    });

    it('should generate plan steps', async () => {
      const taskContext: TaskContext = {
        id: 'test-id',
        title: 'Test Task',
        description: 'Test Description',
      };

      const steps = await provider.generatePlan(taskContext);

      expect(steps).toBeDefined();
      expect(Array.isArray(steps)).toBe(true);
      expect(steps.length).toBeGreaterThan(0);
    });

    it('should generate steps with required fields', async () => {
      const taskContext: TaskContext = {
        id: 'test-id',
        title: 'Test Task',
        description: 'Test Description',
      };

      const steps = await provider.generatePlan(taskContext);

      steps.forEach((step) => {
        expect(step).toHaveProperty('title');
        expect(step).toHaveProperty('description');
        expect(step.title).toBeDefined();
        expect(step.description).toBeDefined();
      });
    });

    it('should generate steps with optional estimatedDuration', async () => {
      const taskContext: TaskContext = {
        id: 'test-id',
        title: 'Test Task',
        description: 'Test Description',
      };

      const steps = await provider.generatePlan(taskContext);

      // At least some steps should have estimatedDuration
      const stepsWithDuration = steps.filter((s) => s.estimatedDuration !== undefined);
      expect(stepsWithDuration.length).toBeGreaterThan(0);
    });
  });
});
