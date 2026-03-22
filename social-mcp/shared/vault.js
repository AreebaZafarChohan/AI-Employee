/**
 * Vault integration — writes markdown files to Obsidian vault folders
 *
 * /Social/Queue   — drafts awaiting approval
 * /Social/Posted  — published posts log
 * /Social/Analytics — engagement summaries
 * /Social/Drafts  — generated content not yet queued
 */
import { writeFileSync, readFileSync, readdirSync, mkdirSync, existsSync, unlinkSync, renameSync } from 'node:fs';
import { join, basename } from 'node:path';

const VAULT = process.env.VAULT_PATH || join(process.cwd(), 'AI-Employee-Vault');
const SOCIAL = join(VAULT, 'Social');
const QUEUE = join(SOCIAL, 'Queue');
const POSTED = join(SOCIAL, 'Posted');
const ANALYTICS = join(SOCIAL, 'Analytics');
const DRAFTS = join(SOCIAL, 'Drafts');

for (const d of [QUEUE, POSTED, ANALYTICS, DRAFTS]) {
  mkdirSync(d, { recursive: true });
}

function ts() { return new Date().toISOString(); }
function slug(s) { return s.replace(/[^a-z0-9]+/gi, '-').toLowerCase().slice(0, 40); }
function fileTs() { return new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19); }

// ─────────────── Draft (awaiting approval) ───────────────

export function saveDraft(platform, content, meta = {}) {
  const id = `${platform}-draft-${fileTs()}`;
  const filename = `${id}.md`;
  const md = `---
id: "${id}"
platform: ${platform}
status: draft
created_at: "${ts()}"
requires_approval: true
${meta.scheduled_at ? `scheduled_at: "${meta.scheduled_at}"` : ''}
${meta.hashtags ? `hashtags: [${meta.hashtags.map(h => `"${h}"`).join(', ')}]` : ''}
---

# ${platform.charAt(0).toUpperCase() + platform.slice(1)} Draft

${content}

---
## Actions
- [ ] Approve and publish
- [ ] Edit content
- [ ] Reject
`;
  const path = join(DRAFTS, filename);
  writeFileSync(path, md, 'utf-8');
  return { id, path, filename };
}

// ─────────────── Queue (approved, ready to post) ───────────────

export function queuePost(platform, content, meta = {}) {
  const id = `${platform}-queued-${fileTs()}`;
  const filename = `${id}.md`;
  const md = `---
id: "${id}"
platform: ${platform}
status: queued
created_at: "${ts()}"
${meta.scheduled_at ? `scheduled_at: "${meta.scheduled_at}"` : ''}
${meta.link ? `link: "${meta.link}"` : ''}
${meta.media_url ? `media_url: "${meta.media_url}"` : ''}
---

# Queued: ${platform}

${content}
`;
  const path = join(QUEUE, filename);
  writeFileSync(path, md, 'utf-8');
  return { id, path, filename };
}

// ─────────────── Posted log ───────────────

export function logPosted(platform, content, result = {}) {
  const id = `${platform}-posted-${fileTs()}`;
  const filename = `${id}.md`;
  const md = `---
id: "${id}"
platform: ${platform}
status: posted
posted_at: "${ts()}"
post_id: "${result.post_id || result.tweet_id || 'N/A'}"
post_url: "${result.post_url || result.tweet_url || 'N/A'}"
---

# Posted: ${platform}

${content}

## Result
\`\`\`json
${JSON.stringify(result, null, 2)}
\`\`\`
`;
  const path = join(POSTED, filename);
  writeFileSync(path, md, 'utf-8');
  return { id, path, filename };
}

// ─────────────── Analytics ───────────────

export function saveAnalytics(platform, data) {
  const id = `${platform}-analytics-${fileTs()}`;
  const filename = `${id}.md`;
  const md = `---
id: "${id}"
platform: ${platform}
type: engagement_summary
generated_at: "${ts()}"
---

# ${platform.charAt(0).toUpperCase() + platform.slice(1)} Engagement Summary

Generated: ${new Date().toLocaleDateString()}

\`\`\`json
${JSON.stringify(data, null, 2)}
\`\`\`
`;
  const path = join(ANALYTICS, filename);
  writeFileSync(path, md, 'utf-8');
  return { id, path, filename };
}

// ─────────────── Read queue ───────────────

export function listQueue(platform = null) {
  try {
    const files = readdirSync(QUEUE).filter(f => f.endsWith('.md'));
    if (platform) return files.filter(f => f.startsWith(platform));
    return files;
  } catch { return []; }
}

export function listDrafts(platform = null) {
  try {
    const files = readdirSync(DRAFTS).filter(f => f.endsWith('.md'));
    if (platform) return files.filter(f => f.startsWith(platform));
    return files;
  } catch { return []; }
}

// ─────────────── Move draft → queue (approval) ───────────────

export function approveDraft(filename) {
  const src = join(DRAFTS, filename);
  if (!existsSync(src)) return null;
  const content = readFileSync(src, 'utf-8').replace('status: draft', 'status: queued');
  const dest = join(QUEUE, filename.replace('-draft-', '-queued-'));
  writeFileSync(dest, content, 'utf-8');
  unlinkSync(src);
  return dest;
}

// ─────────────── Move queue → posted ───────────────

export function markPosted(filename, result = {}) {
  const src = join(QUEUE, filename);
  if (!existsSync(src)) return null;
  let content = readFileSync(src, 'utf-8').replace('status: queued', 'status: posted');
  content += `\n## Post Result\n\`\`\`json\n${JSON.stringify(result, null, 2)}\n\`\`\`\n`;
  const dest = join(POSTED, filename.replace('-queued-', '-posted-'));
  writeFileSync(dest, content, 'utf-8');
  unlinkSync(src);
  return dest;
}

export const paths = { VAULT, SOCIAL, QUEUE, POSTED, ANALYTICS, DRAFTS };
