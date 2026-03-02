# LinkedIn Watcher - Silver Tier

Automated LinkedIn monitoring for business-related DMs, mentions, and comments using Playwright.

## Features

- ✅ **Persistent Session Login** - Uses browser context storage for seamless re-authentication
- ✅ **Multi-Source Monitoring** - DMs, mentions, and comments
- ✅ **Business Keyword Filtering** - Only triggers on relevant business messages
- ✅ **Duplicate Prevention** - SHA256-based deduplication
- ✅ **Retry Logic** - Automatic retries with exponential backoff
- ✅ **DRY_RUN Mode** - Test without creating files
- ✅ **Comprehensive Logging** - JSON logs with event tracking

## Installation

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Or let the script auto-install
python linkedin_watcher.py --help
```

## Configuration

### 1. Create .env file

```bash
cp .env.example .env
```

### 2. Add LinkedIn credentials

```env
# LinkedIn Credentials
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password

# Vault path
VAULT_PATH=./AI-Employee-Vault

# Optional settings
DRY_RUN=false
LOG_LEVEL=INFO
LINKEDIN_WATCH_INTERVAL=300
```

## Usage

### Single Check

```bash
# Run once
python linkedin_watcher.py

# Test mode (no files created)
DRY_RUN=true python linkedin_watcher.py

# Debug logging
LOG_LEVEL=DEBUG python linkedin_watcher.py
```

### Continuous Monitoring

```bash
# Watch mode (default: 5 minute intervals)
python linkedin_watcher.py --watch

# Custom interval (every 10 minutes)
python linkedin_watcher.py --watch --interval 600

# Watch mode with debug logging
LOG_LEVEL=DEBUG python linkedin_watcher.py --watch --interval 300
```

## Business Keywords

The watcher triggers on messages containing these keywords:

| Category | Keywords |
|----------|----------|
| **Pricing** | pricing, price, quote, quotation |
| **Services** | service, services, solution, solutions |
| **Partnerships** | collaboration, collaborate, partner, partnership |
| **Projects** | project, opportunity, proposal, contract |
| **Financial** | budget, investment, deal, agreement |
| **Work** | consulting, freelance, hire, hiring |
| **Meetings** | meeting, call, demo, presentation |
| **Interest** | interested, connect, discussion, explore |

## Output Format

Files created in `/Needs_Action/`:

```markdown
---
type: linkedin_dm
from: "John Doe"
content: "Hi, I'm interested in your services. Can you share pricing?"
thread_url: https://www.linkedin.com/messaging/thread/123456
priority: high
status: pending
linkedin_item_id: a1b2c3d4e5f6
received_at: "2026-02-25T10:00:00Z"
created_at: "2026-02-25T10:05:00Z"
---

# LinkedIn DM

**From:** John Doe
**Received:** 2026-02-25T10:00:00Z
**Priority:** high
**Thread:** [linkedin.com/messaging/thread/123456](...)

## Message Content

Hi, I'm interested in your services. Can you share pricing?

## Actions Required

- [ ] Review message content
- [ ] Determine required response
- [ ] Draft and send response
- [ ] Mark complete when done
```

## Priority Levels

| Priority | Trigger |
|----------|---------|
| **high** | Contains "pricing", "quote", or "budget" |
| **medium** | Other business keywords |

## Duplicate Prevention

- Uses SHA256 hash of `sender:message:timestamp`
- Stores processed IDs in `Logs/linkedin_processed.json`
- Keeps last 1000 IDs to prevent unbounded growth
- Automatically skips duplicates

## Retry Logic

- **Max retries:** 3 attempts
- **Delay between retries:** 5 seconds
- **Logs:** All retry attempts tracked

## Logging

### Daily Log File

Location: `Logs/linkedin-watcher-YYYY-MM-DD.log`

### Log Events

| Event | Description |
|-------|-------------|
| `login` | Login attempt (success/failed/error) |
| `check_dms` | DM check results |
| `check_mentions` | Mention check results |
| `check_comments` | Comment check results |
| `file_created` | New file created in Needs_Action |
| `retry_exhausted` | All retry attempts failed |
| `check_failed` | Full check failed |

### Example Log Entry

```json
{
  "timestamp": "2026-02-25T10:05:00Z",
  "event_type": "file_created",
  "dry_run": false,
  "filename": "linkedin-linkedin_dm-john-doe-a1b2c3d4.md",
  "item_id": "a1b2c3d4e5f6",
  "sender": "John Doe",
  "type": "linkedin_dm"
}
```

## Session Management

### Persistent Session Location

Sessions stored in: `.linkedin_sessions/`

### Benefits

- No need to re-enter credentials each time
- Faster login (uses existing cookies)
- Reduces login challenges from LinkedIn

### Clear Session (if needed)

```bash
# Delete session data
rm -rf .linkedin_sessions/

# Next run will re-authenticate
python linkedin_watcher.py
```

## Troubleshooting

### Login Fails

1. **Check credentials:**
   ```bash
   echo $LINKEDIN_EMAIL
   echo $LINKEDIN_PASSWORD
   ```

2. **Verify account access:**
   - Try logging in manually at linkedin.com
   - Check for 2FA requirements

3. **Clear session:**
   ```bash
   rm -rf .linkedin_sessions/
   python linkedin_watcher.py
   ```

### No Items Found

1. **Check LinkedIn activity:**
   - Verify you have unread DMs/notifications
   - Check if messages contain business keywords

2. **Increase debug logging:**
   ```bash
   LOG_LEVEL=DEBUG python linkedin_watcher.py
   ```

3. **Check selectors:**
   - LinkedIn may update CSS classes
   - Check logs for selector errors

### Playwright Installation Issues

```bash
# Reinstall Playwright
pip uninstall playwright
pip install playwright
playwright install chromium

# Or use system browsers
# Set environment variable before running
export PLAYWRIGHT_BROWSERS_PATH=0
```

### Rate Limiting

If LinkedIn rate limits:

1. **Increase interval:**
   ```bash
   python linkedin_watcher.py --watch --interval 600
   ```

2. **Reduce check scope:**
   - Modify `check_dms()` to check fewer conversations
   - Change `conversations[:10]` to `conversations[:5]`

## Integration

### With Silver Process Engine

Files created in `/Needs_Action/` are automatically processed by:

```bash
python .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py
```

### With Orchestrator

After human approval, orchestrator can execute responses:

```bash
python orchestrator.py
```

### With Daily Briefing

LinkedIn items included in daily briefing:

```bash
python daily_briefing_generator.py
```

## Security

- **Credentials:** Store in `.env` (never commit)
- **Session data:** Stored locally in `.linkedin_sessions/`
- **No external logging:** All logs stay local
- **DRY_RUN mode:** Test without side effects

## Best Practices

1. **Start with DRY_RUN:**
   ```bash
   DRY_RUN=true python linkedin_watcher.py
   ```

2. **Use watch mode sparingly:**
   - 5-minute intervals recommended
   - Avoid aggressive polling (< 60 seconds)

3. **Monitor logs:**
   ```bash
   tail -f Logs/linkedin-watcher-*.log
   ```

4. **Review before responding:**
   - All items go to `/Needs_Action/`
   - Human review required before sending responses

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LINKEDIN_EMAIL` | (required) | LinkedIn email/username |
| `LINKEDIN_PASSWORD` | (required) | LinkedIn password |
| `VAULT_PATH` | `./AI-Employee-Vault` | Path to vault |
| `DRY_RUN` | `false` | Test mode |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `LINKEDIN_WATCH_INTERVAL` | `300` | Watch interval (seconds) |

## Files Created

| File | Purpose |
|------|---------|
| `linkedin_watcher.py` | Main watcher script |
| `.linkedin_sessions/` | Browser session data |
| `Logs/linkedin-watcher-*.log` | Daily logs |
| `Logs/linkedin_processed.json` | Processed item IDs |
| `Needs_Action/linkedin-*.md` | Created items |

## Status

**Production Ready** ✅

All features implemented and tested.
