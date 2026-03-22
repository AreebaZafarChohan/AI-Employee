#!/usr/bin/env node
/**
 * Facebook MCP Server — Social Marketing
 *
 * Tools: generate_post, schedule_post, publish_post, fetch_comments, summarize_engagement
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { loadEnv } from '../shared/env.js';
import { log, auditStart } from '../shared/logger.js';
import { saveDraft, queuePost, logPosted, saveAnalytics } from '../shared/vault.js';

loadEnv();

const P = 'facebook';
const CFG = {
  access_token: process.env.FACEBOOK_ACCESS_TOKEN || '',
  page_id: process.env.FACEBOOK_PAGE_ID || 'me',
  api_version: process.env.FACEBOOK_API_VERSION || 'v18.0',
  timeout: parseInt(process.env.FACEBOOK_TIMEOUT || '30000'),
};
const DRY_RUN = process.env.DRY_RUN?.toLowerCase() === 'true';
const BASE = `https://graph.facebook.com/${CFG.api_version}`;

// ─────────── HTTP helper ───────────

async function fbApi(endpoint, method = 'GET', body = null) {
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
  } catch (e) {
    clearTimeout(t);
    if (e.name === 'AbortError') throw new Error('Facebook API timeout');
    throw e;
  }
}

// ─────────── Tool implementations ───────────

async function generatePost(params) {
  const audit = auditStart(P, 'generate_post', params);
  try {
    const content = params.content || params.topic
      ? `${params.content || ''}\n\n${(params.hashtags || []).map(h => h.startsWith('#') ? h : '#' + h).join(' ')}`.trim()
      : '';
    if (!content) throw new Error('content or topic required');

    const draft = saveDraft(P, content, { hashtags: params.hashtags });
    const result = { success: true, status: 'draft', content, draft_id: draft.id, vault_path: draft.path };
    audit.success(result);
    return result;
  } catch (e) { audit.error(e); throw e; }
}

async function schedulePost(params) {
  const audit = auditStart(P, 'schedule_post', params, { dry_run: DRY_RUN || params.dry_run });
  try {
    if (!params.content) throw new Error('content required');
    if (!params.scheduled_at) throw new Error('scheduled_at required (ISO 8601)');

    if (DRY_RUN || params.dry_run) {
      const q = queuePost(P, params.content, { scheduled_at: params.scheduled_at, link: params.link });
      const result = { success: true, dry_run: true, status: 'queued_locally', queue_file: q.path };
      audit.success(result);
      return result;
    }

    const body = {
      message: params.content,
      published: false,
      scheduled_publish_time: Math.floor(new Date(params.scheduled_at).getTime() / 1000),
    };
    if (params.link) body.link = params.link;

    const res = await fbApi(`${CFG.page_id}/feed`, 'POST', body);
    const q = queuePost(P, params.content, { scheduled_at: params.scheduled_at });
    const result = { success: true, post_id: res.id, status: 'scheduled', scheduled_at: params.scheduled_at, queue_file: q.path };
    audit.success(result);
    return result;
  } catch (e) { audit.error(e); throw e; }
}

async function publishPost(params) {
  const audit = auditStart(P, 'publish_post', params, { dry_run: DRY_RUN || params.dry_run });
  try {
    if (!params.content) throw new Error('content required');

    if (DRY_RUN || params.dry_run) {
      const d = saveDraft(P, params.content, { link: params.link });
      const result = { success: true, dry_run: true, status: 'draft_saved', draft_file: d.path };
      audit.success(result);
      return result;
    }

    const body = { message: params.content };
    if (params.link) body.link = params.link;
    if (params.photo_url) body.picture = params.photo_url;

    const res = await fbApi(`${CFG.page_id}/feed`, 'POST', body);
    const posted = logPosted(P, params.content, { post_id: res.id, post_url: `https://facebook.com/${res.id}` });
    const result = { success: true, post_id: res.id, post_url: `https://facebook.com/${res.id}`, log_file: posted.path };
    audit.success(result);
    return result;
  } catch (e) { audit.error(e); throw e; }
}

async function fetchComments(params) {
  const audit = auditStart(P, 'fetch_comments', params);
  try {
    if (!params.post_id) throw new Error('post_id required');
    const res = await fbApi(`${params.post_id}/comments`, 'GET');
    // add fields via URL
    const url = new URL(`${BASE}/${params.post_id}/comments`);
    url.searchParams.set('access_token', CFG.access_token);
    url.searchParams.set('fields', 'from,message,created_time,like_count');
    url.searchParams.set('limit', String(params.limit || 25));
    const r = await fetch(url.toString()).then(r => r.json());
    if (r.error) throw new Error(r.error.message);

    const comments = (r.data || []).map(c => ({
      id: c.id,
      author: c.from?.name || 'Unknown',
      message: c.message,
      created_at: c.created_time,
      likes: c.like_count || 0,
    }));

    const result = { success: true, post_id: params.post_id, count: comments.length, comments };
    audit.success(result);
    return result;
  } catch (e) { audit.error(e); throw e; }
}

async function summarizeEngagement(params) {
  const audit = auditStart(P, 'summarize_engagement', params);
  try {
    // Get page info
    const page = await fbApi(CFG.page_id, 'GET');

    // Get recent posts
    const url = new URL(`${BASE}/${CFG.page_id}/posts`);
    url.searchParams.set('access_token', CFG.access_token);
    url.searchParams.set('limit', String(params.limit || 10));
    url.searchParams.set('fields', 'id,message,created_time,shares,likes.summary(true),comments.summary(true)');
    const postsRes = await fetch(url.toString()).then(r => r.json());
    if (postsRes.error) throw new Error(postsRes.error.message);

    const posts = (postsRes.data || []).map(p => ({
      id: p.id,
      message: (p.message || '').slice(0, 80),
      created_at: p.created_time,
      likes: p.likes?.summary?.total_count || 0,
      comments: p.comments?.summary?.total_count || 0,
      shares: p.shares?.count || 0,
    }));

    const totals = posts.reduce((a, p) => ({
      likes: a.likes + p.likes,
      comments: a.comments + p.comments,
      shares: a.shares + p.shares,
    }), { likes: 0, comments: 0, shares: 0 });

    const summary = {
      platform: P,
      page_name: page.name,
      page_id: page.id,
      period: `last ${posts.length} posts`,
      totals,
      avg_engagement: posts.length ? Math.round((totals.likes + totals.comments + totals.shares) / posts.length) : 0,
      posts,
    };

    const analytics = saveAnalytics(P, summary);
    const result = { success: true, ...summary, vault_file: analytics.path };
    audit.success(result);
    return result;
  } catch (e) { audit.error(e); throw e; }
}

// ─────────── MCP Server ───────────

const server = new McpServer({ name: 'social-mcp-facebook', version: '2.0.0' });

function h(fn) {
  return async (params) => {
    try {
      const r = await fn(params);
      return { content: [{ type: 'text', text: JSON.stringify(r, null, 2) }] };
    } catch (e) {
      return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: e.message }) }], isError: true };
    }
  };
}

server.tool('fb_generate_post', 'Generate a Facebook post draft and save to vault',
  { content: { type: 'string', description: 'Post content' }, hashtags: { type: 'array', items: { type: 'string' } }, topic: { type: 'string' } }, h(generatePost));

server.tool('fb_schedule_post', 'Schedule a Facebook post for later',
  { content: { type: 'string' }, scheduled_at: { type: 'string', description: 'ISO 8601 datetime' }, link: { type: 'string' }, dry_run: { type: 'boolean' } }, h(schedulePost));

server.tool('fb_publish_post', 'Publish a post to Facebook immediately',
  { content: { type: 'string' }, link: { type: 'string' }, photo_url: { type: 'string' }, dry_run: { type: 'boolean' } }, h(publishPost));

server.tool('fb_fetch_comments', 'Fetch comments on a Facebook post',
  { post_id: { type: 'string' }, limit: { type: 'number' } }, h(fetchComments));

server.tool('fb_summarize_engagement', 'Get Facebook page engagement summary',
  { limit: { type: 'number', description: 'Number of recent posts to analyze' } }, h(summarizeEngagement));

// Boot
async function main() {
  console.error('═══ Social MCP: Facebook v2.0 ═══');
  console.error(`Page ID: ${CFG.page_id} | DRY_RUN: ${DRY_RUN}`);
  if (!CFG.access_token) console.error('⚠ FACEBOOK_ACCESS_TOKEN not set');
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('✓ 5 tools registered');
}
main().catch(e => { console.error('Fatal:', e); process.exit(1); });
