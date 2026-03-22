/**
 * list_customers / create_customer — Customer (res.partner) management
 */

import { z } from 'zod';
import { auditStart } from '../utils/logger.js';

// ═══════════════ list_customers ═══════════════

export const listCustomersSchema = {
  search:      { type: 'string', description: 'Search name, email, or phone' },
  is_company:  { type: 'boolean', description: 'Filter companies only. Default: all' },
  customer_rank_gt: { type: 'number', description: 'Minimum customer_rank (1+ = actual customer). Default: 0' },
  limit:       { type: 'number', description: 'Max results. Default: 50' },
  offset:      { type: 'number', description: 'Pagination offset. Default: 0' },
};

const listInput = z.object({
  search: z.string().optional(),
  is_company: z.boolean().optional(),
  customer_rank_gt: z.number().int().min(0).default(0),
  limit: z.number().int().min(1).max(200).default(50),
  offset: z.number().int().min(0).default(0),
});

export async function listCustomers(params, odoo) {
  const v = listInput.parse(params);
  const audit = auditStart('list_customers', params);

  try {
    const domain = [];
    if (v.is_company !== undefined) domain.push(['is_company', '=', v.is_company]);
    if (v.customer_rank_gt > 0) domain.push(['customer_rank', '>=', v.customer_rank_gt]);
    if (v.search) {
      domain.push('|', '|',
        ['name', 'ilike', v.search],
        ['email', 'ilike', v.search],
        ['phone', 'ilike', v.search],
      );
    }

    const fields = [
      'name', 'email', 'phone', 'mobile', 'street', 'city', 'country_id',
      'is_company', 'customer_rank', 'supplier_rank', 'credit', 'debit',
      'total_invoiced',
    ];

    const partners = await odoo.searchRead('res.partner', domain, fields, v.limit, v.offset, 'name asc');
    const total = await odoo.searchCount('res.partner', domain);

    const rows = partners.map(p => ({
      id: p.id,
      name: p.name,
      email: p.email || null,
      phone: p.phone || p.mobile || null,
      city: p.city || null,
      country: p.country_id?.[1] || null,
      is_company: p.is_company,
      total_invoiced: p.total_invoiced,
      credit: p.credit,
      debit: p.debit,
      balance: p.credit - p.debit,
    }));

    const result = { success: true, total, returned: rows.length, offset: v.offset, customers: rows };
    audit.success(result);
    return result;
  } catch (err) {
    audit.error(err);
    throw err;
  }
}

// ═══════════════ create_customer ═══════════════

export const createCustomerSchema = {
  name:       { type: 'string', description: 'Customer / company name (required)' },
  email:      { type: 'string', description: 'Email address' },
  phone:      { type: 'string', description: 'Phone number' },
  street:     { type: 'string', description: 'Street address' },
  city:       { type: 'string', description: 'City' },
  zip:        { type: 'string', description: 'ZIP / postal code' },
  country_code: { type: 'string', description: 'ISO 3166-1 alpha-2 country code (e.g. US, PK)' },
  is_company: { type: 'boolean', description: 'true = company, false = individual. Default: true' },
  vat:        { type: 'string', description: 'Tax ID / VAT number' },
  dry_run:    { type: 'boolean', description: 'Validate only. Default: false' },
};

const createInput = z.object({
  name: z.string().min(1),
  email: z.string().email().optional(),
  phone: z.string().optional(),
  street: z.string().optional(),
  city: z.string().optional(),
  zip: z.string().optional(),
  country_code: z.string().length(2).optional(),
  is_company: z.boolean().default(true),
  vat: z.string().optional(),
  dry_run: z.boolean().default(false),
});

export async function createCustomer(params, odoo) {
  const v = createInput.parse(params);
  const audit = auditStart('create_customer', params, { dry_run: v.dry_run });

  try {
    const values = {
      name: v.name,
      is_company: v.is_company,
      customer_rank: 1,
    };
    if (v.email) values.email = v.email;
    if (v.phone) values.phone = v.phone;
    if (v.street) values.street = v.street;
    if (v.city) values.city = v.city;
    if (v.zip) values.zip = v.zip;
    if (v.vat) values.vat = v.vat;

    // Resolve country
    if (v.country_code) {
      const countries = await odoo.searchRead('res.country', [['code', '=', v.country_code.toUpperCase()]], ['id', 'name'], 1);
      if (countries.length) {
        values.country_id = countries[0].id;
      }
    }

    if (v.dry_run) {
      const result = { success: true, dry_run: true, message: 'Validation passed', values };
      audit.success(result);
      return result;
    }

    const partnerId = await odoo.create('res.partner', values);
    const [partner] = await odoo.read('res.partner', [partnerId], ['name', 'email', 'phone', 'is_company', 'customer_rank']);

    const result = {
      success: true,
      partner_id: partnerId,
      name: partner.name,
      email: partner.email,
      is_company: partner.is_company,
      odoo_url: `${odoo.url}/web#id=${partnerId}&model=res.partner&view_type=form`,
    };

    audit.success(result);
    return result;
  } catch (err) {
    audit.error(err);
    throw err;
  }
}
