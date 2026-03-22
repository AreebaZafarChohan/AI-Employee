/**
 * Vault Controller
 * Handles all vault-related operations including Gmail, WhatsApp, and LinkedIn items.
 */

import { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import { exec } from 'child_process';

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), '..', 'AI-Employee-Vault');

export type VaultStatus = 'pending' | 'approved' | 'rejected' | 'done' | 'needs_action';
export type VaultChannel = 'whatsapp' | 'gmail' | 'linkedin' | 'plan' | 'general';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface VaultItem {
  filename: string;
  title: string;
  status: VaultStatus;
  channel: VaultChannel;
  risk_level: RiskLevel;
  created_at: string;
  updated_at?: string;
  metadata: Record<string, any>;
  body_preview: string;
}

export class VaultController {
  /**
   * Get items from a specific folder
   */
  async getFolderItems(_req: Request, res: Response, folderName: string, status: VaultStatus) {
    try {
      const folderPath = path.join(VAULT_PATH, folderName);
      
      if (!fs.existsSync(folderPath)) {
        return res.json({ data: [] });
      }

      const files = fs.readdirSync(folderPath)
        .filter(f => f.endsWith('.md'))
        .map(f => {
          const filePath = path.join(folderPath, f);
          const stats = fs.statSync(filePath);
          const content = fs.readFileSync(filePath, 'utf-8');
          const { metadata, body } = this.parseMarkdown(content);
          
          const channel = this.determineChannel(metadata, f);
          
          return {
            filename: f,
            title: metadata.subject || metadata.title || f.replace('.md', ''),
            status: status,
            channel: channel,
            risk_level: (metadata.risk_level || metadata.priority || 'medium').toLowerCase() as RiskLevel,
            created_at: metadata.created_at || stats.birthtime.toISOString(),
            updated_at: stats.mtime.toISOString(),
            metadata: metadata,
            body_preview: body.substring(0, 200).trim() + (body.length > 200 ? '...' : ''),
          };
        });

      // Sort by created date descending
      files.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      res.json({ data: files });
    } catch (error) {
      console.error(`Error fetching items from ${folderName}:`, error);
      res.status(500).json({
        error: {
          code: 'INTERNAL_ERROR',
          message: `Failed to fetch ${folderName} items`,
        },
      });
    }
  }

  async getNeedsAction(req: Request, res: Response) {
    return this.getFolderItems(req, res, 'Needs_Action', 'needs_action');
  }

  async getPending(req: Request, res: Response) {
    return this.getFolderItems(req, res, 'Pending_Approval', 'pending');
  }

  async getApproved(req: Request, res: Response) {
    return this.getFolderItems(req, res, 'Approved', 'approved');
  }

  async getRejected(req: Request, res: Response) {
    return this.getFolderItems(req, res, 'Rejected', 'rejected');
  }

  async getDone(req: Request, res: Response) {
    return this.getFolderItems(req, res, 'Done', 'done');
  }

  /**
   * Get counts across all folders
   */
  async getCounts(_req: Request, res: Response) {
    try {
      const folders = {
        needs_action: 'Needs_Action',
        pending: 'Pending_Approval',
        approved: 'Approved',
        rejected: 'Rejected',
        done: 'Done'
      };
      
      const counts: Record<string, number> = {};

      for (const [key, folder] of Object.entries(folders)) {
        const folderPath = path.join(VAULT_PATH, folder);
        counts[key] = fs.existsSync(folderPath)
          ? fs.readdirSync(folderPath).filter(f => f.endsWith('.md')).length
          : 0;
      }

      res.json({ data: counts });
    } catch (error) {
      console.error('Error fetching vault counts:', error);
      res.status(500).json({
        error: {
          code: 'INTERNAL_ERROR',
          message: 'Failed to fetch vault counts',
        },
      });
    }
  }

  /**
   * Approve a file
   */
  async approve(req: Request, res: Response) {
    try {
      const { filename } = req.body;
      if (!filename) {
        return res.status(400).json({ error: { code: 'BAD_REQUEST', message: 'Filename is required' } });
      }

      // Try to find file in Pending_Approval or Needs_Action
      const sourceFolders = ['Pending_Approval', 'Needs_Action'];
      let foundPath = '';

      for (const folder of sourceFolders) {
        const p = path.join(VAULT_PATH, folder, filename);
        if (fs.existsSync(p)) {
          foundPath = p;
          break;
        }
      }

      if (!foundPath) {
        return res.status(404).json({ error: { code: 'NOT_FOUND', message: 'File not found' } });
      }

      // Parse file to get metadata
      const content = fs.readFileSync(foundPath, 'utf-8');
      const { metadata } = this.parseMarkdown(content);
      const channel = this.determineChannel(metadata, filename);

      // Perform channel-specific actions
      if (channel === 'gmail' && (metadata.gmail_message_id || metadata.message_id)) {
        const messageId = metadata.gmail_message_id || metadata.message_id;
        const scriptPath = path.resolve(process.cwd(), '..', 'gmail_actions.py');
        console.log(`[Vault] Marking Gmail message ${messageId} as read...`);
        
        // Try 'python' or 'python3'
        const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
        
        exec(`${pythonCmd} "${scriptPath}" mark_as_read --message_id ${messageId}`, (error, stdout, stderr) => {
          if (error) {
            console.error(`[Vault] Error marking Gmail as read: ${error.message}`);
          }
          if (stderr) {
            console.error(`[Vault] Gmail script stderr: ${stderr}`);
          }
          console.log(`[Vault] Gmail script output: ${stdout}`);
        });
      }

      const approvedDir = path.join(VAULT_PATH, 'Approved');
      if (!fs.existsSync(approvedDir)) fs.mkdirSync(approvedDir, { recursive: true });

      const destPath = path.join(approvedDir, filename);
      fs.renameSync(foundPath, destPath);

      res.json({
        data: {
          success: true,
          message: channel === 'gmail' ? 'Email marked as read' : 'File approved',
          filename,
          new_status: 'approved'
        }
      });
    } catch (error) {
      console.error('Error approving file:', error);
      res.status(500).json({
        error: { code: 'INTERNAL_ERROR', message: 'Failed to approve file' }
      });
    }
  }

  /**
   * Reject a file
   */
  async reject(req: Request, res: Response) {
    try {
      const { filename } = req.body;
      if (!filename) {
        return res.status(400).json({ error: { code: 'BAD_REQUEST', message: 'Filename is required' } });
      }

      const sourceFolders = ['Pending_Approval', 'Needs_Action'];
      let foundPath = '';

      for (const folder of sourceFolders) {
        const p = path.join(VAULT_PATH, folder, filename);
        if (fs.existsSync(p)) {
          foundPath = p;
          break;
        }
      }

      if (!foundPath) {
        return res.status(404).json({ error: { code: 'NOT_FOUND', message: 'File not found' } });
      }

      const rejectedDir = path.join(VAULT_PATH, 'Rejected');
      if (!fs.existsSync(rejectedDir)) fs.mkdirSync(rejectedDir, { recursive: true });

      const destPath = path.join(rejectedDir, filename);
      fs.renameSync(foundPath, destPath);

      res.json({
        data: {
          success: true,
          message: 'File rejected',
          filename,
          new_status: 'rejected'
        }
      });
    } catch (error) {
      console.error('Error rejecting file:', error);
      res.status(500).json({
        error: { code: 'INTERNAL_ERROR', message: 'Failed to reject file' }
      });
    }
  }

  /**
   * Helper to determine channel from metadata or filename
   */
  private determineChannel(metadata: any, filename: string): VaultChannel {
    if (metadata.type === 'email' || metadata.source === 'gmail' || filename.startsWith('email-')) return 'gmail';
    if (metadata.type === 'whatsapp' || metadata.source === 'whatsapp' || filename.startsWith('whatsapp-')) return 'whatsapp';
    if (metadata.type === 'linkedin' || metadata.source === 'linkedin' || filename.startsWith('linkedin-')) return 'linkedin';
    if (metadata.type === 'plan' || filename.startsWith('plan-')) return 'plan';
    return 'general';
  }

  /**
   * Helper to parse markdown metadata and body
   */
  private parseMarkdown(content: string): { metadata: Record<string, any>, body: string } {
    const match = content.match(/^---\n([\s\S]*?)\n---/);
    if (!match) return { metadata: {}, body: content };

    const metadata: Record<string, any> = {};
    const lines = match[1].split('\n');
    
    for (const line of lines) {
      const colonIndex = line.indexOf(':');
      if (colonIndex > -1) {
        const key = line.substring(0, colonIndex).trim();
        let value = line.substring(colonIndex + 1).trim();
        // Remove quotes if present
        if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
          value = value.substring(1, value.length - 1);
        }
        metadata[key] = value;
      }
    }

    const body = content.replace(match[0], '').trim();
    return { metadata, body };
  }
}

export const vaultController = new VaultController();
