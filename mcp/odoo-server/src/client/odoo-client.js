/**
 * Odoo Client - JSON-RPC Integration
 * 
 * Connects to Odoo Community Edition via JSON-RPC API
 */

import fetch from 'node-fetch';

export class OdooClient {
  constructor(config) {
    this.url = config.url;
    this.db = config.db;
    this.username = config.username;
    this.password = config.password;
    this.uid = null;
    this.timeout = config.timeout || 30000;
  }

  /**
   * Authenticate with Odoo
   */
  async authenticate() {
    try {
      const response = await fetch(`${this.url}/jsonrpc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: {
            service: 'common',
            method: 'authenticate',
            args: [this.db, this.username, this.password, {}]
          }
        })
      });

      const result = await response.json();
      
      if (result.error) {
        throw new Error(`Odoo authentication failed: ${result.error.message}`);
      }

      this.uid = result.result;
      return this.uid;
    } catch (error) {
      throw new Error(`Odoo authentication error: ${error.message}`);
    }
  }

  /**
   * Execute Odoo method
   */
  async execute(model, method, args = [], kwargs = {}) {
    if (!this.uid) {
      await this.authenticate();
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      const response = await fetch(`${this.url}/jsonrpc`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: {
            service: 'object',
            method: 'execute_kw',
            args: [this.db, this.uid, this.password, model, method, args],
            kwargs: kwargs
          }
        })
      });

      clearTimeout(timeoutId);

      const result = await response.json();
      
      if (result.error) {
        throw new Error(`Odoo execution failed: ${result.error.message}`);
      }

      return result.result;
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error(`Odoo request timeout after ${this.timeout}ms`);
      }
      throw new Error(`Odoo execution error: ${error.message}`);
    }
  }

  /**
   * Search and read records
   */
  async searchRead(model, domain, fields = [], limit = 80) {
    return this.execute(model, 'search_read', [domain], { fields, limit });
  }

  /**
   * Search for record IDs
   */
  async search(model, domain, limit = 80) {
    return this.execute(model, 'search', [domain], { limit });
  }

  /**
   * Create record
   */
  async create(model, values) {
    return this.execute(model, 'create', [values]);
  }

  /**
   * Update record
   */
  async write(model, ids, values) {
    return this.execute(model, 'write', [ids, values]);
  }

  /**
   * Delete record
   */
  async unlink(model, ids) {
    return this.execute(model, 'unlink', [ids]);
  }

  /**
   * Get field names for a model
   */
  async getFieldNames(model) {
    return this.execute(model, 'fields_get', []);
  }
}
