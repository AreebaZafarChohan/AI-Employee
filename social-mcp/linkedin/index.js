#!/usr/bin/env node
/**
 * LinkedIn MCP Server — Social Marketing (Improved v2)
 *
 * Uses LinkedIn Marketing API (OAuth 2.0) instead of Playwright.
 * Falls back to vault-only draft mode if no API token.
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { loadEnv } from '../shared/env.js';
import { log, auditStart } from '../shared/logger.js';
import { saveDraft, queuePost, logPosted, saveAnalytics } from '../shared/vault.js';

loadEnv();

const P = 'linkedin';
const CFG = {
  access_token: process.env.LINKEDIN_ACCESS_TOKEN || '',
  org_id: process.env.LINKEDIN_ORG_ID || '',
  person_urn: process.env.LINKEDIN_PERSON_URN || '', // urn:li:person:xxxxx
  timeout: parseInt(process.env.LINKEDIN_TIMEOUT || '30000'),
};
const DRY_RUN = process.env.DRY_RUN?.toLowerCase() === 'true';
const BASE = 'https://api.linkedin.com/v2';
const HAS_API = CFG.access_token && CFG.access_token !== 'your_linkedin_access_token';

async function liApi(endpoint, method = 'GET', body = null) {
  if (!HAS_API) throw new Error('LINKEDIN_ACCESS_TOKEN not configured — using draft-only mode');
  const url = `${BASE}/${endpoint}`;
  const opts = {
    method,
    headers: {
      Authorization: `Bearer ${CFG.access_token}`,
      'Content-Type': 'application/json',
      'X-Restli-Protocol-Version': '2.0.0',
      'LinkedIn-Version': '202401',
    },
  };
  if (body) opts.body = JSON.stringify(body);
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), CFG.timeout);
  try {
    const res = await fetch(url, { ...opts, signal: ac.signal });
    clearTimeout(t);
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`LinkedIn API ${res.status}: ${text.slice(0, 200)}`);
    }
    const text = await res.text();
    return text ? JSON.parse(text) : {};
  } catch (e) { clearTimeout(t); if (e.name === 'AbortError') throw new Error('LinkedIn API timeout'); throw e; }
}

// ─── Tools ───

async function generatePost(params) {
  const audit = auditStart(P, 'generate_post', params);
  try {
    let content = params.content || '';
    if (params.hashtags?.length) content += '\n\n' + params.hashtags.map(h => h.startsWith('#') ? h : '#' + h).join(' ');
    content = content.trim();
    if (!content) throw new Error('content required');
    if (content.length > 3000) throw new Error(`Post is ${content.length} chars — LinkedIn max is 3000`);

    const draft = saveDraft(P, content, { hashtags: params.hashtags });
    const result = { success: true, status: 'draft', content, char_count: content.length, draft_id: draft.id, vault_path: draft.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function schedulePost(params) {
  const audit = auditStart(P, 'schedule_post', params);
  try {
    if (!params.content) throw new Error('content required');
    if (!params.scheduled_at) throw new Error('scheduled_at required');

    const q = queuePost(P, params.content, { scheduled_at: params.scheduled_at });
    const result = { success: true, status: 'queued', scheduled_at: params.scheduled_at, queue_file: q.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function publishPost(params) {
  const audit = auditStart(P, 'publish_post', params, { dry_run: DRY_RUN || params.dry_run });
  try {
    if (!params.content) throw new Error('content required');

    if (DRY_RUN || params.dry_run || !HAS_API) {
      const d = saveDraft(P, params.content);
      return { success: true, dry_run: true, reason: HAS_API ? 'dry_run flag' : 'no API token', draft_file: d.path };
    }

    // Determine author URN
    const authorUrn = CFG.org_id
      ? `urn:li:organization:${CFG.org_id}`
      : CFG.person_urn || (await getPersonUrn());

    const body = {
      author: authorUrn,
      lifecycleState: 'PUBLISHED',
      specificContent: {
        'com.linkedin.ugc.ShareContent': {
          shareCommentary: { text: params.content },
          shareMediaCategory: 'NONE',
        },
      },
      visibility: { 'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC' },
    };

    if (params.link) {
      body.specificContent['com.linkedin.ugc.ShareContent'].shareMediaCategory = 'ARTICLE';
      body.specificContent['com.linkedin.ugc.ShareContent'].media = [{
        status: 'READY',
        originalUrl: params.link,
      }];
    }

    const res = await liApi('ugcPosts', 'POST', body);
    const postId = res.id || res['X-RestLi-Id'] || 'unknown';
    const posted = logPosted(P, params.content, { post_id: postId, post_url: `https://linkedin.com/feed/update/${postId}` });
    const result = { success: true, post_id: postId, log_file: posted.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function getPersonUrn() {
  const me = await liApi('me');
  return `urn:li:person:${me.id}`;
}

async function fetchComments(params) {
  const audit = auditStart(P, 'fetch_comments', params);
  try {
    if (!params.post_urn) throw new Error('post_urn required (e.g. urn:li:share:123456)');
    if (!HAS_API) throw new Error('LINKEDIN_ACCESS_TOKEN required for fetching comments');

    const res = await liApi(`socialActions/${encodeURIComponent(params.post_urn)}/comments?count=${params.limit || 25}`);
    const comments = (res.elements || []).map(c => ({
      id: c['$URN'] || c.id,
      author: c.actor,
      message: c.message?.text || '',
      created_at: c.created?.time ? new Date(c.created.time).toISOString() : null,
      likes: c.likesSummary?.totalLikes || 0,
    }));

    const result = { success: true, post_urn: params.post_urn, count: comments.length, comments };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function summarizeEngagement(params) {
  const audit = auditStart(P, 'summarize_engagement', params);
  try {
    if (!HAS_API) {
      const result = { success: false, error: 'LINKEDIN_ACCESS_TOKEN required', note: 'Configure LinkedIn API token for engagement data' };
      audit.error(new Error(result.error)); return result;
    }

    const me = await liApi('me', 'GET');

    // Organization stats if org_id available
    let orgData = null;
    if (CFG.org_id) {
      try {
        orgData = await liApi(`organizationalEntityFollowerStatistics?q=organizationalEntity&organizationalEntity=urn:li:organization:${CFG.org_id}`);
      } catch { /* may not have permissions */ }
    }

    const summary = {
      platform: P,
      user: { id: me.id, name: `${me.localizedFirstName} ${me.localizedLastName}` },
      organization: CFG.org_id ? { id: CFG.org_id, followers: orgData?.elements?.[0]?.followerCounts?.organicFollowerCount } : null,
      note: 'LinkedIn API has limited analytics access. Use LinkedIn Campaign Manager for full analytics.',
    };

    const analytics = saveAnalytics(P, summary);
    const result = { success: true, ...summary, vault_file: analytics.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

// ─── MCP ───

const server = new McpServer({ name: 'social-mcp-linkedin', version: '2.0.0' });
function h(fn) { return async (p) => { try { return { content: [{ type: 'text', text: JSON.stringify(await fn(p), null, 2) }] }; } catch (e) { return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: e.message }) }], isError: true }; } }; }

server.tool('li_generate_post', 'Generate a LinkedIn post draft (max 3000 chars)', { content: { type: 'string' }, hashtags: { type: 'array', items: { type: 'string' } } }, h(generatePost));
server.tool('li_schedule_post', 'Queue a LinkedIn post for scheduled publishing', { content: { type: 'string' }, scheduled_at: { type: 'string' } }, h(schedulePost));
server.tool('li_publish_post', 'Publish a post to LinkedIn via API', { content: { type: 'string' }, link: { type: 'string' }, dry_run: { type: 'boolean' } }, h(publishPost));
server.tool('li_fetch_comments', 'Fetch comments on a LinkedIn post', { post_urn: { type: 'string' }, limit: { type: 'number' } }, h(fetchComments));
server.tool('li_summarize_engagement', 'Get LinkedIn engagement summary', { limit: { type: 'number' } }, h(summarizeEngagement));

async function main() {
  console.error('═══ Social MCP: LinkedIn v2.0 ═══');
  console.error(`API mode: ${HAS_API ? 'LIVE' : 'DRAFT-ONLY (no token)'} | DRY_RUN: ${DRY_RUN}`);
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('✓ 5 tools registered');
}
main().catch(e => { console.error('Fatal:', e); process.exit(1); });
