/**
 * create_invoice — Create a customer or vendor invoice in Odoo
 */

import { z } from 'zod';
import { auditStart } from '../utils/logger.js';

export const schema = {
  partner_id:   { type: 'number', description: 'Odoo partner (customer/vendor) ID' },
  move_type:    { type: 'string', description: 'Invoice type: out_invoice (customer) or in_invoice (vendor). Default: out_invoice' },
  invoice_date: { type: 'string', description: 'Invoice date YYYY-MM-DD. Default: today' },
  date_due:     { type: 'string', description: 'Due date YYYY-MM-DD' },
  lines: {
    type: 'array',
    description: 'Invoice line items',
    items: {
      type: 'object',
      properties: {
        name:       { type: 'string', description: 'Line description (required)' },
        quantity:   { type: 'number', description: 'Quantity. Default: 1' },
        price_unit: { type: 'number', description: 'Unit price (required)' },
        product_id: { type: 'number', description: 'Optional product ID' },
        tax_ids:    { type: 'array', items: { type: 'number' }, description: 'Tax IDs list' },
      },
      required: ['name', 'price_unit'],
    },
  },
  ref:     { type: 'string', description: 'External reference / PO number' },
  dry_run: { type: 'boolean', description: 'If true, validate only — do not create. Default: false' },
};

const lineSchema = z.object({
  name: z.string().min(1),
  quantity: z.number().positive().default(1),
  price_unit: z.number(),
  product_id: z.number().int().positive().optional(),
  tax_ids: z.array(z.number().int()).optional(),
});

const inputSchema = z.object({
  partner_id: z.number().int().positive(),
  move_type: z.enum(['out_invoice', 'in_invoice']).default('out_invoice'),
  invoice_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  date_due: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  lines: z.array(lineSchema).min(1, 'At least one invoice line is required'),
  ref: z.string().optional(),
  dry_run: z.boolean().default(false),
});

export async function createInvoice(params, odoo) {
  const v = inputSchema.parse(params);
  const audit = auditStart('create_invoice', params, { dry_run: v.dry_run });

  try {
    // Validate partner exists
    const partners = await odoo.searchRead('res.partner', [['id', '=', v.partner_id]], ['name'], 1);
    if (!partners.length) throw new Error(`Partner ID ${v.partner_id} not found`);

    const invoiceLines = v.lines.map(l => {
      const vals = {
        name: l.name,
        quantity: l.quantity,
        price_unit: l.price_unit,
      };
      if (l.product_id) vals.product_id = l.product_id;
      if (l.tax_ids?.length) vals.tax_ids = [[6, 0, l.tax_ids]]; // Odoo m2m set
      return [0, 0, vals]; // Odoo one2many create command
    });

    const values = {
      partner_id: v.partner_id,
      move_type: v.move_type,
      invoice_line_ids: invoiceLines,
    };
    if (v.invoice_date) values.invoice_date = v.invoice_date;
    if (v.date_due) values.invoice_date_due = v.date_due;
    if (v.ref) values.ref = v.ref;

    if (v.dry_run) {
      const result = {
        success: true,
        dry_run: true,
        message: 'Validation passed. Invoice would be created with these values.',
        partner: partners[0].name,
        move_type: v.move_type,
        line_count: v.lines.length,
        total: v.lines.reduce((s, l) => s + l.quantity * l.price_unit, 0),
      };
      audit.success(result);
      return result;
    }

    const invoiceId = await odoo.create('account.move', values);

    // Read back the created invoice
    const [invoice] = await odoo.read('account.move', [invoiceId], [
      'name', 'amount_total', 'amount_untaxed', 'state', 'partner_id', 'invoice_date', 'invoice_date_due',
    ]);

    const result = {
      success: true,
      invoice_id: invoiceId,
      number: invoice.name,
      partner: invoice.partner_id?.[1],
      amount_untaxed: invoice.amount_untaxed,
      amount_total: invoice.amount_total,
      state: invoice.state,
      invoice_date: invoice.invoice_date,
      date_due: invoice.invoice_date_due,
      odoo_url: `${odoo.url}/web#id=${invoiceId}&model=account.move&view_type=form`,
    };

    audit.success(result);
    return result;
  } catch (err) {
    audit.error(err);
    throw err;
  }
}
