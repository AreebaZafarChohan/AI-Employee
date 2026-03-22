/**
 * Structured JSONL audit logger with posting log for vault integration
 */
import { appendFileSync, mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const LOG_DIR = join(__dirname, '..', 'logs');
mkdirSync(LOG_DIR, { recursive: true });

export function log(level, platform, action, meta = {}) {
  const entry = { ts: new Date().toISOString(), level, platform, action, ...meta };
  console.error(`[${level.toUpperCase()}] ${platform}: ${action}`);
  try {
    appendFileSync(join(LOG_DIR, 'social-audit.jsonl'), JSON.stringify(entry) + '\n');
  } catch { /* non-fatal */ }
}

export function auditStart(platform, tool, params, { dry_run = false } = {}) {
  const start = Date.now();
  const id = `${platform}-${tool}-${start}-${Math.random().toString(36).slice(2, 6)}`;
  log('audit', platform, dry_run ? 'dry_run' : 'invoked', { id, tool, params });
  return {
    id,
    success(result) {
      log('audit', platform, 'success', { id, tool, ms: Date.now() - start });
    },
    error(err) {
      log('error', platform, 'error', { id, tool, ms: Date.now() - start, error: err?.message });
    },
  };
}
