/**
 * System Controller
 * HTTP request handlers for system endpoints
 */

import { Request, Response, NextFunction } from 'express';
import { systemStateService } from '../services/system-state.service';
import { SystemState as PrismaSystemState } from '@prisma/client';

/**
 * Map backend PascalCase state to frontend kebab-case
 */
function mapSystemState(state: string): string {
  const mapping: Record<string, string> = {
    'Idle': 'idle',
    'Thinking': 'processing',
    'Planning': 'working',
    'Error': 'error',
  };
  return mapping[state] ?? state.toLowerCase();
}

/**
 * Map backend system state to frontend shape
 */
function mapSystemStateForResponse(state: PrismaSystemState): Record<string, unknown> {
  return {
    status: mapSystemState(state.state as string),
    lastActivityAt: state.lastActivity.toISOString(),
    currentTaskId: (state as unknown as { currentTaskId?: string | null }).currentTaskId ?? null,
  };
}

export class SystemController {
  /**
   * Get current system state
   * GET /api/v1/system/state
   */
  async getState(_req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const state = await systemStateService.getState();

      res.status(200).json({
        data: mapSystemStateForResponse(state),
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      _next(error);
    }
  }

  /**
   * Get health status
   * GET /api/v1/system/health
   */
  async getHealth(_req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const health = await systemStateService.getHealth();

      const statusCode = health.status === 'healthy' ? 200 : 503;

      res.status(statusCode).json({
        data: health,
        meta: {
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      _next(error);
    }
  }
}

export const systemController = new SystemController();
export default systemController;
