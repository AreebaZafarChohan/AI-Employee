#!/usr/bin/env node
/**
 * Odoo MCP Server — Production-Ready
 *
 * Integrates Claude Code with Odoo Community Edition (v17/18/19+)
 * via the Model Context Protocol over stdio.
 *
 * Capabilities:
 *   create_invoice, list_invoices, record_payment,
 *   list_customers, create_customer, get_revenue_summary, list_expenses
 *
 * Features:
 *   - Retry with exponential backoff
 *   - Dry-run mode on write operations
 *   - Audit logging (JSONL)
 *   - Zod input validation
 *   - Session auto-recovery
 */

import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { OdooClient } from './utils/odoo_client.js';
import { log } from './utils/logger.js';

// Tool implementations
import { createInvoice, schema as createInvoiceSchema } from './tools/create_invoice.js';
import { listInvoices, schema as listInvoicesSchema } from './tools/list_invoices.js';
import { recordPayment, schema as recordPaymentSchema } from './tools/record_payment.js';
import { listCustomers, listCustomersSchema, createCustomer, createCustomerSchema } from './tools/list_customers.js';
import { getRevenueSummary, schema as revenueSummarySchema } from './tools/revenue_summary.js';
import { listExpenses, schema as listExpensesSchema } from './tools/list_expenses.js';

// ─────────────────────────── env loader ───────────────────────────

const __dirname = dirname(fileURLToPath(import.meta.url));

function loadEnv() {
  // Try multiple locations for .env
  const candidates = [
    resolve(__dirname, '.env'),
    resolve(__dirname, '..', '.env'),
  ];
  for (const p of candidates) {
    try {
      const content = readFileSync(p, 'utf-8');
      for (const line of content.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const eq = trimmed.indexOf('=');
        if (eq === -1) continue;
        const key = trimmed.slice(0, eq).trim();
        const val = trimmed.slice(eq + 1).trim();
        if (!process.env[key]) process.env[key] = val;
      }
      return p;
    } catch { /* next */ }
  }
  return null;
}

const envFile = loadEnv();

// ─────────────────────────── config ───────────────────────────

const config = {
  url:            process.env.ODOO_URL,
  db:             process.env.ODOO_DB,
  username:       process.env.ODOO_USERNAME,
  password:       process.env.ODOO_PASSWORD,
  timeout:        parseInt(process.env.ODOO_TIMEOUT || '30000'),
  max_retries:    parseInt(process.env.MAX_RETRIES || '3'),
  retry_delay:    parseInt(process.env.RETRY_DELAY_SECONDS || '2') * 1000,
  retry_max_delay: parseInt(process.env.RETRY_MAX_DELAY || '30') * 1000,
};

// ─────────────────────────── shared client ───────────────────────────

let odoo = null;

function getClient() {
  if (!odoo) {
    odoo = new OdooClient(config);
  }
  return odoo;
}

/** Wrapper: connect client, call tool fn, format MCP response */
function handler(toolFn) {
  return async (params) => {
    try {
      const client = getClient();
      await client.ensureAuth();
      const result = await toolFn(params, client);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: err.message }) }],
        isError: true,
      };
    }
  };
}

// ─────────────────────────── server ───────────────────────────

const server = new McpServer({
  name: 'odoo-mcp',
  version: '2.0.0',
  description: 'Production MCP server for Odoo Community Edition accounting — invoices, payments, customers, revenue, expenses',
});

// Register all 7 tools
server.tool('create_invoice',      'Create a customer or vendor invoice in Odoo',           createInvoiceSchema,   handler(createInvoice));
server.tool('list_invoices',       'List and filter invoices (customer & vendor)',           listInvoicesSchema,    handler(listInvoices));
server.tool('record_payment',      'Record a payment against an invoice',                   recordPaymentSchema,   handler(recordPayment));
server.tool('list_customers',      'Search and list customers/partners',                    listCustomersSchema,   handler(listCustomers));
server.tool('create_customer',     'Create a new customer or vendor in Odoo',               createCustomerSchema,  handler(createCustomer));
server.tool('get_revenue_summary', 'Get aggregated revenue, expenses, and net income',      revenueSummarySchema,  handler(getRevenueSummary));
server.tool('list_expenses',       'List vendor bills / expenses with filters',             listExpensesSchema,    handler(listExpenses));

// ─────────────────────────── boot ───────────────────────────

async function main() {
  console.error('═══════════════════════════════════════════');
  console.error('  Odoo MCP Server v2.0.0');
  console.error('═══════════════════════════════════════════');
  console.error(`Env file:  ${envFile || 'none (using system env)'}`);
  console.error(`Odoo URL:  ${config.url || 'NOT SET'}`);
  console.error(`Odoo DB:   ${config.db || 'NOT SET'}`);
  console.error(`Odoo User: ${config.username || 'NOT SET'}`);
  console.error(`Retries:   ${config.max_retries}`);
  console.error(`Timeout:   ${config.timeout}ms`);

  if (!config.url || !config.db || !config.username || !config.password) {
    console.error('\n✗ Missing required ODOO_URL / ODOO_DB / ODOO_USERNAME / ODOO_PASSWORD');
    console.error('  Set them in .env or as environment variables.');
    process.exit(1);
  }

  // Test connection
  try {
    const client = getClient();
    const version = await client.version();
    console.error(`\n✓ Odoo server: ${version.server_version} (${version.server_serie})`);

    await client.authenticate();
    console.error(`✓ Authenticated as UID ${client.uid}`);
  } catch (err) {
    console.error(`\n✗ Connection failed: ${err.message}`);
    console.error('  Server will start but tools will fail until Odoo is reachable.');
    odoo = null; // reset so next call retries
  }

  // Start MCP transport
  const transport = new StdioServerTransport();
  await server.connect(transport);

  console.error('\n✓ MCP server running on stdio — 7 tools registered');
  console.error('  Tools: create_invoice, list_invoices, record_payment,');
  console.error('         list_customers, create_customer, get_revenue_summary, list_expenses');
  console.error('═══════════════════════════════════════════\n');

  log('info', 'server', 'started', { tools: 7, odoo_url: config.url });
}

main().catch(err => {
  console.error('Fatal:', err);
  process.exit(1);
});
