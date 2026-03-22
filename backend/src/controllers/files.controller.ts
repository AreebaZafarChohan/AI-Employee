/**
 * Files Controller
 * Handles file operations from the vault (Pending_Approval, Approved, etc.)
 */

import { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';

const VAULT_PATH = process.env.VAULT_PATH || path.join(process.cwd(), '..', 'AI-Employee-Vault');

export class FilesController {
  /**
   * Get files from Pending_Approval folder
   */
  async getPending(_req: Request, res: Response) {
    try {
      const pendingDir = path.join(VAULT_PATH, 'Pending_Approval');
      
      if (!fs.existsSync(pendingDir)) {
        return res.json({
          data: [],
        });
      }

      const files = fs.readdirSync(pendingDir)
        .filter(f => f.endsWith('.md'))
        .map(f => {
          const filePath = path.join(pendingDir, f);
          const stats = fs.statSync(filePath);
          const content = fs.readFileSync(filePath, 'utf-8');
          const metadata = this.parseMarkdownMetadata(content);
          
          return {
            id: f.replace('.md', ''),
            path: filePath,
            name: f,
            type: this.getFileType(metadata),
            size: stats.size,
            createdAt: stats.birthtime.toISOString(),
            modifiedAt: stats.mtime.toISOString(),
            classification: metadata.classification || 'general',
            riskLevel: metadata.risk_level || 'medium',
            actionType: metadata.action_type || 'unknown',
          };
        });

      // Sort by modified date descending
      files.sort((a, b) => 
        new Date(b.modifiedAt).getTime() - new Date(a.modifiedAt).getTime()
      );

      res.json({
        data: files,
      });
    } catch (error) {
      console.error('Error fetching pending files:', error);
      res.status(500).json({
        error: 'Failed to fetch pending files',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
      return;
    }
  }

  /**
   * Get file details
   */
  async getFile(req: Request, res: Response) {
    try {
      const { path: filePath } = req.params;
      const decodedPath = decodeURIComponent(filePath);
      
      if (!fs.existsSync(decodedPath)) {
        return res.status(404).json({
          error: 'File not found',
        });
      }

      const stats = fs.statSync(decodedPath);
      const content = fs.readFileSync(decodedPath, 'utf-8');
      const metadata = this.parseMarkdownMetadata(content);

      res.json({
        data: {
          id: path.basename(decodedPath, '.md'),
          path: decodedPath,
          name: path.basename(decodedPath),
          type: this.getFileType(metadata),
          size: stats.size,
          createdAt: stats.birthtime.toISOString(),
          modifiedAt: stats.mtime.toISOString(),
          classification: metadata.classification || 'general',
          riskLevel: metadata.risk_level || 'medium',
          content: content.split('---\n\n')[1] || '',
          metadata,
        },
      });
    } catch (error) {
      console.error('Error fetching file:', error);
      res.status(500).json({
        error: 'Failed to fetch file',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
      return;
    }
  }

  /**
   * Approve a file (move to Approved folder)
   */
  async approve(req: Request, res: Response) {
    try {
      const { path: filePath } = req.params;
      const decodedPath = decodeURIComponent(filePath);
      
      if (!fs.existsSync(decodedPath)) {
        return res.status(404).json({
          error: 'File not found',
        });
      }

      const approvedDir = path.join(VAULT_PATH, 'Approved');
      if (!fs.existsSync(approvedDir)) {
        fs.mkdirSync(approvedDir, { recursive: true });
      }

      const fileName = path.basename(decodedPath);
      const destPath = path.join(approvedDir, fileName);
      
      // Move file
      fs.renameSync(decodedPath, destPath);

      console.log(`[Files] Approved: ${fileName}`);

      res.json({
        data: {
          success: true,
          message: 'File approved successfully',
        },
      });
    } catch (error) {
      console.error('Error approving file:', error);
      res.status(500).json({
        error: 'Failed to approve file',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
      return;
    }
  }

  /**
   * Reject a file (move to Rejected folder or delete)
   */
  async reject(req: Request, res: Response) {
    try {
      const { path: filePath, reason } = req.body;
      const decodedPath = decodeURIComponent(filePath);
      
      if (!fs.existsSync(decodedPath)) {
        return res.status(404).json({
          error: 'File not found',
        });
      }

      const rejectedDir = path.join(VAULT_PATH, 'Rejected');
      if (!fs.existsSync(rejectedDir)) {
        fs.mkdirSync(rejectedDir, { recursive: true });
      }

      const fileName = path.basename(decodedPath);
      const destPath = path.join(rejectedDir, fileName);
      
      // Add rejection reason to file
      const content = fs.readFileSync(decodedPath, 'utf-8');
      const rejectedContent = `${content}\n\n---\nRejected: ${new Date().toISOString()}\nReason: ${reason || 'No reason provided'}\n`;
      fs.writeFileSync(destPath, rejectedContent);
      
      // Remove original
      fs.unlinkSync(decodedPath);

      console.log(`[Files] Rejected: ${fileName}`);

      res.json({
        data: {
          success: true,
          message: 'File rejected successfully',
        },
      });
    } catch (error) {
      console.error('Error rejecting file:', error);
      res.status(500).json({
        error: 'Failed to reject file',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
      return;
    }
  }

  /**
   * Get files statistics
   */
  async getStats(_req: Request, res: Response) {
    try {
      const folders = ['Pending_Approval', 'Approved', 'Rejected', 'Needs_Action'];
      const stats: Record<string, number> = {};

      for (const folder of folders) {
        const folderPath = path.join(VAULT_PATH, folder);
        stats[folder] = fs.existsSync(folderPath)
          ? fs.readdirSync(folderPath).filter(f => f.endsWith('.md')).length
          : 0;
      }

      res.json({
        data: {
          total: Object.values(stats).reduce((a, b) => a + b, 0),
          byFolder: stats,
          lastUpdated: new Date().toISOString(),
        },
      });
    } catch (error) {
      console.error('Error fetching file stats:', error);
      res.status(500).json({
        error: 'Failed to fetch file stats',
        message: error instanceof Error ? error.message : 'Unknown error',
      });
      return;
    }
  }

  /**
   * Parse markdown metadata from file content
   */
  private parseMarkdownMetadata(content: string): Record<string, string> {
    const match = content.match(/---\n([\s\S]*?)\n---/);
    if (!match) return {};

    const metadata: Record<string, string> = {};
    const lines = match[1].split('\n');
    
    for (const line of lines) {
      const [key, value] = line.split(':').map(s => s.trim());
      if (key && value) {
        metadata[key] = value.replace(/['"]/g, '');
      }
    }

    return metadata;
  }

  /**
   * Get file type from metadata
   */
  private getFileType(metadata: Record<string, string>): string {
    const actionType = metadata.action_type || '';
    if (actionType.includes('email')) return 'email';
    if (actionType.includes('whatsapp')) return 'whatsapp';
    if (actionType.includes('linkedin')) return 'linkedin';
    if (actionType.includes('file')) return 'file';
    return 'general';
  }
}

export const filesController = new FilesController();
