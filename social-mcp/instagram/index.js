#!/usr/bin/env node
/**
 * Instagram MCP Server — Social Marketing
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { loadEnv } from '../shared/env.js';
import { log, auditStart } from '../shared/logger.js';
import { saveDraft, queuePost, logPosted, saveAnalytics } from '../shared/vault.js';

loadEnv();

const P = 'instagram';
const CFG = {
  access_token: process.env.INSTAGRAM_ACCESS_TOKEN || '',
  account_id: process.env.INSTAGRAM_BUSINESS_ACCOUNT_ID || '',
  api_version: process.env.INSTAGRAM_API_VERSION || 'v18.0',
  timeout: parseInt(process.env.INSTAGRAM_TIMEOUT || '30000'),
};
const DRY_RUN = process.env.DRY_RUN?.toLowerCase() === 'true';
const BASE = `https://graph.facebook.com/${CFG.api_version}`;

async function igApi(endpoint, method = 'GET', body = null) {
  const url = new URL(`${BASE}/${endpoint}`);
  url.searchParams.set('access_token', CFG.access_token);
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), CFG.timeout);
  try {
    const res = await fetch(url.toString(), { ...opts, signal: ac.signal });
    clearTimeout(t);
    const json = await res.json();
    if (json.error) throw new Error(json.error.message);
    return json;
  } catch (e) { clearTimeout(t); if (e.name === 'AbortError') throw new Error('Instagram API timeout'); throw e; }
}

// ─── Tools ───

async function generatePost(params) {
  const audit = auditStart(P, 'generate_post', params);
  try {
    const caption = `${params.content || ''}\n\n${(params.hashtags || []).map(h => h.startsWith('#') ? h : '#' + h).join(' ')}`.trim();
    if (!caption) throw new Error('content required');
    const draft = saveDraft(P, caption, { hashtags: params.hashtags, media_url: params.media_url });
    const result = { success: true, status: 'draft', caption, draft_id: draft.id, vault_path: draft.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function schedulePost(params) {
  const audit = auditStart(P, 'schedule_post', params, { dry_run: DRY_RUN || params.dry_run });
  try {
    if (!params.content) throw new Error('content required');
    if (!params.scheduled_at) throw new Error('scheduled_at required');
    // Instagram API doesn't natively support scheduling — save to queue
    const q = queuePost(P, params.content, { scheduled_at: params.scheduled_at, media_url: params.media_url });
    const result = { success: true, status: 'queued_for_schedule', scheduled_at: params.scheduled_at, queue_file: q.path, note: 'Instagram does not support native scheduling via API. Post queued for manual/automated pickup.' };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function publishPost(params) {
  const audit = auditStart(P, 'publish_post', params, { dry_run: DRY_RUN || params.dry_run });
  try {
    if (!params.content) throw new Error('content (caption) required');
    if (!params.media_url) throw new Error('media_url required (Instagram requires an image/video)');

    if (DRY_RUN || params.dry_run) {
      const d = saveDraft(P, params.content, { media_url: params.media_url });
      return { success: true, dry_run: true, draft_file: d.path };
    }

    // Step 1: Create media container
    const container = await igApi(`${CFG.account_id}/media`, 'POST', {
      image_url: params.media_url,
      caption: params.content,
      access_token: CFG.access_token,
    });

    // Step 2: Publish
    const pub = await igApi(`${CFG.account_id}/media_publish`, 'POST', {
      creation_id: container.id,
      access_token: CFG.access_token,
    });

    const posted = logPosted(P, params.content, { post_id: pub.id });
    const result = { success: true, post_id: pub.id, log_file: posted.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function fetchComments(params) {
  const audit = auditStart(P, 'fetch_comments', params);
  try {
    if (!params.media_id) throw new Error('media_id required');
    const url = new URL(`${BASE}/${params.media_id}/comments`);
    url.searchParams.set('access_token', CFG.access_token);
    url.searchParams.set('fields', 'id,text,username,timestamp,like_count');
    url.searchParams.set('limit', String(params.limit || 25));
    const r = await fetch(url.toString()).then(r => r.json());
    if (r.error) throw new Error(r.error.message);

    const comments = (r.data || []).map(c => ({
      id: c.id, author: c.username, message: c.text, created_at: c.timestamp, likes: c.like_count || 0,
    }));
    const result = { success: true, media_id: params.media_id, count: comments.length, comments };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function summarizeEngagement(params) {
  const audit = auditStart(P, 'summarize_engagement', params);
  try {
    // Account info
    const url = new URL(`${BASE}/${CFG.account_id}`);
    url.searchParams.set('access_token', CFG.access_token);
    url.searchParams.set('fields', 'id,username,name,followers_count,follows_count,media_count');
    const account = await fetch(url.toString()).then(r => r.json());
    if (account.error) throw new Error(account.error.message);

    // Recent media
    const mUrl = new URL(`${BASE}/${CFG.account_id}/media`);
    mUrl.searchParams.set('access_token', CFG.access_token);
    mUrl.searchParams.set('fields', 'id,caption,media_type,timestamp,like_count,comments_count,permalink');
    mUrl.searchParams.set('limit', String(params.limit || 10));
    const media = await fetch(mUrl.toString()).then(r => r.json());
    if (media.error) throw new Error(media.error.message);

    const posts = (media.data || []).map(m => ({
      id: m.id, caption: (m.caption || '').slice(0, 80), type: m.media_type,
      likes: m.like_count || 0, comments: m.comments_count || 0, permalink: m.permalink,
    }));

    const totals = posts.reduce((a, p) => ({ likes: a.likes + p.likes, comments: a.comments + p.comments }), { likes: 0, comments: 0 });

    const summary = {
      platform: P, username: account.username, followers: account.followers_count,
      media_count: account.media_count, period: `last ${posts.length} posts`,
      totals, avg_engagement: posts.length ? Math.round((totals.likes + totals.comments) / posts.length) : 0,
      posts,
    };

    const analytics = saveAnalytics(P, summary);
    const result = { success: true, ...summary, vault_file: analytics.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

// ─── MCP ───

const server = new McpServer({ name: 'social-mcp-instagram', version: '2.0.0' });
function h(fn) { return async (p) => { try { return { content: [{ type: 'text', text: JSON.stringify(await fn(p), null, 2) }] }; } catch (e) { return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: e.message }) }], isError: true }; } }; }

server.tool('ig_generate_post', 'Generate an Instagram post draft', { content: { type: 'string' }, hashtags: { type: 'array', items: { type: 'string' } }, media_url: { type: 'string' } }, h(generatePost));
server.tool('ig_schedule_post', 'Queue an Instagram post for scheduled publishing', { content: { type: 'string' }, scheduled_at: { type: 'string' }, media_url: { type: 'string' }, dry_run: { type: 'boolean' } }, h(schedulePost));
server.tool('ig_publish_post', 'Publish a post to Instagram (requires media_url)', { content: { type: 'string' }, media_url: { type: 'string' }, dry_run: { type: 'boolean' } }, h(publishPost));
server.tool('ig_fetch_comments', 'Fetch comments on an Instagram post', { media_id: { type: 'string' }, limit: { type: 'number' } }, h(fetchComments));
server.tool('ig_summarize_engagement', 'Get Instagram engagement summary', { limit: { type: 'number' } }, h(summarizeEngagement));

async function main() {
  console.error('═══ Social MCP: Instagram v2.0 ═══');
  console.error(`Account: ${CFG.account_id} | DRY_RUN: ${DRY_RUN}`);
  if (!CFG.access_token) console.error('⚠ INSTAGRAM_ACCESS_TOKEN not set');
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('✓ 5 tools registered');
}
main().catch(e => { console.error('Fatal:', e); process.exit(1); });
