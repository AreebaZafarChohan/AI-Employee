/**
 * Shared .env loader — no external deps
 */
import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));

export function loadEnv() {
  for (const p of [
    resolve(__dirname, '..', '.env'),
    resolve(__dirname, '..', '..', '.env'),
  ]) {
    try {
      for (const line of readFileSync(p, 'utf-8').split('\n')) {
        const t = line.trim();
        if (!t || t.startsWith('#')) continue;
        const eq = t.indexOf('=');
        if (eq === -1) continue;
        const k = t.slice(0, eq).trim();
        if (!process.env[k]) process.env[k] = t.slice(eq + 1).trim();
      }
      return p;
    } catch { /* next */ }
  }
  return null;
}
