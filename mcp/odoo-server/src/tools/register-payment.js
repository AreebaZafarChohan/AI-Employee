/**
 * Register Payment Tool
 * 
 * Records a payment for an invoice in Odoo
 */

import { z } from 'zod';

const inputSchema = z.object({
  invoice_id: z.number().describe('Invoice ID'),
  amount: z.number().describe('Payment amount'),
  date: z.string().describe('Payment date (YYYY-MM-DD)'),
  payment_method: z.string().default('manual').describe('Payment method')
});

export async function registerPayment(params, odooClient) {
  const validated = inputSchema.parse(params);

  try {
    // First, verify the invoice exists and get its details
    const invoices = await odooClient.searchRead(
      'account.move',
      [['id', '=', validated.invoice_id]],
      ['id', 'name', 'partner_id', 'amount_residual', 'currency_id']
    );

    if (!invoices || invoices.length === 0) {
      return {
        success: false,
        error: `Invoice ${validated.invoice_id} not found`
      };
    }

    const invoice = invoices[0];

    // Create payment record
    const paymentData = {
      payment_type: 'inbound',
      payment_method_line_id: 1, // Default payment method
      partner_id: invoice.partner_id?.[0],
      amount: validated.amount,
      date: validated.date,
      currency_id: invoice.currency_id?.[0],
      reconciled_invoice_ids: [[6, 0, [validated.invoice_id]]]
    };

    const paymentId = await odooClient.create('account.payment', paymentData);

    // Confirm the payment
    await odooClient.write('account.payment', [paymentId], {
      state: 'posted'
    });

    return {
      success: true,
      payment_id: paymentId,
      invoice_id: validated.invoice_id,
      amount: validated.amount,
      message: `Payment ${paymentId} registered for invoice ${validated.invoice_id}`
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      payment_id: null
    };
  }
}
