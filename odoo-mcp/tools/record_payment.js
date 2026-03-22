/**
 * record_payment — Register a payment against an invoice
 *
 * Uses Odoo's account.payment.register wizard for proper reconciliation.
 */

import { z } from 'zod';
import { auditStart } from '../utils/logger.js';

export const schema = {
  invoice_id:     { type: 'number', description: 'The account.move ID to pay' },
  amount:         { type: 'number', description: 'Payment amount. Omit to pay full residual.' },
  payment_date:   { type: 'string', description: 'Payment date YYYY-MM-DD. Default: today' },
  journal_id:     { type: 'number', description: 'Payment journal ID (bank/cash). Auto-detected if omitted.' },
  memo:           { type: 'string', description: 'Payment memo / reference' },
  dry_run:        { type: 'boolean', description: 'Validate only. Default: false' },
};

const inputSchema = z.object({
  invoice_id: z.number().int().positive(),
  amount: z.number().positive().optional(),
  payment_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  journal_id: z.number().int().positive().optional(),
  memo: z.string().optional(),
  dry_run: z.boolean().default(false),
});

export async function recordPayment(params, odoo) {
  const v = inputSchema.parse(params);
  const audit = auditStart('record_payment', params, { dry_run: v.dry_run });

  try {
    // Validate invoice exists and is payable
    const [invoice] = await odoo.read('account.move', [v.invoice_id], [
      'name', 'state', 'payment_state', 'amount_residual', 'partner_id', 'move_type', 'currency_id',
    ]);
    if (!invoice) throw new Error(`Invoice ID ${v.invoice_id} not found`);
    if (invoice.state !== 'posted') throw new Error(`Invoice ${invoice.name} is in state '${invoice.state}' — must be 'posted' to pay`);
    if (invoice.payment_state === 'paid') throw new Error(`Invoice ${invoice.name} is already fully paid`);

    const payAmount = v.amount ?? invoice.amount_residual;
    if (payAmount > invoice.amount_residual) {
      throw new Error(`Payment amount ${payAmount} exceeds residual ${invoice.amount_residual}`);
    }

    // Find a bank journal if not specified
    let journalId = v.journal_id;
    if (!journalId) {
      const journals = await odoo.searchRead('account.journal', [['type', 'in', ['bank', 'cash']]], ['id', 'name'], 1);
      if (!journals.length) throw new Error('No bank/cash journal found — please specify journal_id');
      journalId = journals[0].id;
    }

    if (v.dry_run) {
      const result = {
        success: true,
        dry_run: true,
        message: `Would register payment of ${payAmount} against ${invoice.name}`,
        invoice: invoice.name,
        partner: invoice.partner_id?.[1],
        amount: payAmount,
        residual_after: invoice.amount_residual - payAmount,
        journal_id: journalId,
      };
      audit.success(result);
      return result;
    }

    // Create payment via account.payment model directly
    const paymentVals = {
      payment_type: invoice.move_type === 'out_invoice' ? 'inbound' : 'outbound',
      partner_type: invoice.move_type === 'out_invoice' ? 'customer' : 'supplier',
      partner_id: invoice.partner_id[0],
      amount: payAmount,
      journal_id: journalId,
      date: v.payment_date || new Date().toISOString().slice(0, 10),
      ref: v.memo || `Payment for ${invoice.name}`,
    };

    const paymentId = await odoo.create('account.payment', paymentVals);

    // Confirm the payment
    await odoo.execute('account.payment', 'action_post', [[paymentId]]);

    // Read back
    const [payment] = await odoo.read('account.payment', [paymentId], [
      'name', 'amount', 'state', 'date', 'partner_id',
    ]);

    // Re-read invoice to get updated residual
    const [updatedInv] = await odoo.read('account.move', [v.invoice_id], ['amount_residual', 'payment_state']);

    const result = {
      success: true,
      payment_id: paymentId,
      payment_name: payment.name,
      amount_paid: payment.amount,
      payment_state: payment.state,
      payment_date: payment.date,
      invoice: invoice.name,
      invoice_residual_after: updatedInv.amount_residual,
      invoice_payment_state: updatedInv.payment_state,
    };

    audit.success(result);
    return result;
  } catch (err) {
    audit.error(err);
    throw err;
  }
}
