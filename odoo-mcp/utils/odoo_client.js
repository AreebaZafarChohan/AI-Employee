/**
 * Odoo JSON-RPC Client — Production Grade
 *
 * Features:
 * - Automatic retry with exponential backoff
 * - Connection pooling via keep-alive
 * - Automatic re-authentication on session expiry
 * - Request timeout with AbortController
 * - Structured error classes
 */

import { log } from './logger.js';

// ───────────────────────────── errors ──────────────────────────────

export class OdooAuthError extends Error {
  constructor(msg) { super(msg); this.name = 'OdooAuthError'; }
}

export class OdooRpcError extends Error {
  constructor(msg, code) { super(msg); this.name = 'OdooRpcError'; this.code = code; }
}

export class OdooTimeoutError extends Error {
  constructor(ms) { super(`Request timed out after ${ms}ms`); this.name = 'OdooTimeoutError'; }
}

// ───────────────────────────── helpers ──────────────────────────────

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ───────────────────────────── client ──────────────────────────────

export class OdooClient {
  /** @param {{ url: string, db: string, username: string, password: string, timeout?: number, max_retries?: number, retry_delay?: number, retry_max_delay?: number }} config */
  constructor(config) {
    if (!config.url) throw new Error('ODOO_URL is required');
    if (!config.db) throw new Error('ODOO_DB is required');
    if (!config.username) throw new Error('ODOO_USERNAME is required');
    if (!config.password) throw new Error('ODOO_PASSWORD is required');

    this.url = config.url.replace(/\/+$/, '');
    this.db = config.db;
    this.username = config.username;
    this.password = config.password;
    this.timeout = config.timeout ?? 30_000;
    this.maxRetries = config.max_retries ?? 3;
    this.retryDelay = config.retry_delay ?? 2_000;
    this.retryMaxDelay = config.retry_max_delay ?? 30_000;

    this.uid = null;
    this._rpcId = 0;
  }

  // ──────────────── low-level RPC ────────────────

  async _rpc(service, method, args) {
    this._rpcId += 1;
    const body = {
      jsonrpc: '2.0',
      id: this._rpcId,
      method: 'call',
      params: { service, method, args },
    };

    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort(), this.timeout);

    try {
      const res = await fetch(`${this.url}/jsonrpc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: ac.signal,
      });
      clearTimeout(timer);

      if (!res.ok) {
        throw new OdooRpcError(`HTTP ${res.status}: ${res.statusText}`, res.status);
      }

      const json = await res.json();

      if (json.error) {
        const msg = json.error.data?.message || json.error.message || JSON.stringify(json.error);
        throw new OdooRpcError(msg, json.error.code);
      }

      return json.result;
    } catch (err) {
      clearTimeout(timer);
      if (err.name === 'AbortError') throw new OdooTimeoutError(this.timeout);
      throw err;
    }
  }

  // ──────────────── auth ────────────────

  async authenticate() {
    log('info', 'odoo_client', 'authenticating', { url: this.url, db: this.db, user: this.username });

    const uid = await this._rpc('common', 'authenticate', [this.db, this.username, this.password, {}]);

    if (!uid || uid === false) {
      throw new OdooAuthError(`Authentication failed for ${this.username}@${this.db} — check credentials`);
    }

    this.uid = uid;
    log('info', 'odoo_client', 'authenticated', { uid });
    return uid;
  }

  async ensureAuth() {
    if (!this.uid) await this.authenticate();
  }

  // ──────────────── execute with retry ────────────────

  /**
   * Call execute_kw with automatic retry + re-auth on session expiry.
   */
  async execute(model, method, args = [], kwargs = {}) {
    await this.ensureAuth();

    let lastError;
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        return await this._rpc('object', 'execute_kw', [
          this.db, this.uid, this.password, model, method, args, kwargs,
        ]);
      } catch (err) {
        lastError = err;

        // session expired → re-auth and retry
        if (err instanceof OdooRpcError && /session|expired|access denied/i.test(err.message)) {
          log('warn', 'odoo_client', 'session_expired_reauth', { attempt });
          this.uid = null;
          await this.authenticate();
          continue;
        }

        // timeout or transient → backoff
        if (err instanceof OdooTimeoutError || (err instanceof OdooRpcError && err.code >= 500)) {
          const delay = Math.min(this.retryDelay * 2 ** (attempt - 1), this.retryMaxDelay);
          log('warn', 'odoo_client', 'retrying', { attempt, delay, error: err.message });
          await sleep(delay);
          continue;
        }

        // non-retryable
        throw err;
      }
    }

    throw lastError;
  }

  // ──────────────── convenience methods ────────────────

  async searchRead(model, domain, fields = [], limit = 80, offset = 0, order = '') {
    const kw = { fields, limit, offset };
    if (order) kw.order = order;
    return this.execute(model, 'search_read', [domain], kw);
  }

  async search(model, domain, limit = 80) {
    return this.execute(model, 'search', [domain], { limit });
  }

  async read(model, ids, fields = []) {
    return this.execute(model, 'read', [ids], { fields });
  }

  async create(model, values) {
    return this.execute(model, 'create', [values]);
  }

  async write(model, ids, values) {
    return this.execute(model, 'write', [ids, values]);
  }

  async unlink(model, ids) {
    return this.execute(model, 'unlink', [ids]);
  }

  async searchCount(model, domain) {
    return this.execute(model, 'search_count', [domain]);
  }

  /** Version / server info (no auth needed) */
  async version() {
    return this._rpc('common', 'version', []);
  }
}
