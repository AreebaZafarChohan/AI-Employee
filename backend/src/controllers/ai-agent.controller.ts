/**
 * AI Agent Controller
 * Provides content generation via Gemini/Grok and posting to platforms.
 * Reads real data from vault for post history.
 */

import { Request, Response } from 'express';
import * as fs from 'fs';
import * as path from 'path';
import https from 'https';
import http from 'http';
import { exec } from 'child_process';

const VAULT_PATH = process.env.VAULT_PATH || path.join(__dirname, '..', '..', '..', 'AI-Employee-Vault');
const ROOT_PATH = path.join(__dirname, '..', '..', '..');
const DONE_DIR = path.join(VAULT_PATH, 'Done');
const PENDING_DIR = path.join(VAULT_PATH, 'Pending_Approval');
const LOGS_DIR = path.join(VAULT_PATH, 'Logs');

const GEMINI_API_KEY = process.env.GEMINI_API_KEY || process.env.GOOGLE_AI_API_KEY || '';
const GROK_API_KEY = process.env.GROK_API_KEY || '';

interface PlatformConfig {
  maxChars: number;
  promptTemplate: string;
}

const PLATFORM_CONFIGS: Record<string, PlatformConfig> = {
  twitter: {
    maxChars: 280,
    promptTemplate: 'Write a single tweet (max 270 characters) about: {topic}\nRules:\n- Under 270 characters\n- Include 2-3 hashtags\n- Professional but engaging\n- No quotes or markdown',
  },
  linkedin: {
    maxChars: 1500,
    promptTemplate: 'Write a professional LinkedIn post (500-1500 chars) about: {topic}\nRules:\n- Professional, insightful tone\n- Business insights\n- 3-5 hashtags at the end\n- Engaging hook in first line',
  },
  facebook: {
    maxChars: 800,
    promptTemplate: 'Write a Facebook post (300-800 chars) about: {topic}\nRules:\n- Casual-professional tone\n- Encourage engagement\n- 2-3 hashtags',
  },
  instagram: {
    maxChars: 500,
    promptTemplate: 'Write an Instagram caption (300-500 chars) about: {topic}\nRules:\n- Visual and descriptive\n- 5-10 hashtags at the end\n- Engaging and trendy',
  },
  whatsapp: {
    maxChars: 300,
    promptTemplate: 'Write a short WhatsApp message (under 300 chars) about: {topic}\nRules:\n- Short, direct, personal\n- No hashtags\n- Conversational',
  },
  email: {
    maxChars: 5000,
    promptTemplate: 'Write a professional email about: {topic}\nFormat:\nSubject: <subject>\n\n<body>\nRules:\n- Professional\n- Clear call to action',
  },
};

function fetchJson(url: string, options: { method?: string; headers?: Record<string, string>; body?: string }): Promise<any> {
  return new Promise((resolve, reject) => {
    const parsed = new URL(url);
    const lib = parsed.protocol === 'https:' ? https : http;
    const req = lib.request(url, {
      method: options.method || 'POST',
      headers: options.headers || {},
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch { reject(new Error(`Invalid JSON: ${data.substring(0, 200)}`)); }
      });
    });
    req.on('error', reject);
    if (options.body) req.write(options.body);
    req.end();
    setTimeout(() => req.destroy(new Error('timeout')), 30000);
  });
}

async function generateGemini(prompt: string): Promise<string | null> {
  if (!GEMINI_API_KEY) return null;
  try {
    const result = await fetchJson(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${GEMINI_API_KEY}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] }),
      }
    );
    return result?.candidates?.[0]?.content?.parts?.[0]?.text?.trim()?.replace(/^["']|["']$/g, '') || null;
  } catch (e) {
    console.error('Gemini error:', e);
    return null;
  }
}

async function generateGrok(prompt: string): Promise<string | null> {
  if (!GROK_API_KEY) return null;
  try {
    const result = await fetchJson('https://api.x.ai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${GROK_API_KEY}` },
      body: JSON.stringify({ model: 'grok-3', messages: [{ role: 'user', content: prompt }], max_tokens: 500 }),
    });
    return result?.choices?.[0]?.message?.content?.trim()?.replace(/^["']|["']$/g, '') || null;
  } catch (e) {
    console.error('Grok error:', e);
    return null;
  }
}

function parseMarkdownFrontmatter(content: string): { metadata: Record<string, any>; body: string } {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return { metadata: {}, body: content };
  const metadata: Record<string, any> = {};
  for (const line of match[1].split('\n')) {
    const idx = line.indexOf(':');
    if (idx > -1) {
      const key = line.substring(0, idx).trim();
      let val = line.substring(idx + 1).trim();
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.slice(1, -1);
      }
      metadata[key] = val;
    }
  }
  return { metadata, body: content.replace(match[0], '').trim() };
}

export class AiAgentController {
  /**
   * GET /api/v1/ai-agent/status
   * Returns AI provider and platform status.
   */
  async getStatus(_req: Request, res: Response) {
    try {
      const platforms: Record<string, string> = {};
      const scripts: Record<string, string> = {
        twitter: 'post_to_twitter.py',
        linkedin: 'mcp/linkedin-server/post_executor.js',
        facebook: 'mcp/facebook-server/src/post_executor.js',
        instagram: 'mcp/instagram-server/src/post_executor.js',
      };

      for (const [p, s] of Object.entries(scripts)) {
        platforms[p] = fs.existsSync(path.join(ROOT_PATH, s)) ? 'ready' : 'missing';
      }
      platforms.whatsapp = 'available';
      platforms.email = 'available';

      res.json({
        data: {
          gemini: GEMINI_API_KEY ? 'ready' : 'no_key',
          grok: GROK_API_KEY ? 'ready' : 'no_key',
          platforms,
          supported: Object.keys(PLATFORM_CONFIGS),
        },
      });
    } catch (error) {
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to get agent status' } });
    }
  }

  /**
   * POST /api/v1/ai-agent/generate
   * Generate content for a platform.
   * Body: { platform: string, topic: string }
   */
  async generateContent(req: Request, res: Response): Promise<any> {
    try {
      const { platform, topic } = req.body;
      if (!platform || !topic) {
        return res.status(400).json({ error: { code: 'BAD_REQUEST', message: 'platform and topic required' } });
      }

      const config = PLATFORM_CONFIGS[platform];
      if (!config) {
        return res.status(400).json({ error: { code: 'BAD_REQUEST', message: `Unsupported platform: ${platform}` } });
      }

      const prompt = config.promptTemplate.replace('{topic}', topic);

      // Try Gemini first, fallback to Grok
      let content = await generateGemini(prompt);
      let provider = 'gemini';
      if (!content) {
        content = await generateGrok(prompt);
        provider = 'grok';
      }
      if (!content) {
        return res.status(503).json({ error: { code: 'AI_UNAVAILABLE', message: 'No AI provider available' } });
      }

      if (content.length > config.maxChars) {
        content = content.substring(0, config.maxChars - 3) + '...';
      }

      res.json({
        data: {
          content,
          platform,
          topic,
          provider,
          charCount: content.length,
          maxChars: config.maxChars,
        },
      });
    } catch (error) {
      console.error('Error generating content:', error);
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to generate content' } });
    }
  }

  /**
   * POST /api/v1/ai-agent/post
   * Post content to a platform.
   * Body: { platform: string, content: string }
   */
  async postContent(req: Request, res: Response): Promise<any> {
    try {
      const { platform, content } = req.body;
      if (!platform || !content) {
        return res.status(400).json({ error: { code: 'BAD_REQUEST', message: 'platform and content required' } });
      }

      // Save to Pending_Approval first
      const ts = new Date().toISOString().replace(/[-:T]/g, '').substring(0, 14);
      const slug = content.substring(0, 40).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+$/, '');
      const filename = `social-post-${platform}-${slug}-${ts}.md`;

      if (!fs.existsSync(PENDING_DIR)) fs.mkdirSync(PENDING_DIR, { recursive: true });
      if (!fs.existsSync(DONE_DIR)) fs.mkdirSync(DONE_DIR, { recursive: true });

      const fileContent = `---\nplatform: ${platform}\nstatus: pending\ncreated_at: ${new Date().toISOString()}\nsource: ai-agent-frontend\n---\n\n## Content\n\n${content}\n`;
      const pendingPath = path.join(PENDING_DIR, filename);
      fs.writeFileSync(pendingPath, fileContent, 'utf-8');

      // Try to post via Python ai_agent or MCP executor
      let postResult: any = { success: false, method: 'saved_only' };

      if (platform === 'twitter') {
        // Use post_to_twitter.py via subprocess
        const twitterScript = path.join(ROOT_PATH, 'post_to_twitter.py');
        if (fs.existsSync(twitterScript)) {
          try {
            const tempFile = path.join(ROOT_PATH, '.temp_api_post_content.txt');
            fs.writeFileSync(tempFile, content, 'utf-8');
            await new Promise<void>((resolve, reject) => {
              exec(`python "${twitterScript}" "${content.substring(0, 100)}"`, { cwd: ROOT_PATH, timeout: 30000 }, (err, stdout) => {
                if (err) { reject(err); return; }
                postResult = { success: true, method: 'twitter_api', output: stdout };
                resolve();
              });
            });
            if (fs.existsSync(tempFile)) fs.unlinkSync(tempFile);
          } catch (e: any) {
            postResult = { success: false, method: 'twitter_api', error: e.message };
          }
        }
      } else if (['linkedin', 'facebook', 'instagram'].includes(platform)) {
        const scriptMap: Record<string, string> = {
          linkedin: 'mcp/linkedin-server/post_executor.js',
          facebook: 'mcp/facebook-server/src/post_executor.js',
          instagram: 'mcp/instagram-server/src/post_executor.js',
        };
        const script = path.join(ROOT_PATH, scriptMap[platform]);
        if (fs.existsSync(script)) {
          try {
            const tempFile = path.join(ROOT_PATH, `.temp_${platform}_api_content.txt`);
            fs.writeFileSync(tempFile, content, 'utf-8');
            await new Promise<void>((resolve, reject) => {
              exec(`node "${script}" "${tempFile}"`, { cwd: ROOT_PATH, timeout: 60000 }, (err, stdout) => {
                if (err) { reject(err); return; }
                postResult = { success: true, method: 'mcp_executor', output: stdout };
                resolve();
              });
            });
            if (fs.existsSync(tempFile)) fs.unlinkSync(tempFile);
          } catch (e: any) {
            postResult = { success: false, method: 'mcp_executor', error: e.message };
          }
        }
      }

      // If posted successfully, move to Done
      if (postResult.success && fs.existsSync(pendingPath)) {
        const donePath = path.join(DONE_DIR, filename);
        fs.renameSync(pendingPath, donePath);
      }

      // Log the action
      if (!fs.existsSync(LOGS_DIR)) fs.mkdirSync(LOGS_DIR, { recursive: true });
      const logFile = path.join(LOGS_DIR, `agent-${new Date().toISOString().slice(0, 10).replace(/-/g, '')}.log`);
      const logLine = `[${new Date().toISOString().slice(11, 19)}] POST platform=${platform} success=${postResult.success} method=${postResult.method}\n`;
      fs.appendFileSync(logFile, logLine, 'utf-8');

      res.json({
        data: {
          filename,
          platform,
          posted: postResult.success,
          method: postResult.method,
          savedTo: postResult.success ? 'Done' : 'Pending_Approval',
          error: postResult.error || null,
        },
      });
    } catch (error) {
      console.error('Error posting content:', error);
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to post content' } });
    }
  }

  /**
   * GET /api/v1/ai-agent/history
   * Returns post history from Done/ and Pending_Approval/.
   */
  async getHistory(req: Request, res: Response) {
    try {
      const limit = Math.min(Number(req.query.limit) || 50, 200);
      const platformFilter = req.query.platform as string;

      const posts: any[] = [];

      for (const [dir, status] of [[DONE_DIR, 'done'], [PENDING_DIR, 'pending']] as const) {
        if (!fs.existsSync(dir)) continue;
        const files = fs.readdirSync(dir).filter(f => f.endsWith('.md') && f.startsWith('social-post-'));
        for (const f of files) {
          try {
            const content = fs.readFileSync(path.join(dir, f), 'utf-8');
            const { metadata, body } = parseMarkdownFrontmatter(content);
            const platform = metadata.platform || f.split('-')[2] || 'unknown';

            if (platformFilter && platform !== platformFilter) continue;

            posts.push({
              filename: f,
              platform,
              status,
              created_at: metadata.created_at || metadata.posted_at || fs.statSync(path.join(dir, f)).mtime.toISOString(),
              source: metadata.source || 'unknown',
              content_preview: body.replace(/^## Content\s*\n*/, '').substring(0, 300),
            });
          } catch { /* skip */ }
        }
      }

      posts.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

      res.json({
        data: posts.slice(0, limit),
        meta: { total: posts.length, limit },
      });
    } catch (error) {
      console.error('Error fetching history:', error);
      res.status(500).json({ error: { code: 'INTERNAL_ERROR', message: 'Failed to fetch post history' } });
    }
  }
}

export const aiAgentController = new AiAgentController();
export default aiAgentController;
