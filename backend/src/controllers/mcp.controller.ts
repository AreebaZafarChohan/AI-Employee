/**
 * MCP Health Controller — Silver Tier
 * Returns health/status of configured MCP servers.
 */

import { Request, Response, NextFunction } from 'express';
import * as fs from 'fs';
import * as path from 'path';

interface McpServerStatus {
  name: string;
  type: 'stdio' | 'http';
  status: 'healthy' | 'unhealthy' | 'unknown';
  path?: string;
  lastChecked: string;
}

const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');

const MCP_SERVERS = [
  { name: 'watcher-server', type: 'stdio' as const, path: 'mcp/watcher-server/src/index.js' },
  { name: 'whatsapp-server', type: 'stdio' as const, path: 'mcp/whatsapp-server/src/index.js' },
  { name: 'linkedin-server', type: 'stdio' as const, path: 'mcp/linkedin-server/src/index.js' },
  { name: 'odoo-server', type: 'stdio' as const, path: 'mcp/odoo-server/src/index.js' },
  { name: 'email-server', type: 'stdio' as const, path: 'mcp/email-server/src/index.js' },
  { name: 'twitter-server', type: 'stdio' as const, path: 'mcp/twitter-server/src/index.js' },
];

async function checkServer(server: typeof MCP_SERVERS[0]): Promise<McpServerStatus> {
  const fullPath = path.join(ROOT_PATH, server.path);
  const exists = fs.existsSync(fullPath);
  
  return {
    name: server.name,
    type: server.type,
    status: exists ? 'healthy' : 'unhealthy',
    path: server.path,
    lastChecked: new Date().toISOString(),
  };
}

export class McpController {
  /**
   * GET /api/v1/system/mcp-health
   */
  async getMcpHealth(_req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const results = await Promise.all(MCP_SERVERS.map(checkServer));
      const healthy = results.filter((r) => r.status === 'healthy').length;

      res.status(200).json({
        data: {
          servers: results,
          summary: {
            total: results.length,
            healthy,
            unhealthy: results.length - healthy,
          },
        },
        meta: { timestamp: new Date().toISOString() },
      });
    } catch (error) {
      _next(error);
    }
  }
}

export const mcpController = new McpController();
export default mcpController;
