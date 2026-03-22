/**
 * Sales Controller
 * Uses MCP Odoo Server for invoice and payment status when available.
 */

import { Request, Response } from 'express';
import path from 'path';
import fs from 'fs';
import { mcpClientService } from '../services/mcp-client.service';
import { logger } from '../lib/logger';

const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');
const VAULT_PATH = process.env.VAULT_PATH || path.join(ROOT_PATH, 'AI-Employee-Vault');
const PROSPECTS_DIR = path.join(VAULT_PATH, 'Business', 'Clients', 'prospects');
const INVOICES_DIR = path.join(VAULT_PATH, 'Accounting', 'Invoices');
const ODOO_SERVER_PATH = path.join(ROOT_PATH, 'mcp', 'odoo-server', 'src', 'index.js');

const PIPELINE_STAGES = ['new', 'contacted', 'responded', 'meeting', 'closed_won', 'closed_lost'];

export class SalesController {
  private async getOdooResult(toolName: string, toolArgs: any = {}) {
    try {
      const response = await mcpClientService.callTool(
        'odoo-server',
        'node',
        [ODOO_SERVER_PATH],
        toolName,
        toolArgs
      );

      if (response.isError) throw new Error(JSON.stringify(response.content));
      const content = (response.content as any[])[0];
      if (content && content.type === 'text') return JSON.parse(content.text);
      return null;
    } catch (error) {
      logger.error(`MCP Odoo Error calling ${toolName}:`, error);
      return null; // Fallback to filesystem
    }
  }

  async getLeads(req: Request, res: Response) {
    try {
      const stage = req.query.stage as string | undefined;
      const leads = this.readLeadFiles(stage);
      res.json({ data: leads });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch leads' });
    }
  }

  async getLeadById(req: Request, res: Response) {
    try {
      const { id } = req.params;
      const filePath = path.join(PROSPECTS_DIR, `${id}.md`);
      if (!fs.existsSync(filePath)) return res.status(404).json({ error: 'Lead not found' });
      const content = fs.readFileSync(filePath, 'utf-8');
      const meta = this.parseMarkdownFrontmatter(content);
      meta.id = id;
      res.json({ data: meta });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch lead' });
    }
  }

  async getPipelineStats(_req: Request, res: Response) {
    try {
      const leads = this.readLeadFiles();
      let invoices = await this.getOdooResult('list_unpaid_invoices', { limit: 100 });
      
      // Fallback to filesystem if MCP fails
      if (!invoices) {
        invoices = this.readInvoiceFiles();
      } else {
        // Map Odoo structure to our expected structure
        invoices = (invoices.invoices || []).map((inv: any) => ({
          id: inv.name,
          amount: String(inv.amount_total),
          status: inv.state === 'posted' ? 'pending' : 'paid',
          due_date: inv.invoice_date_due,
        }));
      }

      const byStage: Record<string, number> = {};
      PIPELINE_STAGES.forEach(s => byStage[s] = leads.filter(l => l.stage === s).length);

      const totalRevenue = invoices.filter((i: any) => i.status === 'paid').reduce((sum: number, i: any) => sum + parseFloat(i.amount || '0'), 0);
      const pendingRevenue = invoices.filter((i: any) => i.status === 'pending').reduce((sum: number, i: any) => sum + parseFloat(i.amount || '0'), 0);

      res.json({
        data: {
          total_leads: leads.length,
          by_stage: byStage,
          total_revenue: totalRevenue,
          pending_revenue: pendingRevenue,
          invoices_count: invoices.length,
        },
      });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch pipeline stats' });
    }
  }

  async triggerDiscovery(req: Request, res: Response) {
    const { keywords } = req.body;
    res.json({ data: { success: true, message: `Discovery triggered for: ${keywords || 'AI,SaaS'}` } });
  }

  async getInvoices(_req: Request, res: Response) {
    try {
      let invoices = await this.getOdooResult('list_unpaid_invoices', { limit: 100 });
      if (!invoices) {
        invoices = this.readInvoiceFiles();
      } else {
        invoices = (invoices.invoices || []).map((inv: any) => ({
          id: inv.name,
          partner: inv.partner_id[1],
          amount: inv.amount_total,
          status: inv.state === 'posted' ? 'pending' : 'paid',
          date: inv.invoice_date,
        }));
      }
      res.json({ data: invoices });
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch invoices' });
    }
  }

  async getPaymentStatus(_req: Request, res: Response) {
    try {
      const summary = await this.getOdooResult('get_financial_summary', { period: 'monthly' });
      if (summary) {
        res.json({ data: summary });
      } else {
        // Fallback
        res.json({ data: { status: 'filesystem_fallback', note: 'Odoo MCP unavailable' } });
      }
    } catch (error) {
      res.status(500).json({ error: 'Failed to fetch payment status' });
    }
  }

  private readLeadFiles(stage?: string): Array<Record<string, any>> {
    if (!fs.existsSync(PROSPECTS_DIR)) return [];
    const leads = fs.readdirSync(PROSPECTS_DIR).filter(f => f.startsWith('lead-') && f.endsWith('.md')).map(f => {
      const meta = this.parseMarkdownFrontmatter(fs.readFileSync(path.join(PROSPECTS_DIR, f), 'utf-8'));
      meta.id = f.replace('.md', '');
      return meta;
    });
    return stage ? leads.filter(l => l.stage === stage) : leads;
  }

  private readInvoiceFiles(): Array<Record<string, any>> {
    if (!fs.existsSync(INVOICES_DIR)) return [];
    return fs.readdirSync(INVOICES_DIR).filter(f => f.startsWith('INV-') && f.endsWith('.md')).map(f => this.parseMarkdownFrontmatter(fs.readFileSync(path.join(INVOICES_DIR, f), 'utf-8')));
  }

  private parseMarkdownFrontmatter(content: string): Record<string, string> {
    const match = content.match(/---\n([\s\S]*?)\n---/);
    if (!match) return {};
    const meta: Record<string, string> = {};
    match[1].split('\n').forEach(line => {
      const idx = line.indexOf(':');
      if (idx > 0) meta[line.slice(0, idx).trim()] = line.slice(idx + 1).trim();
    });
    return meta;
  }
}

export const salesController = new SalesController();
export default salesController;
