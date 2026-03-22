#!/usr/bin/env node
/**
 * Test All Platforms - One by One
 *
 * Tests Facebook, Instagram, Twitter posting and Odoo connection
 * using the existing MCP client libraries with real credentials from .env
 */

import { readFileSync } from 'fs';

// Load .env manually
const envContent = readFileSync(new URL('.env', import.meta.url), 'utf-8');
for (const line of envContent.split('\n')) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.startsWith('#')) continue;
  const eqIdx = trimmed.indexOf('=');
  if (eqIdx === -1) continue;
  const key = trimmed.substring(0, eqIdx).trim();
  const val = trimmed.substring(eqIdx + 1).trim();
  if (!process.env[key]) process.env[key] = val;
}

// Dynamic imports for each client
const BASE = new URL('.', import.meta.url).pathname;

async function separator(name) {
  console.log('\n' + '='.repeat(60));
  console.log(`  ${name}`);
  console.log('='.repeat(60));
}

// ─────────────────────────────────────────────────────────────
// 1. FACEBOOK
// ─────────────────────────────────────────────────────────────
async function testFacebook() {
  await separator('1. FACEBOOK - Post to Page');

  const { FacebookClient } = await import('./mcp/facebook-server/src/client/facebook-client.js');

  const client = new FacebookClient({
    access_token: process.env.FACEBOOK_ACCESS_TOKEN,
    page_id: process.env.FACEBOOK_PAGE_ID,
    api_version: 'v18.0',
    timeout: 30000,
  });

  // Step 1: Get page info
  console.log('\n[1a] Getting Facebook Page info...');
  try {
    const pageInfo = await client.getPageInfo();
    console.log(`✓ Page Name: ${pageInfo.name}`);
    console.log(`  Page ID: ${pageInfo.id}`);
    console.log(`  Category: ${pageInfo.category || 'N/A'}`);
    console.log(`  Followers: ${pageInfo.followers_count || 'N/A'}`);
  } catch (err) {
    console.log(`✗ Page info failed: ${err.message}`);
  }

  // Step 2: Publish a post
  console.log('\n[1b] Publishing Facebook post...');
  try {
    const postContent = `🤖 AI Employee Gold Tier - Live Test Post!\n\nThis post was published automatically by our AI Employee system using the Facebook Graph API.\n\nTimestamp: ${new Date().toISOString()}\n\n#AIEmployee #Automation #GoldTier #Hackathon`;

    const result = await client.publishPost(postContent);
    console.log(`✓ Post published successfully!`);
    console.log(`  Post ID: ${result.id}`);
    console.log(`  URL: https://facebook.com/${result.id}`);
    return { success: true, post_id: result.id };
  } catch (err) {
    console.log(`✗ Post failed: ${err.message}`);
    return { success: false, error: err.message };
  }
}

// ─────────────────────────────────────────────────────────────
// 2. INSTAGRAM
// ─────────────────────────────────────────────────────────────
async function testInstagram() {
  await separator('2. INSTAGRAM - Post to Account');

  const { InstagramClient } = await import('./mcp/instagram-server/src/client/instagram-client.js');

  const client = new InstagramClient({
    access_token: process.env.INSTAGRAM_ACCESS_TOKEN,
    business_account_id: process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID,
    api_version: 'v18.0',
    timeout: 30000,
  });

  // Step 1: Get account info
  console.log('\n[2a] Getting Instagram Account info...');
  try {
    const accountInfo = await client.getAccountInfo();
    console.log(`✓ Username: ${accountInfo.username || accountInfo.name || 'N/A'}`);
    console.log(`  ID: ${accountInfo.id}`);
    console.log(`  Followers: ${accountInfo.followers_count || 'N/A'}`);
    console.log(`  Media Count: ${accountInfo.media_count || 'N/A'}`);
  } catch (err) {
    console.log(`✗ Account info failed: ${err.message}`);
  }

  // Step 2: Publish a post (requires a public image URL)
  console.log('\n[2b] Publishing Instagram post...');
  try {
    // Instagram requires a publicly accessible image URL
    const imageUrl = 'https://picsum.photos/1080/1080';
    const caption = `🤖 AI Employee Gold Tier - Live Test!\n\nAutomated post via Instagram Graph API.\n\nTimestamp: ${new Date().toISOString()}\n\n#AIEmployee #Automation #GoldTier #Hackathon #Tech`;

    const result = await client.publishPost(caption, imageUrl, 'IMAGE');
    console.log(`✓ Post published successfully!`);
    console.log(`  Post ID: ${result.id}`);
    return { success: true, post_id: result.id };
  } catch (err) {
    console.log(`✗ Post failed: ${err.message}`);
    return { success: false, error: err.message };
  }
}

// ─────────────────────────────────────────────────────────────
// 3. TWITTER
// ─────────────────────────────────────────────────────────────
async function testTwitter() {
  await separator('3. TWITTER - Publish Tweet');

  const { TwitterClient } = await import('./mcp/twitter-server/src/client/twitter-client.js');

  const client = new TwitterClient({
    bearer_token: process.env.TWITTER_BEARER_TOKEN,
    api_key: process.env.TWITTER_API_KEY,
    api_secret: process.env.TWITTER_API_SECRET,
    access_token: process.env.TWITTER_ACCESS_TOKEN,
    access_token_secret: process.env.TWITTER_ACCESS_TOKEN_SECRET,
    timeout: 30000,
  });

  // Step 1: Test connection by searching
  console.log('\n[3a] Testing Twitter API connection...');
  try {
    const searchResult = await client.searchTweets('AI automation', { max_results: 10 });
    console.log(`✓ Twitter API connected! Found ${searchResult.data?.length || 0} tweets`);
    console.log(`  Raw response keys: ${Object.keys(searchResult)}`);
  } catch (err) {
    console.log(`✗ Twitter API connection failed: ${err.message}`);
  }

  // Step 2: Publish a tweet
  console.log('\n[3b] Publishing tweet...');
  try {
    const tweetContent = `🤖 AI Employee Gold Tier - Live Test!\n\nAutomated tweet via Twitter API v2.\n\nTimestamp: ${new Date().toISOString()}\n\n#AIEmployee #Automation #GoldTier`;

    // Truncate to 280 chars
    const truncated = tweetContent.substring(0, 280);

    const result = await client.publishTweet(truncated);
    console.log(`  Raw response: ${JSON.stringify(result).substring(0, 500)}`);
    console.log(`✓ Tweet published successfully!`);
    console.log(`  Tweet ID: ${result.data?.id}`);
    console.log(`  URL: https://twitter.com/i/web/status/${result.data?.id}`);
    return { success: true, tweet_id: result.data?.id };
  } catch (err) {
    console.log(`✗ Tweet failed: ${err.message}`);
    return { success: false, error: err.message };
  }
}

// ─────────────────────────────────────────────────────────────
// 4. ODOO
// ─────────────────────────────────────────────────────────────
async function testOdoo() {
  await separator('4. ODOO - Accounting Connection');

  const { OdooClient } = await import('./mcp/odoo-server/src/client/odoo-client.js');

  const client = new OdooClient({
    url: process.env.ODOO_URL,
    db: process.env.ODOO_DB,
    username: process.env.ODOO_USERNAME,
    password: process.env.ODOO_PASSWORD,
    timeout: 30000,
  });

  // Step 1: Authenticate
  console.log('\n[4a] Authenticating with Odoo...');
  try {
    const uid = await client.authenticate();
    if (!uid || uid === false) {
      console.log(`✗ Authentication returned UID=${uid} (invalid credentials)`);
      console.log(`  URL: ${process.env.ODOO_URL}`);
      console.log(`  DB: ${process.env.ODOO_DB}`);
      console.log(`  User: ${process.env.ODOO_USERNAME}`);
      return { success: false, error: 'Invalid Odoo credentials (UID=false)' };
    }
    console.log(`✓ Authenticated! UID: ${uid}`);
  } catch (err) {
    console.log(`✗ Authentication failed: ${err.message}`);
    return { success: false, error: err.message };
  }

  // Step 2: Get partners (customers)
  console.log('\n[4b] Fetching Odoo partners...');
  try {
    const partners = await client.searchRead('res.partner', [['is_company', '=', true]], ['name', 'email', 'phone'], 5);
    console.log(`✓ Found ${partners.length} company partners:`);
    partners.forEach(p => console.log(`  - ${p.name} (${p.email || 'no email'})`));
  } catch (err) {
    console.log(`✗ Partners fetch failed: ${err.message}`);
  }

  // Step 3: Get invoices
  console.log('\n[4c] Fetching Odoo invoices...');
  try {
    const invoices = await client.searchRead(
      'account.move',
      [['move_type', 'in', ['out_invoice', 'in_invoice']]],
      ['name', 'partner_id', 'amount_total', 'state', 'payment_state'],
      5
    );
    console.log(`✓ Found ${invoices.length} invoices:`);
    invoices.forEach(inv => {
      const partner = inv.partner_id ? inv.partner_id[1] : 'N/A';
      console.log(`  - ${inv.name}: $${inv.amount_total} (${inv.state}) - ${partner}`);
    });
  } catch (err) {
    console.log(`✗ Invoices fetch failed: ${err.message}`);
  }

  // Step 4: Get financial summary (journals)
  console.log('\n[4d] Fetching Odoo journals...');
  try {
    const journals = await client.searchRead('account.journal', [], ['name', 'type', 'default_account_id'], 10);
    console.log(`✓ Found ${journals.length} journals:`);
    journals.forEach(j => console.log(`  - ${j.name} (${j.type})`));
  } catch (err) {
    console.log(`✗ Journals fetch failed: ${err.message}`);
  }

  return { success: true };
}

// ─────────────────────────────────────────────────────────────
// 5. ODOO WATCHER (Python)
// ─────────────────────────────────────────────────────────────
async function testOdooWatcher() {
  await separator('5. ODOO WATCHER - Python');

  console.log('\n[5a] Running odoo_watcher.py single poll...');
  const { execSync } = await import('child_process');
  try {
    const output = execSync('cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee && python3 odoo_watcher.py --debug 2>&1', {
      timeout: 30000,
      encoding: 'utf-8',
      env: { ...process.env, DRY_RUN: 'false' },
    });
    console.log(output);
    return { success: true };
  } catch (err) {
    console.log(`Output: ${err.stdout || ''}`);
    console.log(`Error: ${err.stderr || err.message}`);
    return { success: false, error: err.message };
  }
}

// ─────────────────────────────────────────────────────────────
// 6. SOCIAL WATCHER (Python)
// ─────────────────────────────────────────────────────────────
async function testSocialWatcher() {
  await separator('6. SOCIAL WATCHER - Python');

  console.log('\n[6a] Running social_watcher.py single poll...');
  const { execSync } = await import('child_process');
  try {
    const output = execSync('cd /mnt/d/Gemini_Cli/hackathon/hackathon_0/AI-Employee && python3 social_watcher.py --debug 2>&1', {
      timeout: 30000,
      encoding: 'utf-8',
      env: { ...process.env, DRY_RUN: 'false' },
    });
    console.log(output);
    return { success: true };
  } catch (err) {
    console.log(`Output: ${err.stdout || ''}`);
    console.log(`Error: ${err.stderr || err.message}`);
    return { success: false, error: err.message };
  }
}

// ─────────────────────────────────────────────────────────────
// MAIN
// ─────────────────────────────────────────────────────────────
async function main() {
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║  AI Employee Gold Tier - Platform Integration Tests     ║');
  console.log('║  Testing: Facebook, Instagram, Twitter, Odoo           ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log(`\nTimestamp: ${new Date().toISOString()}`);

  const results = {};

  // Run each test one by one
  results.facebook = await testFacebook();
  results.instagram = await testInstagram();
  results.twitter = await testTwitter();
  results.odoo = await testOdoo();
  results.odoo_watcher = await testOdooWatcher();
  results.social_watcher = await testSocialWatcher();

  // Summary
  await separator('SUMMARY');
  console.log('\nPlatform Results:');
  for (const [platform, result] of Object.entries(results)) {
    const status = result?.success ? '✓ SUCCESS' : '✗ FAILED';
    const detail = result?.error ? ` - ${result.error}` : '';
    console.log(`  ${platform.padEnd(20)} ${status}${detail}`);
  }

  console.log('\nDone!');
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
