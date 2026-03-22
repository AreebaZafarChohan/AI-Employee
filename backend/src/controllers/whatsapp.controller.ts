/**
 * WhatsApp Controller
 * Uses MCP WhatsApp Server for sending messages.
 */

import { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import { mcpClientService } from '../services/mcp-client.service';
import { logger } from '../lib/logger';

const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');
const VAULT_PATH = process.env.VAULT_PATH || path.join(ROOT_PATH, 'AI-Employee-Vault');
const WHATSAPP_SERVER_PATH = path.join(ROOT_PATH, 'mcp', 'whatsapp-server', 'src', 'index.js');

export class WhatsAppController {
  private async getMcpResult(toolName: string, toolArgs: any = {}) {
    try {
      const response = await mcpClientService.callTool(
        'whatsapp-server',
        'node',
        [WHATSAPP_SERVER_PATH],
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
      logger.error(`MCP WhatsApp Error calling ${toolName}:`, error);
      throw error;
    }
  }

  /**
   * Get WhatsApp messages from Needs_Action folder (keeps original logic for reading data)
   */
  async getMessages(req: Request, res: Response) {
    try {
      const { page = 1, limit = 50, status } = req.query;
      const pageNum = parseInt(page as string, 10);
      const limitNum = parseInt(limit as string, 10);

      const allMessages = this.readWhatsAppFiles(status as string | undefined);

      const total = allMessages.length;
      const totalPages = Math.ceil(total / limitNum);
      const paginated = allMessages.slice((pageNum - 1) * limitNum, pageNum * limitNum);

      res.json({
        data: paginated,
        meta: { total, page: pageNum, limit: limitNum, totalPages },
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch WhatsApp messages' });
    }
  }

  /**
   * Send WhatsApp message via MCP
   */
  async sendMessage(req: Request, res: Response) {
    try {
      const { recipient, message, dry_run } = req.body;

      if (!recipient || !message) {
        return res.status(400).json({ error: 'Missing recipient or message' });
      }

      const result = await this.getMcpResult('send_message', { 
        recipient, 
        instruction: message,
        dry_run: dry_run || false
      });

      const messageId = `msg_${Date.now()}`;

      // Save outbound message record to Done/
      if (result.success) {
        const doneDir = path.join(VAULT_PATH, 'Done');
        if (!fs.existsSync(doneDir)) fs.mkdirSync(doneDir, { recursive: true });
        const now = new Date().toISOString();
        const slug = recipient.replace(/[^a-z0-9]/gi, '-').toLowerCase().slice(0, 40);
        const ts = now.replace(/[-:T]/g, '').slice(0, 14);
        const doneContent = [
          '---',
          'type: whatsapp',
          'direction: outbound',
          `sender: "AI Employee"`,
          `recipient: "${recipient}"`,
          `message: "${(result.message || message).replace(/\n/g, ' ')}"`,
          `timestamp: "${now}"`,
          'status: sent',
          '---',
          '',
          `# WhatsApp Sent to ${recipient}`,
          '',
          result.message || message,
        ].join('\n');
        fs.writeFileSync(path.join(doneDir, `whatsapp-sent-${slug}-${ts}.md`), doneContent, 'utf-8');
      }

      res.json({
        data: {
          success: result.success,
          messageId,
          generated_message: result.message,
          status: result.success ? 'sent' : 'error',
        },
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to send WhatsApp message via MCP' });
    }
  }

  /**
   * Get pending WhatsApp messages (status = pending)
   */
  async getPending(req: Request, res: Response) {
    try {
      const messages = this.readWhatsAppFiles('pending');
      res.json({ data: messages });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch pending messages' });
    }
  }

  /**
   * Get WhatsApp contacts (extracted from message senders)
   */
  async getContacts(_req: Request, res: Response) {
    try {
      const messages = this.readWhatsAppFiles();
      const contactMap = new Map<string, { name: string; lastMessage: string; lastTimestamp: string }>();
      for (const msg of messages) {
        if (!contactMap.has(msg.from) || new Date(msg.timestamp) > new Date(contactMap.get(msg.from)!.lastTimestamp)) {
          contactMap.set(msg.from, { name: msg.from, lastMessage: msg.content, lastTimestamp: msg.timestamp });
        }
      }
      const contacts = Array.from(contactMap.entries()).map(([name, data]) => ({
        id: name.replace(/\s+/g, '-').toLowerCase(),
        name,
        lastMessage: data.lastMessage,
        lastTimestamp: data.lastTimestamp,
      }));
      res.json({ data: contacts });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch contacts' });
    }
  }

  /**
   * Approve a pending WhatsApp message
   */
  async approveMessage(req: Request, res: Response) {
    try {
      const { message_id, reply_content } = req.body;
      if (!message_id) return res.status(400).json({ error: 'Missing message_id' });

      const needsActionDir = path.join(VAULT_PATH, 'Needs_Action');
      const doneDir = path.join(VAULT_PATH, 'Done');
      if (!fs.existsSync(doneDir)) fs.mkdirSync(doneDir, { recursive: true });

      // Move file from Needs_Action to Done
      const srcFile = path.join(needsActionDir, `${message_id}.md`);
      const msgDir = path.join(needsActionDir, 'messages', `${message_id}.md`);
      const source = fs.existsSync(srcFile) ? srcFile : fs.existsSync(msgDir) ? msgDir : null;

      // If reply_content provided, send the reply via MCP
      let sendResult = null;
      if (reply_content && source) {
        const rawContent = fs.readFileSync(source, 'utf-8');
        const metadata = this.parseMarkdownMetadata(rawContent);
        const recipient = metadata.from || metadata.sender || '';
        if (recipient) {
          try {
            sendResult = await this.getMcpResult('send_message', {
              recipient,
              instruction: reply_content,
              dry_run: false,
            });
          } catch (err) {
            logger.warn('Failed to send reply via MCP, still moving to Done', { err });
          }
        }
      }

      if (source) {
        fs.renameSync(source, path.join(doneDir, `${message_id}.md`));
      }

      res.json({ data: { success: true, message_id, action: 'approved', replySent: !!sendResult } });
    } catch (error) {
      res.status(500).json({ error: 'Failed to approve message' });
    }
  }

  /**
   * Reject a pending WhatsApp message
   */
  async rejectMessage(req: Request, res: Response) {
    try {
      const { message_id, reason } = req.body;
      if (!message_id) return res.status(400).json({ error: 'Missing message_id' });

      const needsActionDir = path.join(VAULT_PATH, 'Needs_Action');
      const rejectedDir = path.join(VAULT_PATH, 'Rejected');
      if (!fs.existsSync(rejectedDir)) fs.mkdirSync(rejectedDir, { recursive: true });

      const srcFile = path.join(needsActionDir, `${message_id}.md`);
      const msgDir = path.join(needsActionDir, 'messages', `${message_id}.md`);
      const source = fs.existsSync(srcFile) ? srcFile : fs.existsSync(msgDir) ? msgDir : null;

      if (source) {
        fs.renameSync(source, path.join(rejectedDir, `${message_id}.md`));
      }

      res.json({ data: { success: true, message_id, action: 'rejected', reason } });
    } catch (error) {
      res.status(500).json({ error: 'Failed to reject message' });
    }
  }

  /**
   * Get WhatsApp status
   */
  async getStatus(_req: Request, res: Response) {
    try {
      const needsActionDir = path.join(VAULT_PATH, 'Needs_Action');
      const messagesDir = path.join(needsActionDir, 'messages');
      let pendingCount = 0;
      if (fs.existsSync(needsActionDir)) {
        pendingCount += fs.readdirSync(needsActionDir).filter(f => f.startsWith('whatsapp-') && f.endsWith('.md')).length;
      }
      if (fs.existsSync(messagesDir)) {
        pendingCount += fs.readdirSync(messagesDir).filter(f => f.startsWith('whatsapp-') && f.endsWith('.md')).length;
      }

      res.json({
        data: {
          status: 'active',
          pendingMessages: pendingCount,
          lastSync: new Date().toISOString(),
        },
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to get WhatsApp status' });
    }
  }

  private readWhatsAppFiles(filterStatus?: string) {
    const needsActionDir = path.join(VAULT_PATH, 'Needs_Action');
    const dirs = [needsActionDir, path.join(needsActionDir, 'messages')];
    const messages: any[] = [];

    for (const dir of dirs) {
      if (!fs.existsSync(dir)) continue;
      const files = fs.readdirSync(dir).filter(f => f.startsWith('whatsapp-') && f.endsWith('.md'));
      for (const f of files) {
        const raw = fs.readFileSync(path.join(dir, f), 'utf-8');
        const metadata = this.parseMarkdownMetadata(raw);
        const bodyMatch = raw.split('---\n\n');
        const msg = {
          id: f.replace('.md', ''),
          from: metadata.sender || metadata.from || 'Unknown',
          to: 'AI Employee',
          content: (bodyMatch[1] || '').trim(),
          timestamp: metadata.timestamp || metadata.date || new Date().toISOString(),
          status: metadata.status || 'received',
          type: (metadata.type || 'text') as string,
          risk_level: metadata.risk_level || 'medium',
        };
        if (!filterStatus || msg.status === filterStatus) {
          messages.push(msg);
        }
      }
    }

    messages.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    return messages;
  }

  private parseMarkdownMetadata(content: string): Record<string, string> {
    const match = content.match(/---\n([\s\S]*?)\n---/);
    if (!match) return {};
    const metadata: Record<string, string> = {};
    match[1].split('\n').forEach(line => {
      const colonIdx = line.indexOf(':');
      if (colonIdx === -1) return;
      const key = line.slice(0, colonIdx).trim();
      const value = line.slice(colonIdx + 1).trim().replace(/['"]/g, '');
      if (key && value) metadata[key] = value;
    });
    // Map watcher fields to expected fields
    if (metadata.received && !metadata.timestamp) metadata.timestamp = metadata.received;
    if (metadata.sender && !metadata.from) metadata.from = metadata.sender;
    // Derive status from requires_approval
    if (metadata.requires_approval === 'true' && !metadata.status) metadata.status = 'pending';
    return metadata;
  }
}

export const whatsappController = new WhatsAppController();
export default whatsappController;
