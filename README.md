# AI Employee - Platinum Tier (Complete)

> **Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop.**

A production-ready **Digital FTE (Full-Time Equivalent)** that works 24/7 — monitoring Gmail, WhatsApp, LinkedIn, managing finances via Odoo, posting on social media, and delivering Monday Morning CEO Briefings. Built with **Claude Code** as the reasoning engine and an **Obsidian-compatible vault** as the brain.

**Hackathon**: Personal AI Employee Hackathon 0 — Building Autonomous FTEs in 2026
**Tier**: Platinum (All Bronze + Silver + Gold + Platinum requirements completed)
**Developer**: [Areeba Zafar](https://github.com/AreebaZafarChohan)

---

## What This AI Employee Does

| Domain | What It Handles |
|--------|----------------|
| **Email** | Monitors Gmail, triages by risk, drafts replies, sends with approval |
| **WhatsApp** | Monitors all chats, captures messages, sends replies with approval |
| **LinkedIn** | Monitors DMs/mentions/comments, auto-posts sales content |
| **Social Media** | Posts to Facebook, Instagram, Twitter/X with scheduling |
| **Accounting** | Integrates with Odoo ERP for invoices, payments, financial reporting |
| **Business Audit** | Weekly audits + Monday CEO Briefings with revenue & bottleneck analysis |
| **Task Management** | Autonomous goal decomposition, multi-agent execution, progress tracking |
| **Cost Control** | Real-time AI token cost monitoring with budget auto-pause |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        AI EMPLOYEE ARCHITECTURE                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────── PERCEPTION LAYER (7 Watchers) ────────────────────┐  │
│  │  Gmail API ────→ gmail_watcher.py ────────┐                       │  │
│  │  LinkedIn ────→ linkedin_watcher.py ──────┤                       │  │
│  │  WhatsApp ────→ whatsapp_watcher.py ──────┤                       │  │
│  │  Odoo ERP ────→ odoo_watcher.py ──────────┼──→ /Needs_Action      │  │
│  │  Filesystem ──→ filesystem_watcher.py ────┤                       │  │
│  │  Social ──────→ social_watcher.py ────────┤                       │  │
│  │  File System ─→ file_system_watcher.py ───┘                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                        │                                │
│                                        ▼                                │
│  ┌──────────────── REASONING LAYER (Claude Code) ────────────────────┐  │
│  │  silver_process_engine ──→ Risk Scoring (0-100) + Classification  │  │
│  │                                                                    │  │
│  │      LOW (0-39)         MEDIUM (40-69)        HIGH (70-100)       │  │
│  │      auto-process       needs approval        needs approval      │  │
│  │          │                    │                     │              │  │
│  │          └──────── /Approved ←── Human Review ←────┘              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                        │                                │
│  ┌──────────────── MULTI-AGENT SYSTEM ───────────────────────────────┐  │
│  │  TaskAnalyzer → Planner → RiskAssessment → Memory → Supervisor   │  │
│  │  Ralph Wiggum Loop: PERCEIVE → REASON → DECIDE → ACT → FEEDBACK  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                        │                                │
│  ┌──────────────── ACTION LAYER (8 MCP Servers) ─────────────────────┐  │
│  │  Email:8081  LinkedIn:8082  WhatsApp:8083  Odoo:8084              │  │
│  │  Facebook:8085  Instagram:8086  Twitter:8087  Watcher:8088        │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                        │                                │
│  ┌──────────────── CONTROL CENTER (Next.js Dashboard) ───────────────┐  │
│  │  Dashboard │ Agents │ Goals │ Memory │ Costs │ Tools │ Intelligence│  │
│  │  Gmail │ LinkedIn │ WhatsApp │ Sales │ Watchers │ Approvals       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  ┌──────────────── OBSIDIAN VAULT (The Brain) ───────────────────────┐  │
│  │  /Inbox → /Needs_Action → /Plans → /Pending_Approval →           │  │
│  │  /Approved → /Done   (+) /Briefings /Logs /Audit /Accounting     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Tier Completion Status

### Bronze Tier (Foundation)
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] Working Gmail Watcher + File System Watcher
- [x] Claude Code reading from and writing to the vault
- [x] Folder structure: /Inbox, /Needs_Action, /Done
- [x] All AI functionality implemented as Agent Skills

### Silver Tier (Functional Assistant)
- [x] 3 Watchers: Gmail + WhatsApp + LinkedIn
- [x] Automatically posts on LinkedIn for sales generation
- [x] Claude reasoning loop that creates Plan.md files
- [x] MCP server for sending emails
- [x] Human-in-the-loop approval workflow for sensitive actions
- [x] Risk scoring engine (0-100) with confidence scoring
- [x] Daily briefing generator with 5-section format
- [x] All AI functionality as Agent Skills

### Gold Tier (Autonomous Employee)
- [x] Full cross-domain integration (Personal + Business)
- [x] Odoo Community accounting integration via MCP (JSON-RPC)
- [x] Facebook, Instagram, Twitter/X integration with posting
- [x] 8 MCP servers for different action types
- [x] Weekly Business and Accounting Audit with CEO Briefing
- [x] Error recovery with exponential backoff and graceful degradation
- [x] Comprehensive audit logging
- [x] Ralph Wiggum loop for autonomous multi-step task completion
- [x] All AI functionality as Agent Skills

### Platinum Tier (AI Workforce Control Center)
- [x] Agent Control Panel with real-time start/stop and status monitoring
- [x] Autonomous Goal Planning with decomposition into sub-tasks
- [x] Memory Explorer with vector similarity search
- [x] Cost Dashboard with per-agent/model attribution and budget auto-pause
- [x] Tool Execution Monitor with dynamic risk scoring
- [x] System Intelligence Dashboard (heatmap, timeline, queue health)
- [x] Self-Improvement Engine (failure analysis + optimization suggestions)
- [x] Real-time WebSocket updates with exponential backoff reconnection
- [x] Dark mode, skeleton loaders, responsive design
- [x] Full WhatsApp pipeline with auto-start watcher

---

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 20.x
- Gmail OAuth credentials (`credentials.json`)
- Obsidian (optional, for viewing vault)

### Installation

```bash
# 1. Clone
git clone https://github.com/AreebaZafarChohan/AI-Employee.git
cd AI-Employee

# 2. Python dependencies
pip install -r requirements.txt

# 3. Backend dependencies
cd backend && npm install && cd ..

# 4. Frontend dependencies
cd frontend && npm install && cd ..

# 5. MCP server dependencies (example: email)
cd mcp/email-server && npm install && cd ../..

# 6. Configure environment
cp .env.example .env
# Edit .env with your credentials (Gmail OAuth, Odoo, etc.)
```

### Start Everything

**Windows:**
```bash
start_all.bat
# or
python start_all.py start
```

**Linux/Mac:**
```bash
./start_all.sh
# or
python start_all.py start
```

**Modular start:**
```bash
python run.py orchestrator                # Vault orchestrator
python run.py watcher gmail --watch       # Gmail watcher
python run.py watcher linkedin --watch    # LinkedIn watcher
python run.py watcher whatsapp --watch    # WhatsApp watcher
python run.py all                         # Everything at once
```

### Access Points

| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| MCP Servers | Ports 8081-8088 |

---

## The 7 Watchers (Perception Layer)

| Watcher | Channel | Technology | What It Monitors |
|---------|---------|------------|-----------------|
| **Gmail Watcher** | Email | Google API | Unread important/starred emails |
| **LinkedIn Watcher** | Social | Playwright (headless) | DMs, mentions, comments, business keywords |
| **WhatsApp Watcher** | Messaging | Web automation | All unread messages from all chats |
| **Odoo Watcher** | Accounting | JSON-RPC | Invoices, payments, financial changes |
| **Filesystem Watcher** | Files | Watchdog | New files dropped in watch folder |
| **Social Watcher** | Social Media | APIs | Facebook, Instagram, Twitter activity |
| **File System Watcher** | Documents | Python | Local file system changes |

All watchers follow the `BaseWatcher` pattern: poll → detect → create `.md` file in `/Needs_Action` → Claude processes.

---

## 49 Agent Skills

All AI functionality is implemented as reusable Agent Skills (`.claude/skills/`), organized by domain:

| Category | Skills |
|----------|--------|
| **Foundation** (6) | Dashboard Writer, Needs Action Triage, Plan Generator, Task Lifecycle Manager, Vault State Manager, Company Handbook Enforcer |
| **Silver** (11) | Silver Process Engine, Silver Reasoning Engine, Orchestrator, Approval Workflow Enforcer, Daily Briefing Generator, LinkedIn Post Generator, LinkedIn Sales Post Engine, Monday CEO Briefing, Deadline Monitor, Status Report Generator, Task Priority Optimizer |
| **Gold** (6) | AI-Assisted Task Planner, Cross-Platform Notification Hub, Cross-Team Sync Manager, Dynamic Workflow Adaptor, Integrated AI Insights Generator, Multi-Service Orchestrator |
| **Platinum** (4) | Agent Claim Coordinator, Agent Delegation Manager, Audit Log Writer, Ralph Wiggum Loop Controller |
| **Communication** (2) | Email Drafter, Social Post Generator |
| **Finance** (2) | Invoice Generator, Transaction Classifier |
| **Vault** (5) | Needs Action Triage, Plan Generator, Process Needs Action, Task Lifecycle Manager, Vault State Manager |
| **Other** (13) | Approval Request Creator, Time Event Scheduler, Error Recovery Planner, CEO Briefing Writer, Audit Log Writer, Skill Standard Enforcer, etc. |

---

## 8 MCP Servers (Action Layer)

| Server | Port | Domain | Key Tools |
|--------|------|--------|-----------|
| **Email** | 8081 | Communication | `draft_email`, `send_email`, `list_emails`, `mark_read` |
| **LinkedIn** | 8082 | Social | `publish_post`, `schedule_post`, `get_profile`, `list_posts` |
| **WhatsApp** | 8083 | Messaging | `send_message`, `list_chats`, `get_messages` |
| **Odoo** | 8084 | Accounting | `create_invoice`, `list_invoices`, `record_payment`, `revenue_summary` |
| **Facebook** | 8085 | Social | `publish_post`, `schedule_post`, `get_feed` |
| **Instagram** | 8086 | Social | `publish_post`, `schedule_post`, `get_profile` |
| **Twitter** | 8087 | Social | `tweet`, `schedule_tweet`, `get_timeline`, `search_tweets` |
| **Watcher** | 8088 | System | `list_watchers`, `start_watcher`, `stop_watcher` |

---

## Frontend: AI Workforce Control Center (20+ Pages)

| Page | Description |
|------|-------------|
| `/dashboard` | Main hub — agent status, activity feed, quick stats, MCP health |
| `/agents` | Agent control panel — list, start/stop, real-time status |
| `/live-logs` | Real-time log streaming with severity filtering |
| `/goals` | Goal management — create, track, progress visualization |
| `/memory` | Memory explorer — vector similarity search, context inspection |
| `/costs` | Cost dashboard — usage trends, token breakdown, budget alerts |
| `/tools` | Tool execution monitor — risk scoring, input/output inspection |
| `/intelligence` | System intelligence — activity heatmap, timeline, queue health |
| `/gmail` | Gmail inbox with triage and response |
| `/linkedin` | LinkedIn posting and DM monitoring |
| `/whatsapp` | WhatsApp messages — real-time view, send with approval |
| `/sales` | Sales analytics and lead tracking |
| `/files` | File management |
| `/watchers` | Watcher configuration and control |
| `/plans` | Plan creation, versioning, approval workflow |
| `/needs-action` | Items requiring attention |
| `/ai-agent` | AI agent management |
| `/ai-employee` | Employee status overview |
| `/settings` | System configuration |

---

## Backend API (15 Route Groups)

| Route | Domain |
|-------|--------|
| `/api/agents` | Agent CRUD, start/stop, logs, status |
| `/api/tasks` | Task creation, tracking, completion |
| `/api/plans` | Plan generation, versioning, approval |
| `/api/approvals` | Review/approve/reject workflows |
| `/api/vault` | Vault file operations, DAG sync |
| `/api/system` | Heatmaps, queue health, timeline |
| `/api/audit` | Audit trail queries |
| `/api/whatsapp` | WhatsApp monitoring, sending, approval |
| `/api/linkedin` | LinkedIn posting, scheduling |
| `/api/watcher` | Watcher management |
| `/api/mcp` | MCP server status |
| `/api/files` | File CRUD operations |
| `/api/sales` | Sales analytics |
| `/api/activity` | Activity feed |

---

## Risk Scoring Engine

| Factor | Condition | Score Impact |
|--------|-----------|-------------|
| Financial > $100 | Amount detected | +50 |
| Unknown Sender | External domain | +25 |
| Urgent Keywords | urgent, asap, immediately | +25 |
| Risk Keywords | legal, payment, password | +30 |
| High Priority | `priority: high` | +30 |
| Internal File Drop | Known sender | -20 |

| Risk Level | Score | Action |
|-----------|-------|--------|
| **LOW** | 0-39 | Auto-process, no approval needed |
| **MEDIUM** | 40-69 | Requires human approval |
| **HIGH** | 70-100 | Requires approval + escalation |

---

## Human-in-the-Loop (HITL) Safety

The system **never** takes sensitive actions without approval:

1. Claude detects sensitive action needed
2. Creates approval file in `/Pending_Approval/`
3. Human reviews in Obsidian or Dashboard
4. Moves to `/Approved/` to execute, `/Rejected/` to deny
5. Orchestrator executes via MCP, logs everything, archives to `/Done/`
6. Approvals expire after 24 hours

**Permission Boundaries:**
| Action | Auto-Approve | Always Requires Approval |
|--------|-------------|-------------------------|
| Email replies | Known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs |
| File operations | Create, read | Delete, move outside vault |

---

## Monday Morning CEO Briefing

The flagship feature — autonomous business audit every week:

1. **Trigger**: Scheduled task runs weekly
2. **Process**: Reads Business_Goals.md, checks /Done for completed tasks, reviews accounting data
3. **Output**: Executive briefing with:
   - Revenue snapshot (this week vs target)
   - Completed tasks summary
   - Bottlenecks and delays
   - Proactive suggestions (cancel unused subscriptions, upcoming deadlines)
4. **Delivery**: Written to `/Briefings/YYYY-MM-DD_Monday_Briefing.md`

---

## Vault Structure (The Brain)

```
AI-Employee-Vault/
├── Inbox/                  # Raw incoming items
├── Needs_Action/           # Triaged items ready for processing
├── Plans/                  # Structured plans before execution
├── Pending_Approval/       # Items awaiting human review
├── Approved/               # Human-approved, ready for execution
├── Rejected/               # Rejected items with reasons
├── Done/                   # Completed and archived work
├── Briefings/              # CEO Briefings and daily reports
├── Logs/                   # Execution logs and audit trails
├── Reports/                # Marketing, Revenue, Productivity reports
├── Alerts/                 # System alerts
├── Audit/                  # Compliance audit records
├── Knowledge/              # Long-term AI memory
├── System_Health/          # System status and metrics
├── Social/                 # Social media drafts and posts
├── Business/               # Business operations
├── Accounting/             # Odoo-synced accounting records
├── Quarantine/             # Suspicious items
├── Company_Handbook.md     # Business rules and guidelines
└── Dashboard.md            # Real-time status dashboard
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript 5, shadcn/ui, TanStack Query v5, Framer Motion, Recharts, next-themes, WebSocket |
| **Backend (TS)** | Express.js, TypeScript, Prisma ORM, SQLite/PostgreSQL |
| **Backend (Python)** | FastAPI, Pydantic, Google APIs, Playwright, Watchdog, HTTPX |
| **MCP Servers** | Node.js, Express (8 servers on ports 8081-8088) |
| **Reasoning** | Claude Code (via Gemini API router) |
| **Memory/GUI** | Obsidian-compatible Markdown vault |
| **Process Mgmt** | PM2 / Python orchestrator with auto-restart |

---

## Project Structure

```
AI-Employee/
├── frontend/                     # Next.js Platinum Control Center
│   ├── src/app/                  # 20+ pages
│   ├── src/components/           # Reusable UI components
│   ├── src/hooks/                # 17 custom hooks
│   └── src/services/             # API clients
├── backend/                      # Express.js + Prisma API
│   ├── src/controllers/          # 15 controllers
│   ├── src/routes/               # 15 route files
│   └── src/services/             # 11 services
├── src/                          # Python Backend (FastAPI)
│   ├── orchestration/            # VaultOrchestrator, ApprovalOrchestrator
│   ├── agents/                   # AgentExecutor, PlanGenerator
│   ├── services/                 # 11 services
│   ├── watcher/                  # 7 watchers
│   ├── api/                      # FastAPI routes + WebSocket
│   ├── core/                     # Config, security, events
│   └── workers/                  # Background tasks
├── mcp/                          # 8 MCP Tool Servers
│   ├── email-server/
│   ├── linkedin-server/
│   ├── whatsapp-server/
│   ├── odoo-server/
│   ├── facebook-server/
│   ├── instagram-server/
│   ├── twitter-server/
│   └── watcher-server/
├── .claude/skills/               # 49 Agent Skills (16 categories)
├── AI-Employee-Vault/            # Obsidian-compatible Brain
├── specs/                        # Feature specs (all tiers)
│   ├── 001-platinum-tier-frontend/
│   ├── 001-platinum-tier-backend/
│   ├── 001-gold-tier-backend/
│   └── gold-tier/
└── history/prompts/              # 35 Prompt History Records
    ├── 001-platinum-tier-backend/ # 6 PHRs
    ├── 001-platinum-tier-frontend/# 8 PHRs
    └── general/                  # 21 PHRs
```

---

## Security

- **No hardcoded secrets** — All credentials in `.env` files (gitignored)
- **Dynamic risk scoring** — AI-powered assessment for every action
- **Human-in-the-loop** — Mandatory approval for medium/high-risk items
- **Cost guardrails** — Auto-pause on budget threshold breach
- **Full audit trail** — Every action logged with timestamps
- **Approval expiry** — 24-hour timeout on pending approvals
- **Dry run mode** — `DRY_RUN=true` tests without real execution
- **Rate limiting** — Max actions per hour to prevent runaway automation
- **Credential rotation** — Monthly rotation recommended

---

## Example End-to-End Flow

**Scenario**: Client sends WhatsApp message asking for invoice

1. **WhatsApp Watcher** detects message → creates `.md` in `/Needs_Action`
2. **Silver Process Engine** scores risk: HIGH (financial + external sender)
3. **Plan created** → `/Plans/PLAN_invoice_client.md` with steps
4. **Approval request** → `/Pending_Approval/` (requires human review)
5. **Human approves** → moves file to `/Approved/`
6. **Orchestrator executes** → Email MCP drafts and sends invoice
7. **Archived** → everything moves to `/Done/`
8. **Logged** → full audit trail in `/Logs/`
9. **Dashboard updated** → "Invoice sent to Client ($1,500)"

---

## Development History

This project was built incrementally through **35 documented prompt sessions** across 4 tiers:

| Phase | Sessions | Key Work |
|-------|----------|----------|
| Foundation + Bronze | 5 | Vault setup, basic watchers, folder structure |
| Silver | 8 | Gmail/LinkedIn/WhatsApp watchers, risk scoring, approval workflow |
| Gold | 12 | Odoo integration, social media, CEO briefings, Ralph loop, multi-agent |
| Platinum | 10 | Agent control, goals, memory, costs, tools, intelligence dashboard |

Full prompt history available in `history/prompts/`.

---

## License

MIT License

---

> **Digital FTE**: Works ~8,760 hours/year vs human's ~2,000. Cost per task: ~$0.50 vs ~$5.00. That's an 85-90% cost saving — the threshold where a CEO approves without further debate.
