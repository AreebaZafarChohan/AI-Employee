/**
 * list_expenses — Query vendor bills (in_invoice) as expenses
 */

import { z } from 'zod';
import { auditStart } from '../utils/logger.js';

export const schema = {
  date_from:  { type: 'string', description: 'Start date YYYY-MM-DD' },
  date_to:    { type: 'string', description: 'End date YYYY-MM-DD' },
  partner_id: { type: 'number', description: 'Filter by vendor ID' },
  min_amount: { type: 'number', description: 'Minimum total amount' },
  state:      { type: 'string', description: 'draft, posted, cancel' },
  limit:      { type: 'number', description: 'Max results. Default: 50' },
  offset:     { type: 'number', description: 'Pagination offset. Default: 0' },
};

const inputSchema = z.object({
  date_from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  date_to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  partner_id: z.number().int().positive().optional(),
  min_amount: z.number().positive().optional(),
  state: z.enum(['draft', 'posted', 'cancel']).optional(),
  limit: z.number().int().min(1).max(200).default(50),
  offset: z.number().int().min(0).default(0),
});

export async function listExpenses(params, odoo) {
  const v = inputSchema.parse(params);
  const audit = auditStart('list_expenses', params);

  try {
    const domain = [['move_type', '=', 'in_invoice']];

    if (v.state) domain.push(['state', '=', v.state]);
    if (v.partner_id) domain.push(['partner_id', '=', v.partner_id]);
    if (v.date_from) domain.push(['invoice_date', '>=', v.date_from]);
    if (v.date_to) domain.push(['invoice_date', '<=', v.date_to]);
    if (v.min_amount) domain.push(['amount_total', '>=', v.min_amount]);

    const fields = [
      'name', 'partner_id', 'invoice_date', 'invoice_date_due',
      'amount_total', 'amount_residual', 'amount_untaxed',
      'state', 'payment_state', 'currency_id', 'ref',
    ];

    const bills = await odoo.searchRead('account.move', domain, fields, v.limit, v.offset, 'invoice_date desc');
    const total = await odoo.searchCount('account.move', domain);

    let grandTotal = 0;
    let grandUnpaid = 0;

    const rows = bills.map(b => {
      grandTotal += b.amount_total;
      grandUnpaid += b.amount_residual;
      return {
        id: b.id,
        number: b.name,
        vendor: b.partner_id?.[1] || 'N/A',
        vendor_id: b.partner_id?.[0] || null,
        date: b.invoice_date,
        due_date: b.invoice_date_due,
        amount_total: b.amount_total,
        amount_unpaid: b.amount_residual,
        currency: b.currency_id?.[1] || 'USD',
        state: b.state,
        payment_state: b.payment_state,
        ref: b.ref || null,
      };
    });

    const result = {
      success: true,
      total,
      returned: rows.length,
      offset: v.offset,
      totals: {
        amount: Math.round(grandTotal * 100) / 100,
        unpaid: Math.round(grandUnpaid * 100) / 100,
      },
      expenses: rows,
    };

    audit.success(result);
    return result;
  } catch (err) {
    audit.error(err);
    throw err;
  }
}
