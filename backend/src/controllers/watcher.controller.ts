/**
 * Watcher Controller
 * Uses MCP Watcher Server to manage and monitor Python watchers.
 */

import { Request, Response } from 'express';
import * as path from 'path';
import { mcpClientService } from '../services/mcp-client.service';
import { logger } from '../lib/logger';

const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');
const WATCHER_SERVER_PATH = path.join(ROOT_PATH, 'mcp', 'watcher-server', 'src', 'index.js');

export class WatcherController {
  private async getMcpResult(toolName: string, toolArgs: any = {}) {
    try {
      const response = await mcpClientService.callTool(
        'watcher-server',
        'node',
        [WATCHER_SERVER_PATH],
        toolName,
        toolArgs
      );

      if (response.isError) {
        throw new Error(JSON.stringify(response.content));
      }

      // MCP response content is an array, we assume the first item is the JSON text
      const content = (response.content as any[])[0];
      if (content && content.type === 'text') {
        return JSON.parse(content.text);
      }
      return null;
    } catch (error) {
      logger.error(`MCP Error calling ${toolName}:`, error);
      throw error;
    }
  }

  /**
   * GET /api/v1/watchers
   * Returns status of all watchers.
   */
  async getWatchers(_req: Request, res: Response) {
    try {
      const result = await this.getMcpResult('list_watchers');
      res.json({ data: result.watchers });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch watchers via MCP' } });
    }
  }

  /**
   * GET /api/v1/watchers/:id/logs
   * Returns recent logs for a specific watcher.
   */
  async getWatcherLogs(req: Request, res: Response) {
    try {
      const { id } = req.params;
      const limit = Number(req.query.limit) || 50;
      const result = await this.getMcpResult('get_watcher_logs', { id, limit });
      
      res.json({
        data: result.logs,
        meta: { total: result.total, watcher_id: id },
      });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch watcher logs via MCP' } });
    }
  }

  /**
   * POST /api/v1/watchers/:id/start
   * Starts a watcher subprocess via MCP.
   */
  async startWatcher(req: Request, res: Response): Promise<any> {
    try {
      const { id } = req.params;
      const result = await this.getMcpResult('start_watcher', { id });

      res.json({
        data: {
          success: result.success,
          message: result.message,
          pid: result.pid,
          watcher_id: id,
        },
      });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to start watcher via MCP' } });
    }
  }

  /**
   * POST /api/v1/watchers/start-all
   * Starts run_master.py via MCP.
   */
  async startAll(_req: Request, res: Response): Promise<any> {
    try {
      const result = await this.getMcpResult('start_all_watchers');

      res.json({
        data: {
          success: result.success,
          message: result.message,
          pid: result.pid,
        },
      });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to start all watchers via MCP' } });
    }
  }
}

export const watcherController = new WatcherController();
export default watcherController;
