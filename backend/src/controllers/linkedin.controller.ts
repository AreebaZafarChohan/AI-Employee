/**
 * LinkedIn Controller
 * Uses MCP LinkedIn Server for publishing and scheduling posts.
 */

import { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import { mcpClientService } from '../services/mcp-client.service';
import { logger } from '../lib/logger';

const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');
const VAULT_PATH = process.env.VAULT_PATH || path.join(ROOT_PATH, 'AI-Employee-Vault');
const LINKEDIN_SERVER_PATH = path.join(ROOT_PATH, 'mcp', 'linkedin-server', 'src', 'index.js');

export class LinkedInController {
  private async getMcpResult(toolName: string, toolArgs: any = {}) {
    try {
      const response = await mcpClientService.callTool(
        'linkedin-server',
        'node',
        [LINKEDIN_SERVER_PATH],
        toolName,
        toolArgs
      );

      if (response.isError) {
        throw new Error(JSON.stringify(response.content));
      }

      const content = (response.content as any[])[0];
      if (content && content.type === 'text') {
        return JSON.parse(content.text);
      }
      return null;
    } catch (error) {
      logger.error(`MCP LinkedIn Error calling ${toolName}:`, error);
      throw error;
    }
  }

  /**
   * Get LinkedIn connections (Placeholder - could be an MCP tool)
   */
  async getConnections(_req: Request, res: Response) {
    try {
      // Mock data for now
      const connections = [
        { id: 'conn_1', name: 'John Doe', headline: 'CEO at Tech Corp', connectedAt: new Date().toISOString() },
        { id: 'conn_2', name: 'Jane Smith', headline: 'Marketing Director', connectedAt: new Date().toISOString() },
      ];
      res.json({ data: connections });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch LinkedIn connections' });
    }
  }

  /**
   * Get LinkedIn messages from Needs_Action folder
   */
  async getMessages(_req: Request, res: Response) {
    try {
      const needsActionDir = path.join(VAULT_PATH, 'Needs_Action');
      if (!fs.existsSync(needsActionDir)) return res.json({ data: [] });

      const files = fs.readdirSync(needsActionDir)
        .filter(f => f.endsWith('.md'))
        .map(f => {
          const content = fs.readFileSync(path.join(needsActionDir, f), 'utf-8');
          const metadata = this.parseMarkdownMetadata(content);
          return {
            id: f.replace('.md', ''),
            from: { id: metadata.sender_id || 'unknown', name: metadata.sender || 'Unknown' },
            content: content.split('---\n\n')[1] || '',
            timestamp: metadata.timestamp || new Date().toISOString(),
            read: metadata.status === 'read',
            type: metadata.action_type || 'message',
            riskLevel: metadata.risk_level || 'medium',
          };
        });

      files.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      res.json({ data: files });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch LinkedIn messages' });
    }
  }

  /**
   * Get LinkedIn posts from Needs_Action folder
   */
  async getPosts(_req: Request, res: Response) {
    try {
      const needsActionDir = path.join(VAULT_PATH, 'Needs_Action');
      if (!fs.existsSync(needsActionDir)) return res.json({ data: [] });

      const files = fs.readdirSync(needsActionDir)
        .filter(f => f.endsWith('.md'))
        .map(f => {
          const content = fs.readFileSync(path.join(needsActionDir, f), 'utf-8');
          const metadata = this.parseMarkdownMetadata(content);
          return {
            id: f.replace('.md', ''),
            content: content.split('---\n\n')[1] || '',
            scheduledFor: metadata.scheduled_for || metadata.timestamp,
            status: metadata.status || 'draft',
            riskLevel: metadata.risk_level || 'medium',
            createdAt: metadata.timestamp || new Date().toISOString(),
          };
        })
        .filter(p => p.content.toLowerCase().includes('linkedin') || p.content.toLowerCase().includes('post'));

      res.json({ data: files });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch LinkedIn posts' });
    }
  }

  /**
   * Create/schedule a LinkedIn post via MCP
   */
  async createPost(req: Request, res: Response) {
    try {
      const { content, scheduledFor, hashtags } = req.body;

      if (!content) return res.status(400).json({ error: 'Content is required' });

      let result;
      if (scheduledFor) {
        result = await this.getMcpResult('schedule_post', { content, scheduledTime: scheduledFor, hashtags });
      } else {
        result = await this.getMcpResult('publish_post', { content, hashtags });
      }

      res.json({
        data: {
          success: result.success || (result.status !== 'error'),
          postId: result.postId || `post_${Date.now()}`,
          status: scheduledFor ? 'scheduled' : 'published',
          message: result.message,
        },
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to create LinkedIn post via MCP' });
    }
  }

  /**
   * Get LinkedIn status
   */
  async getStatus(_req: Request, res: Response) {
    try {
      const needsActionDir = path.join(VAULT_PATH, 'Needs_Action');
      const pendingCount = fs.existsSync(needsActionDir)
        ? fs.readdirSync(needsActionDir).filter(f => f.endsWith('.md')).length
        : 0;

      res.json({
        data: {
          status: 'active',
          pendingActions: pendingCount,
          lastSync: new Date().toISOString(),
        },
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to get LinkedIn status' });
    }
  }

  private parseMarkdownMetadata(content: string): Record<string, string> {
    const match = content.match(/---\n([\s\S]*?)\n---/);
    if (!match) return {};
    const metadata: Record<string, string> = {};
    match[1].split('\n').forEach(line => {
      const [key, value] = line.split(':').map(s => s.trim());
      if (key && value) metadata[key] = value.replace(/['"]/g, '');
    });
    return metadata;
  }
}

export const linkedInController = new LinkedInController();
export default linkedInController;
