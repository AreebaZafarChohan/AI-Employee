/**
 * get_revenue_summary — Aggregate revenue metrics from posted invoices
 */

import { z } from 'zod';
import { auditStart } from '../utils/logger.js';

export const schema = {
  period:    { type: 'string', description: 'Preset period: this_month, last_month, this_quarter, this_year, last_year, custom. Default: this_month' },
  date_from: { type: 'string', description: 'Custom start date YYYY-MM-DD (required if period=custom)' },
  date_to:   { type: 'string', description: 'Custom end date YYYY-MM-DD (required if period=custom)' },
  group_by:  { type: 'string', description: 'Group results by: partner, month, product. Default: none' },
};

const inputSchema = z.object({
  period: z.enum(['this_month', 'last_month', 'this_quarter', 'this_year', 'last_year', 'custom']).default('this_month'),
  date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  group_by: z.enum(['partner', 'month', 'product', 'none']).default('none'),
});

function resolvePeriod(period, dateFrom, dateTo) {
  const now = new Date();
  const y = now.getFullYear();
  const m = now.getMonth(); // 0-indexed

  switch (period) {
    case 'this_month':
      return { from: new Date(y, m, 1), to: new Date(y, m + 1, 0) };
    case 'last_month':
      return { from: new Date(y, m - 1, 1), to: new Date(y, m, 0) };
    case 'this_quarter': {
      const q = Math.floor(m / 3) * 3;
      return { from: new Date(y, q, 1), to: new Date(y, q + 3, 0) };
    }
    case 'this_year':
      return { from: new Date(y, 0, 1), to: new Date(y, 11, 31) };
    case 'last_year':
      return { from: new Date(y - 1, 0, 1), to: new Date(y - 1, 11, 31) };
    case 'custom':
      if (!dateFrom || !dateTo) throw new Error('date_from and date_to required for custom period');
      return { from: new Date(dateFrom), to: new Date(dateTo) };
  }
}

function fmt(d) { return d.toISOString().slice(0, 10); }

export async function getRevenueSummary(params, odoo) {
  const v = inputSchema.parse(params);
  const audit = auditStart('get_revenue_summary', params);

  try {
    const { from, to } = resolvePeriod(v.period, v.date_from, v.date_to);

    // Customer invoices, posted
    const domain = [
      ['move_type', '=', 'out_invoice'],
      ['state', '=', 'posted'],
      ['invoice_date', '>=', fmt(from)],
      ['invoice_date', '<=', fmt(to)],
    ];

    const invoices = await odoo.searchRead('account.move', domain, [
      'name', 'partner_id', 'invoice_date', 'amount_total', 'amount_residual',
      'amount_untaxed', 'payment_state', 'currency_id',
    ], 500);

    // Aggregation
    let totalRevenue = 0;
    let totalCollected = 0;
    let totalOutstanding = 0;
    let paidCount = 0;

    const byGroup = {};

    for (const inv of invoices) {
      totalRevenue += inv.amount_total;
      totalOutstanding += inv.amount_residual;
      totalCollected += inv.amount_total - inv.amount_residual;
      if (inv.payment_state === 'paid') paidCount++;

      if (v.group_by !== 'none') {
        let key;
        if (v.group_by === 'partner') key = inv.partner_id?.[1] || 'Unknown';
        else if (v.group_by === 'month') key = inv.invoice_date?.slice(0, 7) || 'Unknown';
        else key = 'all';

        if (!byGroup[key]) byGroup[key] = { revenue: 0, collected: 0, outstanding: 0, count: 0 };
        byGroup[key].revenue += inv.amount_total;
        byGroup[key].collected += inv.amount_total - inv.amount_residual;
        byGroup[key].outstanding += inv.amount_residual;
        byGroup[key].count += 1;
      }
    }

    // Vendor bills for expense context
    const expDomain = [
      ['move_type', '=', 'in_invoice'],
      ['state', '=', 'posted'],
      ['invoice_date', '>=', fmt(from)],
      ['invoice_date', '<=', fmt(to)],
    ];
    const expenses = await odoo.searchRead('account.move', expDomain, ['amount_total'], 500);
    const totalExpenses = expenses.reduce((s, e) => s + e.amount_total, 0);

    const result = {
      success: true,
      period: { label: v.period, from: fmt(from), to: fmt(to) },
      summary: {
        total_revenue: Math.round(totalRevenue * 100) / 100,
        total_collected: Math.round(totalCollected * 100) / 100,
        total_outstanding: Math.round(totalOutstanding * 100) / 100,
        total_expenses: Math.round(totalExpenses * 100) / 100,
        net_income: Math.round((totalRevenue - totalExpenses) * 100) / 100,
        invoice_count: invoices.length,
        paid_count: paidCount,
        collection_rate: invoices.length ? Math.round((paidCount / invoices.length) * 10000) / 100 : 0,
      },
      ...(v.group_by !== 'none' ? { breakdown: byGroup } : {}),
    };

    audit.success(result);
    return result;
  } catch (err) {
    audit.error(err);
    throw err;
  }
}
