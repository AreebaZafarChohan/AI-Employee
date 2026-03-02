# AI Employee - Silver Tier

**Personal AI Employee Silver Tier** - A sophisticated, local-first AI automation system with Gmail integration, MCP servers, approval workflows, and daily briefing generation.

---

## 🎯 Overview

The AI Employee Silver Tier is a comprehensive automation platform that:

- **Monitors Gmail** for important/starred emails
- **Monitors LinkedIn** for DMs, mentions, and comments (business keywords)
- **Processes items** through a structured workflow with risk assessment
- **Generates plans** with confidence scoring and approval routing
- **Executes actions** via MCP (Model Context Protocol) servers
- **Creates daily briefings** with executive summaries
- **Maintains full audit trails** in an Obsidian-compatible vault

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SILVER TIER ARCHITECTURE                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Gmail API ──→ gmail_watcher.py ──┐                             │
│                                   ├──→ /Needs_Action            │
│  LinkedIn ──→ linkedin_watcher.py ─┘                            │
│                                              │                  │
│                                              ↓                  │
│                                   silver_process_engine         │
│                                   - Type classification         │
│                                   - Risk scoring (0-100)        │
│                                   - Confidence (0-100%)         │
│                                              │                  │
│                    ┌─────────────────────────┼────────────┐    │
│                    │                         │            │    │
│                    ↓                         ↓            ↓    │
│              LOW risk                 MEDIUM/HIGH     /Logs    │
│              (auto-process)           risk          (audit)    │
│                    │                  │                       │
│                    │                  ↓                       │
│                    │         /Pending_Approval                │
│                    │                  │                       │
│                    │          (human approval)                │
│                    │                  │                       │
│                    │                  ↓                       │
│                    └────────── /Approved ◄─── human ──────────┤
│                                   │                           │
│                                   ↓                           │
│                            orchestrator                       │
│                            - MCP integration                  │
│                            - Email draft/send                 │
│                            - File operations                  │
│                                   │                           │
│                                   ↓                           │
│                              /Done (archive)                  │
│                                                                 │
│  daily_briefing_generator ──→ /Briefings/YYYY-MM-DD_Daily.md  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Vault Structure

```
AI-Employee-Vault/
├── Inbox/                 # Raw incoming items
├── Needs_Action/          # Items triaged and ready for processing
├── Plans/                 # Structured plans before execution
├── Pending_Approval/      # Medium/High risk items awaiting approval
├── Approved/              # Human-approved items ready for execution
├── Rejected/              # Rejected items with reasons
├── Done/                  # Completed and archived work
├── Briefings/             # Daily briefing reports
├── Logs/                  # Execution logs and audit trails
├── Reports/               # Generated reports and summaries
├── Social/                # Social media drafts (LinkedIn, etc.)
├── Company_Handbook.md    # Business rules and guidelines
└── Dashboard.md           # Real-time status dashboard
```

---

## 🚀 Key Features

### 1. Gmail Integration ✅
- **Watcher:** Polls Gmail for unread important/starred emails
- **Query:** `is:unread (is:important OR is:starred)`
- **Auto-classification:** Creates markdown files in `/Needs_Action`
- **MCP Server:** `send_email`, `draft_email`, `search_inbox` tools

### 2. LinkedIn Watcher ✅
- **Playwright-based:** Headless browser with persistent session
- **Monitors:** DMs, mentions, comments on posts
- **Business Keywords:** pricing, quote, service, partnership, etc.
- **Priority:** High for pricing/budget, Medium for others
- **Duplicate Prevention:** SHA256-based deduplication

### 3. Risk Scoring Engine ✅
- **Score:** 0-100 based on multiple factors
- **Confidence:** 0-100% based on available data
- **Factors:**
  - Financial amount > $100 → +50 (HIGH)
  - Unknown sender → +25 (MEDIUM)
  - Urgent keywords → +25 (MEDIUM)
  - Internal file drop → -20 (LOW)
  - High priority → +30
  - Risk keywords (legal, payment) → +30

### 3. Approval Workflow ✅
- **LOW risk:** Auto-process, no approval needed
- **MEDIUM/HIGH risk:** Requires human approval
- **Approval file:** Created in `/Pending_Approval`
- **Human action:** Move to `/Approved` to execute

### 4. Orchestrator ✅
- **Monitors:** `/Approved` folder
- **Validates:** Approval metadata, expiry (24h)
- **Executes:** MCP tools (email, file operations)
- **Logs:** All actions to `/Logs`
- **Archives:** Moves to `/Done` after execution

### 5. Daily Briefing Generator ✅
- **Reads:** Company goals, completed tasks, accounting data
- **Generates:** 5-section briefing
  - Executive Summary
  - Revenue Snapshot
  - Task Summary
  - Bottlenecks & Blockers
  - Suggestions & Next Steps
- **Updates:** Dashboard.md with briefing link
- **Schedule:** Daily at 8:00 AM (configurable)

### 6. Agent Skills ✅
- **silver_process_engine:** Core triage and planning
- **daily_briefing_generator:** Automated reporting
- **linkedin_post_generator:** Social media drafts
- **orchestrator:** Execution engine

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 20.x (for MCP servers)
- Gmail OAuth credentials
- Obsidian (optional, for viewing vault)

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
# Includes: google-api-python-client, pyyaml, watchdog, etc.
```

### 2. Install MCP Server Dependencies

```bash
cd mcp/email-server
npm install
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Gmail OAuth
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=your_refresh_token
GMAIL_USER=me

# Vault paths
VAULT_PATH=./AI-Employee-Vault

# Feature flags
DRY_RUN=false
LOG_LEVEL=INFO
```

### 4. Initialize Vault

```bash
python -m src.cli.main init --vault-path ./AI-Employee-Vault
```

---

## ⚙️ Configuration

### Gmail OAuth Setup

1. **Enable Gmail API** in Google Cloud Console
2. **Download OAuth credentials** → `credentials.json`
3. **Run OAuth flow:**
   ```bash
   python reauthorize_gmail.py
   ```
4. **Required scopes:**
   - `gmail.readonly`
   - `gmail.modify`
   - `gmail.send` (for sending)
   - `gmail.compose` (for drafts)

### MCP Email Server Setup

1. **Configure credentials:**
   ```bash
   cd mcp/email-server
   cp .env.example .env
   # Edit with your OAuth tokens
   ```

2. **Add to Claude Desktop config:**
   ```json
   {
     "mcpServers": {
       "ai-employee-email": {
         "command": "node",
         "args": ["path/to/mcp/email-server/src/index.js"],
         "env": {
           "GMAIL_CLIENT_ID": "...",
           "GMAIL_CLIENT_SECRET": "...",
           "GMAIL_REFRESH_TOKEN": "...",
           "DRY_RUN": "false"
         }
       }
     }
   }
   ```

3. **Windows:** Run `setup-windows.bat` for one-click setup

---

## 🎯 Quick Start

### 1. Start Gmail Watcher

```bash
# Single poll
python gmail_watcher.py

# Continuous monitoring
python gmail_watcher.py --watch

# Dry run (test)
DRY_RUN=true python gmail_watcher.py
```

### 2. Monitor LinkedIn (NEW)

```bash
# Install Playwright first
pip install playwright
playwright install chromium

# Single check
python linkedin_watcher.py

# Continuous monitoring (5 min intervals)
python linkedin_watcher.py --watch

# Custom interval (10 min)
python linkedin_watcher.py --watch --interval 600

# Test mode (no files created)
DRY_RUN=true python linkedin_watcher.py
```

### 3. Process Items (Silver Process Engine)

```bash
# Run once
python .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py

# Debug mode
SILVER_PE_LOG_LEVEL=DEBUG python ...

# Dry run
SILVER_PE_DRY_RUN=true python ...
```

### 4. Execute Approved Items (Orchestrator)

```bash
# Run one cycle
python orchestrator.py

# Watch mode (continuous)
python orchestrator.py --watch --interval 30

# Dry run
DRY_RUN=true python orchestrator.py
```

### 5. Generate Daily Briefing

```bash
# Generate briefing
python daily_briefing_generator.py

# Preview mode
python daily_briefing_generator.py --dry-run

# Debug mode
python daily_briefing_generator.py --debug
```

### 5. Schedule Daily Automation

**Windows (Task Scheduler):**
```powershell
# Run as Administrator
powershell.exe -ExecutionPolicy Bypass -File scripts\setup_scheduled_task.ps1
```

**macOS/Linux (cron):**
```bash
crontab -e
# Add: 0 8 * * * /path/to/scripts/daily_briefing.sh
```

---

## 🔧 CLI Commands

### Gmail Watcher
| Command | Description |
|---------|-------------|
| `python gmail_watcher.py` | Single poll cycle |
| `python gmail_watcher.py --watch` | Continuous monitoring |
| `DRY_RUN=true python ...` | Test without writing files |

### LinkedIn Watcher
| Command | Description |
|---------|-------------|
| `python linkedin_watcher.py` | Single LinkedIn check |
| `python linkedin_watcher.py --watch` | Continuous monitoring |
| `python linkedin_watcher.py --interval 600` | Custom interval (10 min) |
| `DRY_RUN=true python ...` | Test mode |

### Silver Process Engine
| Command | Description |
|---------|-------------|
| `python silver_process_engine.py` | Process Needs_Action items |
| `SILVER_PE_DRY_RUN=true ...` | Test mode |
| `SILVER_PE_LOG_LEVEL=DEBUG ...` | Verbose logging |

### Orchestrator
| Command | Description |
|---------|-------------|
| `python orchestrator.py` | Execute approved items |
| `python orchestrator.py --watch` | Continuous monitoring |
| `python orchestrator.py --interval 30` | Custom interval |

### Daily Briefing
| Command | Description |
|---------|-------------|
| `python daily_briefing_generator.py` | Generate daily briefing |
| `python ... --dry-run` | Preview without writing |
| `python ... --debug` | Debug mode |

### MCP Email Server
| Command | Description |
|---------|-------------|
| `cd mcp/email-server && npm start` | Start MCP server |
| `DRY_RUN=true node src/index.js` | Test mode |
| `.\setup-windows.bat` | Windows setup |

---

## 📊 Risk Scoring System

### Score Calculation

| Factor | Condition | Score Impact |
|--------|-----------|--------------|
| **Financial > $100** | Amount > $100 | +50 (HIGH) |
| **Financial > $0** | Any amount | +20 |
| **Unknown Sender** | External domain | +25 (MEDIUM) |
| **Known Sender** | Internal domain | +5 |
| **Urgent Keywords** | urgent, asap, immediately | +25 (MEDIUM) |
| **Risk Keywords** | legal, payment, password | +30 |
| **High Priority** | `priority: high` | +30 |
| **Medium Priority** | `priority: medium` | +20 |
| **Low Priority** | `priority: low` | +10 |
| **Internal File Drop** | file_drop + known sender | -20 |

### Base Scores by Type

| Type | Base Score |
|------|------------|
| email | +20 |
| file_drop | +30 |
| whatsapp | +25 |

### Risk Levels

| Score Range | Risk Level | Approval Required |
|-------------|------------|-------------------|
| 0-39 | **LOW** | No |
| 40-69 | **MEDIUM** | Yes |
| 70-100 | **HIGH** | Yes |

### Confidence Score

- **Base:** 60%
- **+10%** per factor (sender, priority, amount, content)
- **Maximum:** 100%

---

## 📝 Example Workflow

### Scenario: Invoice Request Email

1. **Email Received**
   ```
   From: Sarah Johnson <sarah@acmecorp.com>
   Subject: Invoice Request - Project Alpha
   Amount: $2,500
   Priority: high
   ```

2. **Gmail Watcher** → Creates file in `/Needs_Action`

3. **Silver Process Engine** → Assesses risk:
   ```
   Risk Score: 100/100 (HIGH)
   Confidence: 100%
   Factors: amount >$100 (+50), external sender (+25),
            high priority (+30), urgent keywords (+25),
            risk keywords (+30)
   ```

4. **Plan Created** → `/Plans/invoice-request-...-plan.md`

5. **Approval Requested** → `/Pending_Approval/...-approval.md`

6. **Human Approval** → Move to `/Approved/`

7. **Orchestrator Executes** → MCP `draft_email` tool

8. **Archived** → Moved to `/Done/`

9. **Logged** → Entry in `/Logs/orchestrator-*.log`

---

## 🧪 Testing

### Full Scenario Simulation

```bash
# 1. Create test email
# Create file in Needs_Action/ with test content

# 2. Run silver_process_engine
python .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py

# 3. Simulate approval (move to Approved/)

# 4. Run orchestrator
python orchestrator.py

# 5. Check logs
cat AI-Employee-Vault/Logs/*.log
```

### Unit Tests

```bash
# Test risk scoring
python test_risk_scoring.py

# Test daily briefing
python daily_briefing_generator.py --dry-run

# Test orchestrator
python orchestrator.py --dry-run
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| `SCHEDULING_GUIDE.md` | Cron/Task Scheduler setup |
| `CLAUDE.md` | Claude Code integration |
| `GEMINI.md` | Gemini API integration |
| `AGENTS.md` | Agent development guide |
| `.claude/skills/*/SKILL.md` | Individual skill specifications |

---

## 🔐 Security

- **No hardcoded secrets** — All credentials in `.env`
- **Approval gates** — High-risk items require human review
- **Audit trail** — All actions logged with timestamps
- **Dry run support** — Test without real execution
- **Expiry checks** — Approvals expire after 24 hours

---

## 🛠️ Troubleshooting

### Gmail Watcher Not Finding Emails

- Check OAuth scopes include `gmail.readonly` and `gmail.modify`
- Verify query: `is:unread (is:important OR is:starred)`
- Check `token.json` exists and is valid

### MCP Server Not Starting

- Run `npm install` in `mcp/email-server/`
- Check `.env` has all required variables
- Test with `DRY_RUN=true node src/index.js`

### Orchestrator Not Processing

- Ensure files are in `/Approved/` (not `/Pending_Approval/`)
- Check approval metadata (all required fields present)
- Verify approval not expired (< 24 hours old)

### Risk Scoring Incorrect

- Check `RISK_KEYWORDS` set in `silver_process_engine.py`
- Verify sender domain matching (internal vs external)
- Review amount extraction patterns

---

## 📄 License

MIT License

---

## 🎉 Status

**Silver Tier: PRODUCTION READY** ✅

All core features implemented and tested:
- ✅ Gmail integration
- ✅ Risk scoring with confidence
- ✅ Approval workflow
- ✅ Orchestrator with MCP
- ✅ Daily briefing generator
- ✅ Scheduling automation
- ✅ Full audit logging
