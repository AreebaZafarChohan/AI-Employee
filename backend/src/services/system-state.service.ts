/**
 * System State Service
 * Business logic for system state management and state machine
 */

import { prisma } from '../models';
import type { SystemState } from '@prisma/client';
import type { SystemStateEnum } from '../models/system-state.model';
import { STATE_TRANSITIONS } from '../models/system-state.model';
import { ConflictError } from '../utils/errors';
import logger from '../utils/logger';

export class SystemStateService {
  private readonly SINGLETON_ID = 'system-state-singleton';

  /**
   * Get current system state
   */
  async getState(): Promise<SystemState> {
    const state = await prisma.systemState.findUnique({
      where: { id: this.SINGLETON_ID },
    });

    if (!state) {
      // Initialize if doesn't exist
      return this.initializeState();
    }

    return state;
  }

  /**
   * Set system state with transition validation
   */
  async setState(newState: SystemStateEnum): Promise<SystemState> {
    const currentState = await this.getState();

    // Validate state transition
    const validTransitions = STATE_TRANSITIONS[currentState.state];

    if (!validTransitions.includes(newState)) {
      throw new ConflictError(
        `Cannot transition from ${currentState.state} to ${newState}. Valid transitions: ${validTransitions.join(', ') || 'none'}`,
        'INVALID_TRANSITION'
      );
    }

    const updatedState = await prisma.systemState.update({
      where: { id: this.SINGLETON_ID },
      data: {
        state: newState,
        lastActivity: new Date(),
      },
    });

    logger.info('System state changed:', {
      from: currentState.state,
      to: newState,
    });

    // Log state change activity
    await this.logStateChange(currentState.state, newState);

    return updatedState;
  }

  /**
   * Transition to Thinking state
   */
  async startThinking(): Promise<SystemState> {
    return this.setState('Thinking');
  }

  /**
   * Transition to Planning state
   */
  async startPlanning(): Promise<SystemState> {
    return this.setState('Planning');
  }

  /**
   * Transition to Idle state
   */
  async returnToIdle(): Promise<SystemState> {
    return this.setState('Idle');
  }

  /**
   * Get health status
   */
  async getHealth(): Promise<{
    status: 'healthy' | 'unhealthy';
    uptime: number;
    timestamp: Date;
    checks: Record<string, string>;
  }> {
    const startTime = Date.now();
    const checks: Record<string, string> = {};

    // Check database connectivity
    try {
      await prisma.$queryRaw`SELECT 1`;
      checks.database = 'up';
    } catch (error) {
      checks.database = 'down';
    }

    const isHealthy = checks.database === 'up';

    return {
      status: isHealthy ? 'healthy' : 'unhealthy',
      uptime: Math.floor((Date.now() - startTime) / 1000),
      timestamp: new Date(),
      checks,
    };
  }

  /**
   * Initialize system state if it doesn't exist
   */
  private async initializeState(): Promise<SystemState> {
    const state = await prisma.systemState.create({
      data: {
        id: this.SINGLETON_ID,
        state: 'Idle',
        lastActivity: new Date(),
      },
    });

    logger.info('System state initialized:', { state: state.state });

    return state;
  }

  /**
   * Log state change activity
   */
  private async logStateChange(from: SystemStateEnum, to: SystemStateEnum): Promise<void> {
    try {
      await prisma.activityLog.create({
        data: {
          type: 'state.changed',
          description: `System state changed from ${from} to ${to}`,
          metadata: JSON.stringify({ from, to }),
        },
      });
    } catch (error) {
      logger.warn('Failed to log state change:', { from, to, error });
    }
  }
}

export const systemStateService = new SystemStateService();
export default systemStateService;
