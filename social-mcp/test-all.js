#!/usr/bin/env node
/**
 * Test all social MCP servers — vault integration, draft mode, and API connectivity
 */
import { loadEnv } from './shared/env.js';
import { saveDraft, queuePost, logPosted, saveAnalytics, listQueue, listDrafts, approveDraft, paths } from './shared/vault.js';

loadEnv();

function hr(label) {
  console.log(`\n${'═'.repeat(50)}`);
  console.log(`  ${label}`);
  console.log('═'.repeat(50));
}

async function main() {
  console.log('╔════════════════════════════════════════════╗');
  console.log('║  Social MCP — Integration Test Suite       ║');
  console.log('╚════════════════════════════════════════════╝');
  console.log(`Vault: ${paths.VAULT}`);

  // ── 1. Vault Operations ──
  hr('1. Vault: Draft → Queue → Posted Flow');

  const draft = saveDraft('facebook', 'Test post from integration test\n\n#test #automation');
  console.log(`✓ Draft saved: ${draft.filename}`);

  const queued = queuePost('twitter', 'Test tweet queued', { scheduled_at: '2026-03-15T10:00:00Z' });
  console.log(`✓ Queued: ${queued.filename}`);

  const posted = logPosted('instagram', 'Test IG post logged', { post_id: '12345', post_url: 'https://instagram.com/p/test' });
  console.log(`✓ Posted log: ${posted.filename}`);

  const analytics = saveAnalytics('linkedin', { followers: 500, posts: 10, engagement_rate: '3.2%' });
  console.log(`✓ Analytics: ${analytics.filename}`);

  // Approval flow
  const drafts = listDrafts('facebook');
  console.log(`\n  Drafts: ${drafts.length}`);
  if (drafts.length) {
    const approved = approveDraft(drafts[0]);
    console.log(`✓ Draft approved → Queue: ${approved}`);
  }

  const queue = listQueue();
  console.log(`  Queue total: ${queue.length}`);

  // ── 2. Platform Connectivity ──
  hr('2. Facebook API');
  try {
    const token = process.env.FACEBOOK_ACCESS_TOKEN;
    if (!token) { console.log('⚠ FACEBOOK_ACCESS_TOKEN not set — skipping'); }
    else {
      const res = await fetch(`https://graph.facebook.com/v18.0/${process.env.FACEBOOK_PAGE_ID}?fields=name,id&access_token=${token}`);
      const json = await res.json();
      if (json.error) console.log(`✗ ${json.error.message}`);
      else console.log(`✓ Page: ${json.name} (${json.id})`);
    }
  } catch (e) { console.log(`✗ ${e.message}`); }

  hr('3. Instagram API');
  try {
    const token = process.env.INSTAGRAM_ACCESS_TOKEN;
    if (!token) { console.log('⚠ INSTAGRAM_ACCESS_TOKEN not set — skipping'); }
    else {
      const res = await fetch(`https://graph.facebook.com/v18.0/${process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID}?fields=username,id&access_token=${token}`);
      const json = await res.json();
      if (json.error) console.log(`✗ ${json.error.message}`);
      else console.log(`✓ Account: ${json.username || json.id}`);
    }
  } catch (e) { console.log(`✗ ${e.message}`); }

  hr('4. Twitter API (Bearer)');
  try {
    const bearer = process.env.TWITTER_BEARER_TOKEN;
    if (!bearer) { console.log('⚠ TWITTER_BEARER_TOKEN not set — skipping'); }
    else {
      const res = await fetch('https://api.twitter.com/2/tweets/search/recent?query=test&max_results=10', {
        headers: { Authorization: `Bearer ${bearer}` },
      });
      const json = await res.json();
      if (json.errors || json.title) console.log(`✗ ${json.errors?.[0]?.message || json.detail || 'Unknown error'}`);
      else console.log(`✓ Twitter API connected — ${json.data?.length || 0} tweets found`);
    }
  } catch (e) { console.log(`✗ ${e.message}`); }

  hr('5. LinkedIn API');
  try {
    const token = process.env.LINKEDIN_ACCESS_TOKEN;
    if (!token || token === 'your_linkedin_access_token') { console.log('⚠ LINKEDIN_ACCESS_TOKEN not configured — draft-only mode'); }
    else {
      const res = await fetch('https://api.linkedin.com/v2/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (json.status === 401) console.log('✗ Token expired or invalid');
      else console.log(`✓ LinkedIn: ${json.localizedFirstName} ${json.localizedLastName}`);
    }
  } catch (e) { console.log(`✗ ${e.message}`); }

  hr('SUMMARY');
  console.log(`
  Vault Paths:
    Drafts:    ${paths.DRAFTS}
    Queue:     ${paths.QUEUE}
    Posted:    ${paths.POSTED}
    Analytics: ${paths.ANALYTICS}

  Files Created:
    Drafts:    ${listDrafts().length}
    Queued:    ${listQueue().length}
  `);
  console.log('✓ Test complete');
}

main().catch(e => { console.error('Fatal:', e); process.exit(1); });
