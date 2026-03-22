#!/usr/bin/env node
/**
 * MCP Odoo Server
 *
 * Provides Odoo Community Accounting integration via MCP protocol
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { config } from 'dotenv';
import { OdooClient } from './client/odoo-client.js';
import { listUnpaidInvoices } from './tools/list-unpaid-invoices.js';
import { listOverduePayments } from './tools/list-overdue-payments.js';
import { createInvoice } from './tools/create-invoice.js';
import { registerPayment } from './tools/register-payment.js';
import { getFinancialSummary } from './tools/get-financial-summary.js';
import { getPartnerBalance } from './tools/get-partner-balance.js';

// Load environment variables
config();

// Configuration
const odooConfig = {
  url: process.env.ODOO_URL || 'http://localhost:8069',
  db: process.env.ODOO_DB || 'odoo',
  username: process.env.ODOO_USERNAME || 'admin',
  password: process.env.ODOO_PASSWORD || 'admin',
  timeout: parseInt(process.env.ODOO_TIMEOUT || '30000')
};

// Initialize Odoo client
let odooClient = null;

async function getClient() {
  if (!odooClient) {
    odooClient = new OdooClient(odooConfig);
    await odooClient.authenticate();
  }
  return odooClient;
}

// Create MCP server
const server = new McpServer({
  name: 'odoo-server',
  version: '1.0.0',
  description: 'MCP server for Odoo Community Accounting integration'
});

// Register tools with zod schemas (required for MCP SDK v1.27+)
server.tool(
  'list_unpaid_invoices',
  'Retrieve unpaid invoices from Odoo',
  {
    partner_id: z.number().optional().describe('Filter by partner ID'),
    date_from: z.string().optional().describe('Start date (YYYY-MM-DD)'),
    date_to: z.string().optional().describe('End date (YYYY-MM-DD)'),
    limit: z.number().optional().default(50).describe('Max results')
  },
  async (args) => {
    try {
      const client = await getClient();
      const result = await listUnpaidInvoices(args, client);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    } catch (error) {
      return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }], isError: true };
    }
  }
);

server.tool(
  'list_overdue_payments',
  'Retrieve overdue payments from Odoo',
  {
    days_overdue: z.number().optional().default(7).describe('Minimum days overdue'),
    limit: z.number().optional().default(50).describe('Max results')
  },
  async (args) => {
    try {
      const client = await getClient();
      const result = await listOverduePayments(args, client);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    } catch (error) {
      return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }], isError: true };
    }
  }
);

server.tool(
  'create_invoice',
  'Create a new customer invoice in Odoo',
  {
    partner_id: z.number().describe('Customer/Partner ID'),
    lines: z.array(z.object({
      product_id: z.number().optional(),
      name: z.string().describe('Line item description'),
      quantity: z.number().default(1).describe('Quantity'),
      price_unit: z.number().describe('Unit price'),
      tax_ids: z.array(z.number()).optional()
    })).describe('Invoice line items'),
    date_due: z.string().describe('Due date (YYYY-MM-DD)'),
    description: z.string().optional().describe('Invoice description')
  },
  async (args) => {
    try {
      const client = await getClient();
      const result = await createInvoice(args, client);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    } catch (error) {
      return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }], isError: true };
    }
  }
);

server.tool(
  'register_payment',
  'Record a payment for an invoice in Odoo',
  {
    invoice_id: z.number().describe('Invoice ID'),
    amount: z.number().describe('Payment amount'),
    date: z.string().describe('Payment date (YYYY-MM-DD)'),
    payment_method: z.string().optional().default('manual')
  },
  async (args) => {
    try {
      const client = await getClient();
      const result = await registerPayment(args, client);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    } catch (error) {
      return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }], isError: true };
    }
  }
);

server.tool(
  'get_financial_summary',
  'Get profit & loss summary from Odoo',
  {
    period: z.enum(['daily', 'weekly', 'monthly', 'yearly']).optional().default('monthly'),
    comparison: z.boolean().optional().default(true)
  },
  async (args) => {
    try {
      const client = await getClient();
      const result = await getFinancialSummary(args, client);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    } catch (error) {
      return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }], isError: true };
    }
  }
);

server.tool(
  'get_partner_balance',
  'Get balance for a specific customer/vendor',
  {
    partner_id: z.number().describe('Partner/Customer ID')
  },
  async (args) => {
    try {
      const client = await getClient();
      const result = await getPartnerBalance(args, client);
      return { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] };
    } catch (error) {
      return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }) }], isError: true };
    }
  }
);

// Start server
async function main() {
  try {
    console.error('Starting MCP Odoo Server...');

    const transport = new StdioServerTransport();
    await server.connect(transport);

    console.error('MCP Odoo Server running on stdio');
    console.error(`Odoo URL: ${odooConfig.url}`);
    console.error(`Odoo DB: ${odooConfig.db}`);
    console.error(`Odoo Username: ${odooConfig.username}`);

    // Test connection
    try {
      await getClient();
      console.error('✓ Connected to Odoo successfully');
    } catch (error) {
      console.error('✗ Failed to connect to Odoo:', error.message);
    }
  } catch (error) {
    console.error('Server error:', error);
    process.exit(1);
  }
}

main();
