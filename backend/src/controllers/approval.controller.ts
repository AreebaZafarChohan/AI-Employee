/**
 * Approval Metrics Controller — Silver Tier
 * Reads Pending_Approval/ directory and returns metrics.
 */

import { Request, Response, NextFunction } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'yaml';

const VAULT_PATH = process.env.VAULT_PATH || path.join(__dirname, '..', '..', '..', 'AI-Employee-Vault');
const PENDING_DIR = path.join(VAULT_PATH, 'Pending_Approval');

function parseFrontmatter(content: string): Record<string, unknown> {
  const match = content.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!match) return {};
  try { return yaml.parse(match[1]) || {}; } catch { return {}; }
}

export class ApprovalController {
  /**
   * GET /api/v1/approvals/metrics
   */
  async getMetrics(_req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const APPROVED_DIR = path.join(VAULT_PATH, 'Approved');
      const REJECTED_DIR = path.join(VAULT_PATH, 'Rejected');
      const NEEDS_ACTION_DIR = path.join(VAULT_PATH, 'Needs_Action');

      const pendingFiles = fs.existsSync(PENDING_DIR) ? fs.readdirSync(PENDING_DIR).filter((f) => f.endsWith('.md')) : [];
      const needsActionFiles = fs.existsSync(NEEDS_ACTION_DIR) ? fs.readdirSync(NEEDS_ACTION_DIR).filter((f) => f.endsWith('.md')) : [];
      const approvedFiles = fs.existsSync(APPROVED_DIR) ? fs.readdirSync(APPROVED_DIR).filter((f) => f.endsWith('.md')) : [];
      const rejectedFiles = fs.existsSync(REJECTED_DIR) ? fs.readdirSync(REJECTED_DIR).filter((f) => f.endsWith('.md')) : [];

      const riskBreakdown = { low: 0, medium: 0, high: 0 };
      let oldestTime: Date | null = null;
      let overdueCount = 0;
      const now = Date.now();
      const OVERDUE_MS = 24 * 60 * 60 * 1000; // 24h

      const allPendingFiles = [...pendingFiles.map(f => path.join(PENDING_DIR, f)), ...needsActionFiles.map(f => path.join(NEEDS_ACTION_DIR, f))];

      for (const filePath of allPendingFiles) {
        try {
          const raw = fs.readFileSync(filePath, 'utf-8');
          const meta = parseFrontmatter(raw);
          const risk = String(meta.risk_level || 'medium').toLowerCase() as keyof typeof riskBreakdown;
          if (risk in riskBreakdown) riskBreakdown[risk]++;

          const createdAt = meta.created_at ? new Date(String(meta.created_at)) : null;
          if (createdAt) {
            if (!oldestTime || createdAt < oldestTime) oldestTime = createdAt;
            if (now - createdAt.getTime() > OVERDUE_MS) overdueCount++;
          }
        } catch { /* skip unreadable */ }
      }

      const oldestAge = oldestTime ? Math.round((now - oldestTime.getTime()) / 60000) : null;

      res.status(200).json({
        data: {
          count: allPendingFiles.length,
          approvedCount: approvedFiles.length,
          rejectedCount: rejectedFiles.length,
          riskBreakdown,
          oldestAge, // minutes
          overdueCount,
        },
        meta: { timestamp: new Date().toISOString() },
      });
    } catch (error) {
      _next(error);
    }
  }
}

export const approvalController = new ApprovalController();
export default approvalController;
