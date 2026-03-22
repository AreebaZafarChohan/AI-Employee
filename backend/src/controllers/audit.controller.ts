/**
 * Audit Log Controller — Silver Tier
 * Reads audit/log files from the vault's Audit/ and Logs/ directories.
 */

import { Request, Response, NextFunction } from 'express';
import * as fs from 'fs';
import * as path from 'path';

const VAULT_PATH = process.env.VAULT_PATH || path.join(__dirname, '..', '..', '..', 'AI-Employee-Vault');
const AUDIT_DIR = path.join(VAULT_PATH, 'Audit');
const LOGS_DIR = path.join(VAULT_PATH, 'Logs');

interface AuditEntry {
  timestamp: string;
  [key: string]: unknown;
}

function readJsonLogs(dir: string): AuditEntry[] {
  const entries: AuditEntry[] = [];
  if (!fs.existsSync(dir)) return entries;

  const files = fs.readdirSync(dir)
    .filter((f) => f.endsWith('.json') || f.endsWith('.log'))
    .sort()
    .reverse()
    .slice(0, 30); // last 30 files max

  for (const file of files) {
    try {
      const raw = fs.readFileSync(path.join(dir, file), 'utf-8').trim();
      if (file.endsWith('.json')) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) entries.push(...parsed);
        else entries.push(parsed);
      } else {
        // .log files: one JSON object per line
        for (const line of raw.split('\n')) {
          if (line.trim()) {
            try { entries.push(JSON.parse(line.trim())); } catch { /* skip malformed lines */ }
          }
        }
      }
    } catch { /* skip unreadable files */ }
  }

  return entries.sort((a, b) =>
    (b.timestamp || '').localeCompare(a.timestamp || '')
  );
}

export class AuditController {
  /**
   * GET /api/v1/audit-logs
   */
  async getAuditLogs(req: Request, res: Response, _next: NextFunction): Promise<void> {
    try {
      const limit = Math.min(Number(req.query.limit) || 100, 500);
      const source = (req.query.source as string) || 'all';

      let entries: AuditEntry[] = [];
      if (source === 'all' || source === 'audit') entries.push(...readJsonLogs(AUDIT_DIR));
      if (source === 'all' || source === 'logs') entries.push(...readJsonLogs(LOGS_DIR));

      // Re-sort combined and limit
      entries.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
      entries = entries.slice(0, limit);

      res.status(200).json({
        data: entries,
        meta: {
          total: entries.length,
          limit,
          source,
          timestamp: new Date().toISOString(),
        },
      });
    } catch (error) {
      _next(error);
    }
  }
}

export const auditController = new AuditController();
export default auditController;
