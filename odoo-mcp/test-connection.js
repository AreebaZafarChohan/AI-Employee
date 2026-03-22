#!/usr/bin/env node
/**
 * Quick connection test — run with: node test-connection.js
 */

import { readFileSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { OdooClient } from './utils/odoo_client.js';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Load .env
for (const p of [resolve(__dirname, '.env'), resolve(__dirname, '..', '.env')]) {
  try {
    for (const line of readFileSync(p, 'utf-8').split('\n')) {
      const t = line.trim();
      if (!t || t.startsWith('#')) continue;
      const eq = t.indexOf('=');
      if (eq === -1) continue;
      const k = t.slice(0, eq).trim();
      if (!process.env[k]) process.env[k] = t.slice(eq + 1).trim();
    }
    break;
  } catch { /* next */ }
}

async function main() {
  console.log('Odoo MCP — Connection Test\n');

  const client = new OdooClient({
    url: process.env.ODOO_URL,
    db: process.env.ODOO_DB,
    username: process.env.ODOO_USERNAME,
    password: process.env.ODOO_PASSWORD,
  });

  // 1. Version
  console.log('1. Checking server version...');
  try {
    const v = await client.version();
    console.log(`   ✓ Odoo ${v.server_version} (${v.server_serie})\n`);
  } catch (e) {
    console.log(`   ✗ ${e.message}\n`);
  }

  // 2. Auth
  console.log('2. Authenticating...');
  try {
    const uid = await client.authenticate();
    console.log(`   ✓ UID = ${uid}\n`);
  } catch (e) {
    console.log(`   ✗ ${e.message}`);
    console.log('   → Check ODOO_USERNAME and ODOO_PASSWORD in .env\n');
    process.exit(1);
  }

  // 3. Partners
  console.log('3. Fetching partners...');
  try {
    const partners = await client.searchRead('res.partner', [['is_company', '=', true]], ['name', 'email'], 5);
    console.log(`   ✓ ${partners.length} companies found:`);
    partners.forEach(p => console.log(`     - ${p.name} (${p.email || 'no email'})`));
  } catch (e) {
    console.log(`   ✗ ${e.message}`);
  }

  // 4. Invoices
  console.log('\n4. Fetching invoices...');
  try {
    const invs = await client.searchRead('account.move',
      [['move_type', 'in', ['out_invoice', 'in_invoice']]],
      ['name', 'partner_id', 'amount_total', 'state'], 5);
    console.log(`   ✓ ${invs.length} invoices found:`);
    invs.forEach(i => console.log(`     - ${i.name}: $${i.amount_total} (${i.state}) - ${i.partner_id?.[1] || 'N/A'}`));
  } catch (e) {
    console.log(`   ✗ ${e.message}`);
  }

  // 5. Journals
  console.log('\n5. Fetching journals...');
  try {
    const journals = await client.searchRead('account.journal', [], ['name', 'type'], 10);
    console.log(`   ✓ ${journals.length} journals:`);
    journals.forEach(j => console.log(`     - ${j.name} (${j.type})`));
  } catch (e) {
    console.log(`   ✗ ${e.message}`);
  }

  console.log('\n✓ Connection test complete');
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
