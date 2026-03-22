/**
 * Audit Logger
 *
 * Structured JSON audit logging with rotation support.
 * All MCP tool invocations are logged for compliance and debugging.
 */

import { appendFileSync, mkdirSync, statSync, renameSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const LOG_DIR = join(__dirname, '..', 'logs');
const MAX_LOG_SIZE = 10 * 1024 * 1024; // 10 MB

mkdirSync(LOG_DIR, { recursive: true });

function logPath() {
  return join(LOG_DIR, 'audit.jsonl');
}

function rotateMaybe() {
  try {
    const stat = statSync(logPath());
    if (stat.size >= MAX_LOG_SIZE) {
      const ts = new Date().toISOString().replace(/[:.]/g, '-');
      renameSync(logPath(), join(LOG_DIR, `audit-${ts}.jsonl`));
    }
  } catch {
    // file doesn't exist yet — fine
  }
}

/**
 * @param {'info'|'warn'|'error'|'audit'} level
 * @param {string} tool   - MCP tool name
 * @param {string} action - what happened (invoked / success / error / dry_run)
 * @param {Record<string, unknown>} meta
 */
export function log(level, tool, action, meta = {}) {
  const entry = {
    ts: new Date().toISOString(),
    level,
    tool,
    action,
    ...meta,
  };

  // always stderr for MCP (stdout is the MCP protocol channel)
  const line = JSON.stringify(entry);
  console.error(`[${level.toUpperCase()}] ${tool}: ${action}`);

  rotateMaybe();
  try {
    appendFileSync(logPath(), line + '\n', 'utf-8');
  } catch {
    // non-fatal — don't crash the server for logging failures
  }
}

/**
 * Audit-log a tool invocation.
 * Returns a finish() callback the caller invokes with the result.
 */
export function auditStart(tool, params, { dry_run = false } = {}) {
  const start = Date.now();
  const id = `${tool}-${start}-${Math.random().toString(36).slice(2, 8)}`;
  log('audit', tool, dry_run ? 'dry_run_invoked' : 'invoked', { id, params });

  return {
    id,
    success(result) {
      log('audit', tool, dry_run ? 'dry_run_ok' : 'success', {
        id,
        duration_ms: Date.now() - start,
        result_keys: result ? Object.keys(result) : [],
      });
    },
    error(err) {
      log('error', tool, 'error', {
        id,
        duration_ms: Date.now() - start,
        error: err?.message || String(err),
      });
    },
  };
}
