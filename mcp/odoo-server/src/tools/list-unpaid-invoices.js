/**
 * List Unpaid Invoices Tool
 * 
 * Retrieves unpaid invoices from Odoo
 */

import { z } from 'zod';

const inputSchema = z.object({
  partner_id: z.number().optional().describe('Filter by partner ID'),
  date_from: z.string().optional().describe('Start date (YYYY-MM-DD)'),
  date_to: z.string().optional().describe('End date (YYYY-MM-DD)'),
  limit: z.number().default(50).describe('Maximum results to return')
});

export async function listUnpaidInvoices(params, odooClient) {
  const validated = inputSchema.parse(params);

  try {
    // Build domain filter
    const domain = [
      ['move_type', 'in', ['out_invoice', 'in_invoice']],
      ['payment_state', '=', 'not_paid']
    ];

    // Add partner filter if provided
    if (validated.partner_id) {
      domain.push(['partner_id', '=', validated.partner_id]);
    }

    // Add date filters if provided
    if (validated.date_from) {
      domain.push(['invoice_date', '>=', validated.date_from]);
    }
    if (validated.date_to) {
      domain.push(['invoice_date', '<=', validated.date_to]);
    }

    // Fetch invoices
    const invoices = await odooClient.searchRead(
      'account.move',
      domain,
      [
        'id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
        'amount_total', 'amount_residual', 'currency_id', 'state', 'move_type'
      ],
      validated.limit
    );

    // Format response
    const formattedInvoices = invoices.map(inv => ({
      id: inv.id,
      name: inv.name,
      partner: inv.partner_id?.[1] || 'Unknown',
      partner_id: inv.partner_id?.[0],
      invoice_date: inv.invoice_date,
      due_date: inv.invoice_date_due,
      amount_total: inv.amount_total,
      amount_due: inv.amount_residual,
      currency: inv.currency_id?.[1] || 'USD',
      state: inv.state,
      type: inv.move_type === 'out_invoice' ? 'Customer Invoice' : 'Vendor Bill'
    }));

    return {
      success: true,
      count: formattedInvoices.length,
      invoices: formattedInvoices
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      invoices: []
    };
  }
}
