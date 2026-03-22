/**
 * list_invoices — Query invoices with flexible filters
 */

import { z } from 'zod';
import { auditStart } from '../utils/logger.js';

export const schema = {
  state:       { type: 'string', description: 'Filter by state: draft, posted, cancel. Omit for all.' },
  payment_state: { type: 'string', description: 'Filter: not_paid, partial, paid, reversed. Omit for all.' },
  move_type:   { type: 'string', description: 'out_invoice (customer) or in_invoice (vendor). Omit for both.' },
  partner_id:  { type: 'number', description: 'Filter by partner ID' },
  date_from:   { type: 'string', description: 'Invoice date >= YYYY-MM-DD' },
  date_to:     { type: 'string', description: 'Invoice date <= YYYY-MM-DD' },
  overdue_only: { type: 'boolean', description: 'Only show invoices past due date. Default: false' },
  limit:       { type: 'number', description: 'Max results. Default: 50' },
  offset:      { type: 'number', description: 'Pagination offset. Default: 0' },
};

const inputSchema = z.object({
  state: z.enum(['draft', 'posted', 'cancel']).optional(),
  payment_state: z.enum(['not_paid', 'partial', 'paid', 'reversed']).optional(),
  move_type: z.enum(['out_invoice', 'in_invoice']).optional(),
  partner_id: z.number().int().positive().optional(),
  date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  overdue_only: z.boolean().default(false),
  limit: z.number().int().min(1).max(200).default(50),
  offset: z.number().int().min(0).default(0),
});

export async function listInvoices(params, odoo) {
  const v = inputSchema.parse(params);
  const audit = auditStart('list_invoices', params);

  try {
    const domain = [];

    // default: only real invoices (not journal entries)
    if (v.move_type) {
      domain.push(['move_type', '=', v.move_type]);
    } else {
      domain.push(['move_type', 'in', ['out_invoice', 'in_invoice']]);
    }

    if (v.state) domain.push(['state', '=', v.state]);
    if (v.payment_state) domain.push(['payment_state', '=', v.payment_state]);
    if (v.partner_id) domain.push(['partner_id', '=', v.partner_id]);
    if (v.date_from) domain.push(['invoice_date', '>=', v.date_from]);
    if (v.date_to) domain.push(['invoice_date', '<=', v.date_to]);
    if (v.overdue_only) {
      const today = new Date().toISOString().slice(0, 10);
      domain.push(['invoice_date_due', '<', today]);
      domain.push(['payment_state', '!=', 'paid']);
    }

    const fields = [
      'name', 'partner_id', 'move_type', 'invoice_date', 'invoice_date_due',
      'amount_total', 'amount_residual', 'amount_untaxed',
      'state', 'payment_state', 'currency_id', 'ref',
    ];

    const invoices = await odoo.searchRead('account.move', domain, fields, v.limit, v.offset, 'invoice_date desc');
    const total = await odoo.searchCount('account.move', domain);

    const today = new Date();
    const rows = invoices.map(inv => {
      const dueDate = inv.invoice_date_due ? new Date(inv.invoice_date_due) : null;
      return {
        id: inv.id,
        number: inv.name,
        partner: inv.partner_id?.[1] || 'N/A',
        partner_id: inv.partner_id?.[0] || null,
        type: inv.move_type,
        date: inv.invoice_date,
        due_date: inv.invoice_date_due,
        days_overdue: dueDate && inv.payment_state !== 'paid' ? Math.max(0, Math.floor((today - dueDate) / 86400000)) : 0,
        amount_untaxed: inv.amount_untaxed,
        amount_total: inv.amount_total,
        amount_due: inv.amount_residual,
        currency: inv.currency_id?.[1] || 'USD',
        state: inv.state,
        payment_state: inv.payment_state,
        ref: inv.ref || null,
      };
    });

    const result = {
      success: true,
      total,
      returned: rows.length,
      offset: v.offset,
      invoices: rows,
    };

    audit.success(result);
    return result;
  } catch (err) {
    audit.error(err);
    throw err;
  }
}
