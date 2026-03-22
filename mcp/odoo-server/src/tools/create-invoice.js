/**
 * Create Invoice Tool
 * 
 * Creates a new customer invoice in Odoo
 */

import { z } from 'zod';

const lineItemSchema = z.object({
  product_id: z.number().optional().describe('Product ID'),
  name: z.string().describe('Line item description'),
  quantity: z.number().default(1).describe('Quantity'),
  price_unit: z.number().describe('Unit price'),
  tax_ids: z.array(z.number()).optional().describe('Tax IDs')
});

const inputSchema = z.object({
  partner_id: z.number().describe('Customer/Partner ID'),
  lines: z.array(lineItemSchema).describe('Invoice line items'),
  date_due: z.string().describe('Due date (YYYY-MM-DD)'),
  description: z.string().optional().describe('Invoice description/narration')
});

export async function createInvoice(params, odooClient) {
  const validated = inputSchema.parse(params);

  try {
    // Prepare invoice lines
    const invoiceLines = validated.lines.map((line, index) => ({
      product_id: line.product_id ? [line.product_id] : false,
      name: line.name,
      quantity: line.quantity,
      price_unit: line.price_unit,
      tax_ids: line.tax_ids?.length ? [[6, 0, line.tax_ids]] : false
    }));

    // Create invoice
    const invoiceData = {
      move_type: 'out_invoice',
      partner_id: validated.partner_id,
      invoice_line_ids: invoiceLines.map(line => [0, 0, line]),
      invoice_date_due: validated.date_due,
      narration: validated.description || ''
    };

    const invoiceId = await odooClient.create('account.move', invoiceData);

    return {
      success: true,
      invoice_id: invoiceId,
      message: `Invoice ${invoiceId} created successfully`
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      invoice_id: null
    };
  }
}
