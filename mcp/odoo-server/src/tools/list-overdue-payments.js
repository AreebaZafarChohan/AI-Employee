/**
 * List Overdue Payments Tool
 * 
 * Retrieves overdue payments from Odoo
 */

import { z } from 'zod';

const inputSchema = z.object({
  days_overdue: z.number().default(7).describe('Minimum days overdue'),
  limit: z.number().default(50).describe('Maximum results to return')
});

export async function listOverduePayments(params, odooClient) {
  const validated = inputSchema.parse(params);

  try {
    // Calculate cutoff date
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - validated.days_overdue);
    const cutoffDateStr = cutoffDate.toISOString().split('T')[0];

    // Build domain filter for overdue invoices
    const domain = [
      ['move_type', 'in', ['out_invoice', 'in_invoice']],
      ['payment_state', '=', 'not_paid'],
      ['invoice_date_due', '<', cutoffDateStr]
    ];

    // Fetch overdue invoices
    const invoices = await odooClient.searchRead(
      'account.move',
      domain,
      [
        'id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
        'amount_total', 'amount_residual', 'currency_id', 'state'
      ],
      validated.limit
    );

    // Calculate days overdue for each
    const today = new Date();
    const formattedInvoices = invoices.map(inv => {
      const dueDate = new Date(inv.invoice_date_due);
      const daysOverdue = Math.floor((today - dueDate) / (1000 * 60 * 60 * 24));
      
      return {
        id: inv.id,
        name: inv.name,
        partner: inv.partner_id?.[1] || 'Unknown',
        partner_id: inv.partner_id?.[0],
        due_date: inv.invoice_date_due,
        amount_due: inv.amount_residual,
        currency: inv.currency_id?.[1] || 'USD',
        days_overdue: daysOverdue
      };
    });

    // Sort by days overdue (most overdue first)
    formattedInvoices.sort((a, b) => b.days_overdue - a.days_overdue);

    return {
      success: true,
      count: formattedInvoices.length,
      days_overdue_filter: validated.days_overdue,
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
