/**
 * Get Partner Balance Tool
 * 
 * Retrieves balance for a specific customer/vendor
 */

import { z } from 'zod';

const inputSchema = z.object({
  partner_id: z.number().describe('Partner/Customer ID')
});

export async function getPartnerBalance(params, odooClient) {
  const validated = inputSchema.parse(params);

  try {
    // Get partner information
    const partners = await odooClient.searchRead(
      'res.partner',
      [['id', '=', validated.partner_id]],
      ['id', 'name', 'email', 'phone']
    );

    if (!partners || partners.length === 0) {
      return {
        success: false,
        error: `Partner ${validated.partner_id} not found`
      };
    }

    const partner = partners[0];

    // Get unpaid invoices for this partner
    const unpaidInvoices = await odooClient.searchRead(
      'account.move',
      [
        ['partner_id', '=', validated.partner_id],
        ['move_type', 'in', ['out_invoice', 'in_invoice']],
        ['payment_state', '=', 'not_paid'],
        ['state', '=', 'posted']
      ],
      ['id', 'name', 'amount_residual', 'move_type']
    );

    // Calculate balances
    const receivables = unpaidInvoices
      .filter(inv => inv.move_type === 'out_invoice')
      .reduce((sum, inv) => sum + (inv.amount_residual || 0), 0);

    const payables = unpaidInvoices
      .filter(inv => inv.move_type === 'in_invoice')
      .reduce((sum, inv) => sum + (inv.amount_residual || 0), 0);

    return {
      success: true,
      partner: {
        id: partner.id,
        name: partner.name,
        email: partner.email,
        phone: partner.phone
      },
      balance: {
        receivables: receivables,  // What they owe us
        payables: payables,        // What we owe them
        net: receivables - payables
      },
      unpaid_invoices: {
        count: unpaidInvoices.length,
        invoices: unpaidInvoices.map(inv => ({
          id: inv.id,
          name: inv.name,
          amount_due: inv.amount_residual,
          type: inv.move_type === 'out_invoice' ? 'Customer Invoice' : 'Vendor Bill'
        }))
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      balance: null
    };
  }
}
