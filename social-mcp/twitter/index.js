#!/usr/bin/env node
/**
 * Twitter (X) MCP Server — Social Marketing
 *
 * Uses OAuth 1.0a for posting (required by Twitter API v2).
 * Bearer token used for read-only endpoints.
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { createHmac, randomBytes } from 'node:crypto';
import { loadEnv } from '../shared/env.js';
import { log, auditStart } from '../shared/logger.js';
import { saveDraft, queuePost, logPosted, saveAnalytics } from '../shared/vault.js';

loadEnv();

const P = 'twitter';
const CFG = {
  bearer: process.env.TWITTER_BEARER_TOKEN || '',
  api_key: process.env.TWITTER_API_KEY || '',
  api_secret: process.env.TWITTER_API_SECRET || '',
  access_token: process.env.TWITTER_ACCESS_TOKEN || '',
  access_secret: process.env.TWITTER_ACCESS_TOKEN_SECRET || '',
  timeout: parseInt(process.env.TWITTER_TIMEOUT || '30000'),
};
const DRY_RUN = process.env.DRY_RUN?.toLowerCase() === 'true';
const BASE = 'https://api.twitter.com/2';

// ─────────── OAuth 1.0a Signature ───────────

function percentEncode(str) {
  return encodeURIComponent(str).replace(/[!'()*]/g, c => '%' + c.charCodeAt(0).toString(16).toUpperCase());
}

function generateOAuthHeader(method, url, params = {}) {
  const oauthParams = {
    oauth_consumer_key: CFG.api_key,
    oauth_nonce: randomBytes(16).toString('hex'),
    oauth_signature_method: 'HMAC-SHA1',
    oauth_timestamp: Math.floor(Date.now() / 1000).toString(),
    oauth_token: CFG.access_token,
    oauth_version: '1.0',
  };

  // Combine all params for signature base
  const allParams = { ...oauthParams, ...params };
  const paramString = Object.keys(allParams).sort()
    .map(k => `${percentEncode(k)}=${percentEncode(allParams[k])}`)
    .join('&');

  const signatureBase = `${method.toUpperCase()}&${percentEncode(url)}&${percentEncode(paramString)}`;
  const signingKey = `${percentEncode(CFG.api_secret)}&${percentEncode(CFG.access_secret)}`;
  const signature = createHmac('sha1', signingKey).update(signatureBase).digest('base64');

  oauthParams.oauth_signature = signature;

  return 'OAuth ' + Object.keys(oauthParams).sort()
    .map(k => `${percentEncode(k)}="${percentEncode(oauthParams[k])}"`)
    .join(', ');
}

// ─────────── API helpers ───────────

async function twitterGet(endpoint, params = {}) {
  const url = new URL(`${BASE}/${endpoint}`);
  Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), CFG.timeout);
  try {
    const res = await fetch(url.toString(), {
      headers: { Authorization: `Bearer ${CFG.bearer}` },
      signal: ac.signal,
    });
    clearTimeout(t);
    const json = await res.json();
    if (json.errors) throw new Error(json.errors[0]?.message || JSON.stringify(json.errors));
    if (json.title && json.detail) throw new Error(`${json.title}: ${json.detail}`);
    return json;
  } catch (e) { clearTimeout(t); if (e.name === 'AbortError') throw new Error('Twitter API timeout'); throw e; }
}

async function twitterPost(endpoint, body = {}) {
  const url = `${BASE}/${endpoint}`;
  const authHeader = generateOAuthHeader('POST', url);
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), CFG.timeout);
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { Authorization: authHeader, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ac.signal,
    });
    clearTimeout(t);
    const json = await res.json();
    if (json.errors) throw new Error(json.errors[0]?.message || JSON.stringify(json.errors));
    if (json.title && json.detail) throw new Error(`${json.title}: ${json.detail}`);
    return json;
  } catch (e) { clearTimeout(t); if (e.name === 'AbortError') throw new Error('Twitter API timeout'); throw e; }
}

// ─── Tools ───

async function generatePost(params) {
  const audit = auditStart(P, 'generate_post', params);
  try {
    let content = params.content || '';
    if (params.hashtags?.length) content += '\n\n' + params.hashtags.map(h => h.startsWith('#') ? h : '#' + h).join(' ');
    content = content.trim();
    if (!content) throw new Error('content required');
    if (content.length > 280) throw new Error(`Tweet is ${content.length} chars — max 280`);

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
    if (params.content.length > 280) throw new Error(`Tweet is ${params.content.length} chars — max 280`);

    // Twitter API doesn't support scheduling — queue locally
    const q = queuePost(P, params.content, { scheduled_at: params.scheduled_at });
    const result = { success: true, status: 'queued', scheduled_at: params.scheduled_at, queue_file: q.path, note: 'Queued for automated pickup at scheduled time' };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function publishPost(params) {
  const audit = auditStart(P, 'publish_post', params, { dry_run: DRY_RUN || params.dry_run });
  try {
    if (!params.content) throw new Error('content required');
    if (params.content.length > 280) throw new Error(`Tweet is ${params.content.length} chars — max 280`);

    if (DRY_RUN || params.dry_run) {
      const d = saveDraft(P, params.content);
      return { success: true, dry_run: true, draft_file: d.path };
    }

    const res = await twitterPost('tweets', { text: params.content });
    const tweetId = res.data?.id;
    const posted = logPosted(P, params.content, { tweet_id: tweetId, tweet_url: `https://x.com/i/status/${tweetId}` });
    const result = { success: true, tweet_id: tweetId, tweet_url: `https://x.com/i/status/${tweetId}`, log_file: posted.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function fetchComments(params) {
  const audit = auditStart(P, 'fetch_comments', params);
  try {
    if (!params.tweet_id) throw new Error('tweet_id required');
    // Search for replies to the tweet
    const res = await twitterGet('tweets/search/recent', {
      query: `conversation_id:${params.tweet_id}`,
      max_results: String(params.limit || 25),
      'tweet.fields': 'author_id,created_at,public_metrics,text',
    });

    const comments = (res.data || []).map(t => ({
      id: t.id, author_id: t.author_id, text: t.text, created_at: t.created_at,
      likes: t.public_metrics?.like_count || 0, retweets: t.public_metrics?.retweet_count || 0,
    }));
    const result = { success: true, tweet_id: params.tweet_id, count: comments.length, comments };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

async function summarizeEngagement(params) {
  const audit = auditStart(P, 'summarize_engagement', params);
  try {
    // Get authenticated user
    const me = await twitterGet('users/me', { 'user.fields': 'public_metrics,name,username' });
    const user = me.data;

    // Get recent tweets
    const tweets = await twitterGet(`users/${user.id}/tweets`, {
      max_results: String(Math.min(params.limit || 10, 100)),
      'tweet.fields': 'created_at,public_metrics,text',
    });

    const posts = (tweets.data || []).map(t => ({
      id: t.id, text: t.text.slice(0, 80), created_at: t.created_at,
      likes: t.public_metrics?.like_count || 0,
      retweets: t.public_metrics?.retweet_count || 0,
      replies: t.public_metrics?.reply_count || 0,
      impressions: t.public_metrics?.impression_count || 0,
    }));

    const totals = posts.reduce((a, p) => ({
      likes: a.likes + p.likes, retweets: a.retweets + p.retweets,
      replies: a.replies + p.replies, impressions: a.impressions + p.impressions,
    }), { likes: 0, retweets: 0, replies: 0, impressions: 0 });

    const summary = {
      platform: P, username: user.username, name: user.name,
      followers: user.public_metrics?.followers_count,
      following: user.public_metrics?.following_count,
      total_tweets: user.public_metrics?.tweet_count,
      period: `last ${posts.length} tweets`, totals,
      avg_engagement: posts.length ? Math.round((totals.likes + totals.retweets + totals.replies) / posts.length) : 0,
      posts,
    };

    const analytics = saveAnalytics(P, summary);
    const result = { success: true, ...summary, vault_file: analytics.path };
    audit.success(result); return result;
  } catch (e) { audit.error(e); throw e; }
}

// ─── MCP ───

const server = new McpServer({ name: 'social-mcp-twitter', version: '2.0.0' });
function h(fn) { return async (p) => { try { return { content: [{ type: 'text', text: JSON.stringify(await fn(p), null, 2) }] }; } catch (e) { return { content: [{ type: 'text', text: JSON.stringify({ success: false, error: e.message }) }], isError: true }; } }; }

server.tool('tw_generate_post', 'Generate a tweet draft (max 280 chars)', { content: { type: 'string' }, hashtags: { type: 'array', items: { type: 'string' } } }, h(generatePost));
server.tool('tw_schedule_post', 'Queue a tweet for scheduled publishing', { content: { type: 'string' }, scheduled_at: { type: 'string' }, dry_run: { type: 'boolean' } }, h(schedulePost));
server.tool('tw_publish_post', 'Publish a tweet using OAuth 1.0a', { content: { type: 'string' }, dry_run: { type: 'boolean' } }, h(publishPost));
server.tool('tw_fetch_comments', 'Fetch replies to a tweet', { tweet_id: { type: 'string' }, limit: { type: 'number' } }, h(fetchComments));
server.tool('tw_summarize_engagement', 'Get Twitter account engagement summary', { limit: { type: 'number' } }, h(summarizeEngagement));

async function main() {
  console.error('═══ Social MCP: Twitter v2.0 ═══');
  console.error(`DRY_RUN: ${DRY_RUN} | OAuth 1.0a: ${CFG.api_key ? 'configured' : 'NOT SET'}`);
  if (!CFG.bearer) console.error('⚠ TWITTER_BEARER_TOKEN not set');
  if (!CFG.api_key) console.error('⚠ TWITTER_API_KEY not set (required for posting)');
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('✓ 5 tools registered');
}
main().catch(e => { console.error('Fatal:', e); process.exit(1); });
