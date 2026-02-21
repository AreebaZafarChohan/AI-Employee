# AGENTS.md

## 1. Purpose of This Document

AGENTS.md is the canonical authority that defines the operational and behavioral boundaries of all AI agents in the Personal AI Employee Hackathon 0 system. This document governs:

- What each agent is permitted and forbidden to do
- How agents communicate via file-based protocols
- How human oversight is enforced through approval workflows
- How autonomy levels are graduated and enforced
- How failures are handled and escalated

Any agent operating in this system must respect these rules. Humans and AI agents alike use this document to verify compliance, audit behavior, and resolve disputes. Violations are considered system faults and must trigger immediate halt and review.

This document is a governance contract, not guidance. Every rule is enforceable and carries operational consequences.

---

## 2. Agent Taxonomy

| Agent | Codename | Description |
|-------|----------|-------------|
| **Local Executive Agent** | `lex` | Runs on local machine; orchestrates Watchers and coordinates with Cloud Executive. Has full access to vault and local environment. |
| **Cloud Executive Agent** | `cex` | Runs in Anthropic cloud; provides advanced reasoning for high-level planning. Cannot modify vault directly—communicates through lex. |
| **Gmail Watcher Agent** | `watcher-gmail` | Monitors Gmail inbox via Gmail API; writes new emails to vault; detects actionable items. |
| **WhatsApp Watcher Agent** | `watcher-whats` | Monitors WhatsApp messages via web API; writes messages to vault; detects requests. |
| **Finance Watcher Agent** | `watcher-finance` | Monitors bank transactions via Plaid/TrueLayer; writes transaction logs; detects anomalies. |
| **Filesystem Watcher Agent** | `watcher-fs` | Monitors configured directories for new files; copies metadata to vault; triggers processing. |
| **Orchestrator Agent** | `orch` | Assigns tasks to Action Agents; enforces idempotency and concurrency limits; manages claim queue. |
| **MCP Action Agents** | `mcp-email`, `mcp-browser`, `mcp-payment`, `mcp-social` | Execute specific actions via Model Context Protocol servers. Stateless; only act when invoked by orchestrator. |
| **Human Actor** | `human` | The human operator. Explicitly defined as an agent boundary. Only actor with irrevocable authority. Must be explicitly coded as a participant in workflows. |

---

## 3. Agent Ownership & Jurisdiction

### 3.1 Local Executive Agent (`lex`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Coordinate all local agents<br>- Read from vault<br>- Write to `/Plans/`, `/In_Progress/`, `/Pending_Approval/`<br>- Execute Python Watchers<br>- Forward approved actions to Orchestrator<br>- Enforce local autonomy limits |
| **Data Read Access** | - Full vault read access<br>- Local filesystem (monitored dirs)<br>- `.env` (read-only for MCP config) |
| **Data Write Access** | - Vault: `/Plans/*`, `/In_Progress/*`, `/Pending_Approval/*`, `/Logs/*`<br>- Vault: `/Updates/signals-from-lex.json` (append-only)<br>- **NEVER writes to `/Approved/`, `/Rejected/`, or `/Done/`** |
| **Can Trigger** | - Watcher agents (start/stop)<br>- MCP Action Agent requests (via Orchestrator, after approval)<br>- Ralph Wiggum loops (Silver tier and above) |
| **Must NEVER** | - Modify Dashboard.md directly<br>- Approve its own plans<br>- Write secrets to vault<br>- Execute irreversible cloud actions without explicit human approval<br>- Issue commands to cloud-based agents directly |

### 3.2 Cloud Executive Agent (`cex`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Strategic planning<br>- Complex reasoning for multi-step tasks<br>- Draft plans for lex<br>- Read vault (via lex proxy)<br>- Provide recommendations only |
| **Data Read Access** | - Vault contents proxied via lex (read-only snapshot)<br>- Cannot bypass lex to read vault directly |
| **Data Write Access** | - **NONE.** Cannot write to vault or any persistent store<br>- May send response messages to lex |
| **Can Trigger** | - Nothing directly. All outputs are advisory. |
| **Must NEVER** | - Execute any action<br>- Access local secrets or `.env`<br>- Modify files directly<br>- Perform network calls outside Anthropic APIs<br>- Request actions beyond lex's autonomy tier |

### 3.3 Gmail Watcher Agent (`watcher-gmail`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Poll Gmail inbox every 60s<br>- Write new emails to `/Needs_Action/emails/<timestamp>-<id>.json`<br>- Detect emails marked with `#ai-action` label<br>- Log errors to `/Logs/watcher-gmail.json` |
| **Data Read Access** | - Gmail API (OAuth2-scoped)<br>- `.env` for credentials path only |
| **Data Write Access** | - Vault: `/Needs_Action/emails/*`<br>- Vault: `/Logs/watcher-gmail.json` (append-only) |
| **Can Trigger** | - Nothing beyond writing to `/Needs_Action/` |
| **Must NEVER** | - Delete or modify emails<br>- Trigger actions based on content<br>- Retain credentials in memory beyond startup |

### 3.4 WhatsApp Watcher Agent (`watcher-whats`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Poll WhatsApp web interface every 30s<br>- Write new messages to `/Needs_Action/messages/<timestamp>-<id>.json`<br>- Detect messages with `@ai` mention<br>- Log errors to `/Logs/watcher-whats.json` |
| **Data Read Access** | - WhatsApp web API<br>- `.env` for session storage path |
| **Data Write Access** | - Vault: `/Needs_Action/messages/*`<br>- Vault: `/Logs/watcher-whats.json` (append-only) |
| **Can Trigger** | - Nothing beyond writing to `/Needs_Action/` |
| **Must NEVER** | - Send messages<br>- Mark messages as read<br>- Store conversation state in plaintext |

### 3.5 Finance Watcher Agent (`watcher-finance`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Poll Plaid/TrueLayer every 300s<br>- Write new transactions to `/Updates/finance/<date>.json`<br>- Detect anomalous amounts (thresholds in `.env`)<br>- Write alerts to `/Needs_Action/finance-alerts/<timestamp>.json` |
| **Data Read Access** | - Banking APIs (OAuth2)<br>- `.env` for provider config |
| **Data Write Access** | - Vault: `/Updates/finance/*`<br>- Vault: `/Needs_Action/finance-alerts/*`<br>- Vault: `/Logs/watcher-finance.json` (append-only) |
| **Can Trigger** | - Anomaly alerts to `/Needs_Action/` |
| **Must NEVER** | - Initiate transactions<br>- Modify account settings<br>- Cache credentials beyond runtime |

### 3.6 Filesystem Watcher Agent (`watcher-fs`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Monitor configured directories for new files<br>- Write metadata to `/Needs_Action/files/<timestamp>-<filename>.json`<br>- Detect files matching patterns in `.env` |
| **Data Read Access** | - Local filesystem (whitelisted dirs only)<br>- `.env` for watch patterns |
| **Data Write Access** | - Vault: `/Needs_Action/files/*`<br>- Vault: `/Logs/watcher-fs.json` (append-only) |
| **Can Trigger** | - Nothing beyond writing to `/Needs_Action/` |
| **Must NEVER** | - Read file contents (metadata only)<br>- Delete or move files<br>- Write outside vault |

### 3.7 Orchestrator Agent (`orch`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Execute MCP Action Agent commands<br>- Enforce idempotency via claim-by-move<br>- Prevent concurrent execution of conflicting actions<br>- Maintain action log in `/Logs/orchestrator.json` |
| **Data Read Access** | - `/Approved/` (read actions to execute)<br>- `/Logs/*` (read action history for idempotency checks) |
| **Data Write Access** | - **NONE.** Only moves files: `/Approved/` → `/In_Progress/` → `/Done/`<br>- Appends to `/Logs/orchestrator-actions.json` |
| **Can Trigger** | - MCP Action Agents via Model Context Protocol<br>- Writes completion status |
| **Must NEVER** | - Approve or reject plans<br>- Modify vault beyond file moves<br>- Execute actions without a valid claim token<br>- Skip idempotency checks |

### 3.8 MCP Action Agents (`mcp-email`, `mcp-browser`, `mcp-payment`, `mcp-social`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Execute one specific action per invocation<br>- Return success/failure status<br>- Maintain no state between invocations |
| **Data Read Access** | - Parameters passed from Orchestrator only<br>- Their respective APIs (Gmail, browser, Stripe, Twitter) |
| **Data Write Access** | - **NONE.** Return status only; Orchestrator writes results. |
| **Can Trigger** | - External API calls per their domain<br>- Cannot trigger other agents |
| **Must NEVER** | - Act without explicit Orchestrator invocation<br>- Access vault directly<br>- Persist data<br>- Retry failed actions (retry logic is lex's responsibility) |

### 3.9 Human Actor (`human`)

| Capability | Details |
|------------|---------|
| **Responsibilities** | - Move files between vault folders to signal approval/rejection<br>- Set autonomy tier in `.env`<br>- Review logs<br>- Override any agent decision |
| **Data Read Access** | - Full vault access<br>- `.env` file<br>- All logs |
| **Data Write Access** | - Vault: any folder (manual moves only)<br>- `.env` (autonomy settings, MCP config)<br>- Dashboard.md (human-maintained state) |
| **Can Trigger** | - All agent behavior by moving files<br>- Emergency halt by creating `/Pending_Approval/HALT` |
| **Must NEVER** | - Run agents without reviewing their plans (at Bronze/Silver tier)<br>- Delete logs<br>- Edit files in `/In_Progress/` while agent is active |

---

## 4. Vault-Based Communication Protocol

### 4.1 Canonical Folder Structure

```
vault/
├── Dashboard.md                  # Human-maintained status dashboard
├── .env                          # NEVER committed; local only
├── Needs_Action/                 # Inbox: raw inputs from watchers
│   ├── emails/
│   ├── messages/
│   ├── files/
│   └── finance-alerts/
├── Plans/                        # Draft plans created by lex or cex
│   └── <plan-id>.json            # Contains: goal, steps, autonomy tier, approval required
├── In_Progress/                  # Active work (single-writer per plan)
│   └── <plan-id>.json            # Lex writes progress; humans must not edit
├── Pending_Approval/             # Awaiting human review
│   ├── <plan-id>.json
│   └── <plan-id>.rejection.md    # Optional: human explains rejection
├── Approved/                     # Human moved plan here
│   └── <plan-id>.json            # Orchestrator claims files from here
├── Rejected/                     # Human moved plan here (archived)
│   └── <plan-id>.json
├── Done/                         # Completed work
│   └── <plan-id>.json            # Contains: outcome, log references
├── Updates/                      # Signals from watchers (non-actionable)
│   └── finance/
├── Logs/                         # Append-only audit trail
│   ├── watcher-gmail.json
│   ├── watcher-whats.json
│   ├── watcher-finance.json
│   ├── watcher-fs.json
│   ├── orchestrator-actions.json
│   └── lex-decisions.json
└── Archive/                      # Optional: old plans moved here
```

### 4.2 Claim-by-Move Rule

Agents claim work by moving files between folders. This is the ONLY coordination mechanism.

- **lex** moves: `Needs_Action/` → `Plans/` → `In_Progress/` → `Pending_Approval/`
- **human** moves: `Pending_Approval/` → `Approved/` or `Rejected/`
- **orch** moves: `Approved/` → `In_Progress/` → `Done/`
- **Watchers** move: external event → `Needs_Action/` (write only; never move)

### 4.3 Single-Writer Rules

At any moment, only ONE agent may write to a file:

- Files in `In_Progress/` are owned by lex (humans must not edit)
- Files in `Pending_Approval/` are read-only to all (humans move only)
- Files in `Approved/` are read-only to all (orch moves only)
- Files in `Logs/` are append-only

Violations: if two agents attempt to write simultaneously, the first writer wins; the second must halt and retry with fresh state.

### 4.4 Conflict Avoidance

Lex must check for existing files before creating new plans:

- If `Plans/<plan-id>.json` exists, do not overwrite; increment ID
- If `In_Progress/` has active plans, serialize work (no parallel plans at Bronze/Silver tier)
- For Gold/Platinum tier, lex may maintain up to 3 parallel plans if they have no resource conflicts

### 4.5 Idempotency Expectations

All actions must be idempotent:

- Watchers: use email/msg/file IDs to avoid duplicate writes
- Lex: regenerate plans from `Needs_Action/` on restart; do not duplicate existing plans
- Orchestrator: check `/Logs/orchestrator-actions.json` before executing; if action ID exists, skip execution and mark as duplicate
- MCP agents: action parameters must include idempotency keys; external APIs must support idempotency

---

## 5. Human-in-the-Loop Enforcement Rules

### 5.1 What Requires Approval

| Autonomy Tier | Requires Approval |
|---------------|-------------------|
| **Bronze** | All plans and actions |
| **Silver** | Plans only; actions within approved plans are auto-executed |
| **Gold** | Plans that involve financial transactions, message sending, or external commitments; informational actions are auto-approved |
| **Platinum** | Cloud Executive agent must gain explicit approval for any irreversible action; local agent operates autonomously within budget |

Explicit approval is ALWAYS required for:

- Financial transactions >$10
- Sending emails/messages to external parties
- Deleting data
- Modifying system configuration
- Actions that could affect reputation or legal standing

### 5.2 How Approval is Requested

When lex moves a plan to `Pending_Approval/`, it must include:

```json
{
  "plan_id": "plan-2026-01-29-001",
  "goal": "Respond to client inquiry about project timeline",
  "steps": [...],
  "risk_level": "low",
  "autonomy_tier": "silver",
  "requires_approval": true,
  "approval_scope": "Send email to client@example.com",
  "estimated_time_minutes": 5,
  "reversible": true
}
```

### 5.3 What Constitutes Approval

Humans approve by:

- Moving the plan file from `Pending_Approval/` to `Approved/`
- Optionally: add `Approved/` → `plan-id.human-note.md` with constraints

Approval is implicit for informational gathering actions at Gold tier and above.

### 5.4 What Happens on Rejection

If human moves plan to `Rejected/`:

- Lex must halt any related Ralph Wiggum loop immediately
- Lex must append explanation from `*.rejection.md` to `/Logs/lex-decisions.json`
- Lex must not retry the same plan without modification
- If pattern of rejections occurs (>3 similar), lex must escalate to human via Dashboard.md

### 5.5 Expiry Rules

- Plans in `Pending_Approval/` expire after 48 hours
- On expiry, lex moves them to `Rejected/` and appends "EXPIRED" reason
- Financial transactions in `Approved/` but not executed within 24 hours require re-approval

### 5.6 Escalation Rules

Lex must escalate to human (write urgent entry to Dashboard.md) if:

- Approval is pending for >24 hours on time-sensitive task
- Multiple rejections of similar plans (>3)
- Unhandled exception during execution
- Ralph Wiggum loop exceeds iteration limit
- MCP agent returns auth error or quota exceeded

---

## 6. Autonomy Levels

### 6.1 Bronze (Default, Training Mode)

**Allowed:**
- Create draft plans only
- Move plans to `Pending_Approval/`
- Execute informational queries (not actions)

**Must Remain Manual:**
- All approvals required for every action
- Human reviews every MCP call before execution
- No Ralph Wiggum loops

**Authority:**
- Lex only; Cloud Executive disabled

### 6.2 Silver

**Allowed:**
- Auto-execute actions within approved plans
- Ralph Wiggum loops up to 5 iterations
- Retry failed actions 2 times before escalating

**Must Remain Manual:**
- Plan approval required
- Financial transactions require explicit approval (regardless of amount)
- External messages require explicit approval

**Authority:**
- Lex; Cloud Executive provides advisory only

### 6.3 Gold

**Allowed:**
- Auto-approve informational actions (no side effects)
- Ralph Wiggum loops up to 15 iterations
- Retry failed actions 3 times with exponential backoff
- Maintain up to 3 parallel plans if no resource conflicts
- Auto-send pre-approved message templates (e.g., "Received, will review")

**Must Remain Manual:**
- Financial transactions >$10
- New message templates
- Plan modifications that increase risk level

**Authority:**
- Lex makes decisions; Cloud Executive can recommend plan modifications

### 6.4 Platinum

**Allowed:**
- Auto-approve any reversible action
- Ralph Wiggum loops up to 50 iterations
- Retry failed actions 5 times
- Maintain up to 10 parallel plans
- Cloud Executive can create and approve plans for lex execution
- Cloud Executive may delegate approval authority to Local Executive for specific plan categories
- Cloud Executive may monitor vault contents (via lex proxy) for strategic opportunities
- Cloud Executive may initiate Ralph Wiggum loops for strategic exploration

**Must Remain Manual:**
- Financial transactions >$100
- Irreversible actions (deletions, contract acceptances)
- Changes to autonomy tier or security config
- Granting Cloud Executive plan creation authority (human must explicitly enable in `.env`)
- Granting Cloud Executive approval delegation authority

**Authority Split:**
- **Local (lex):** Execute plans, manage Watchers, enforce safety, validate cloud-sourced plans before execution
- **Cloud (cex):** Strategic planning, plan creation and approval (lex acts as executor), may approve plans up to delegated limits
- **Human:** Override any decision; retain final authority; defines delegation boundaries

**Cloud-Local Coordination Protocol:**
- Cloud Executive communicates plans to Local Executive via Anthropic API messages
- Local Executive must validate all cloud-sourced plans against local safety rules
- Plans from Cloud Executive must include `source: "cloud"` field
- Cloud Executive may only approve actions within its delegated authority scope
- Any plan exceeding delegation scope requires human approval
- Local Executive logs all cloud-sourced plan executions with source attribution

---

## 7. Ralph Wiggum Loop Governance

### 7.1 Which Agents May Use Ralph Loops

Only **lex** may initiate and manage Ralph Wiggum loops. Orchestrator may execute iterative MCP calls within a single plan, but must not create new plans or self-direct.

### 7.2 Maximum Iteration Limits

- **Bronze:** 0 (loops disabled)
- **Silver:** 5 iterations
- **Gold:** 15 iterations
- **Platinum:** 50 iterations

### 7.3 Completion Criteria

A loop must terminate when:

1. Success condition met (defined in plan)
2. Maximum iterations reached
3. Human moves plan to `Rejected/`
4. Lex detects error condition requiring escalation
5. Any MCP call returns auth error or rate limit exceeded

### 7.4 Loop Termination Requirements

On termination, lex must:

- Write outcome to `/Logs/lex-decisions.json`
- If incomplete, move plan to `Pending_Approval/` with explanation
- If complete, move to `Done/` (if auto-approved) or `Pending_Approval/` (if requiring final sign-off)

### 7.5 Escalation to Human

Lex must escalate if:

- Loop completes without success and no alternative path exists
- Loop iterations consistently fail at the same step (>3 consecutive failures)
- Loop detects conflict with human-created Dashboard.md entry
- Human creates `/Pending_Approval/HALT` file (emergency stop)

---

## 8. Security & Trust Boundaries

### 8.1 Secret Handling Rules

- Secrets (API keys, OAuth tokens, passwords) live ONLY in `.env` file
- `.env` is NEVER committed to git; never written to vault
- Lex reads `.env` at startup only; does not log values
- MCP agents receive secrets via environment variables, never via parameters
- Vault must never contain: tokens, keys, credentials, PII beyond email addresses

### 8.2 What Never Syncs to Cloud

The following data never leaves local machine:

- `.env` file contents
- Vault contents (unless explicitly approved by human)
- Local filesystem paths
- Financial account numbers
- Personal contact information
- Any secret or credential
- Local network topology
- Host machine identification data

**Cloud Executive Data Access Protocol:**
- Cloud Executive may only receive sanitized, anonymized summaries from Local Executive
- Data sent to Cloud Executive must be explicitly approved in `.env` configuration
- Sensitive data fields must be redacted or hashed before transmission
- Transmission logs must record what data was shared with Cloud Executive

### 8.3 Env vs Vault Data Separation

| Data Type | Location | Rationale |
|-----------|----------|-----------|
| Credentials | `.env` | Local only; never logged |
| Configuration | `.env` | Keys, endpoints, thresholds |
| MCP Server Paths | `.env` | Local execution context |
| Work Products | Vault | Reviewable, auditable, human-readable |
| Logs | Vault | Audit trail; can be inspected |
| Dashboard State | Vault: Dashboard.md | Human-maintained canonical state |
| Agent Instructions | This file (AGENTS.md) | Operational contract; not config |

### 8.4 Audit Log Requirements

Every agent must append to its log file on every significant action:

```json
{
  "timestamp": "2026-01-29T14:30:00Z",
  "agent": "lex",
  "action": "move",
  "source": "Plans/plan-001.json",
  "destination": "In_Progress/plan-001.json",
  "reason": "human_approved"
}
```

Logs are append-only. Agents must not modify or delete log entries.

### 8.5 Blast-Radius Containment

- **Financial:** Maximum transaction limit in `.env`; lex cannot exceed it
- **Messaging:** Recipient whitelist in `.env`; lex cannot send to unlisted addresses
- **Filesystem:** Watchers monitor only whitelisted directories
- **API Calls:** MCP servers enforce rate limits and quotas
- **Cloud:** cex cannot trigger local actions; only advises

---

## 9. Failure Modes & Agent Behavior on Error

### 9.1 Retry Rules

| Failure Type | Bronze/Silver | Gold | Platinum |
|--------------|---------------|------|----------|
| Network timeout | Retry 1x after 30s | Retry 2x with exponential backoff | Retry 3x with exponential backoff |
| API rate limit | Wait 60s, retry 1x | Wait 60s, retry 2x | Wait 60s, retry 3x |
| Auth error | Escalate immediately | Escalate immediately | Escalate immediately |
| MCP server down | Escalate after 1 retry | Escalate after 2 retries | Escalate after 3 retries |

### 9.2 Pause Conditions

Lex must pause all activity if:

- `.env` file is missing or malformed
- Vault path is not accessible
- Any log file cannot be written (disk full, permissions)
- MCP server fails health check on startup

### 9.3 Human Alert Thresholds

Lex must write urgent entry to Dashboard.md if:

- >5 consecutive failures of same type
- Financial transaction fails after retries
- Auth error for any service
- Ralph loop exceeds iteration limit without success
- Disk usage >90%

### 9.4 Graceful Degradation

If cloud services unavailable:

- **Bronze/Silver:** Continue with local Watchers only; queue cloud-dependent actions
- **Gold/Platinum:** Attempt fallback strategies (e.g., local models for reasoning); log degraded mode

If vault unavailable:

- All agents halt; lex writes emergency log to local filesystem; human must intervene

---

## 10. Explicit Anti-Patterns (MANDATORY)

The following actions are **FORBIDDEN** for all agents, regardless of tier:

1. **Acting Without Approval:** No agent may execute an action requiring approval that has not been explicitly granted via file move.

2. **Writing Secrets to Vault:** Never write API keys, tokens, passwords, or credentials to any vault file.

3. **Editing Dashboard.md Without Authority:** Only human may edit Dashboard.md. Lex may read it but never write.

4. **Acting on Ambiguous Intent:** If plan goal is unclear, agents must escalate; never guess human intent.

5. **Cloud Agent Performing Irreversible Actions:** `cex` cannot and must not trigger any irreversible action.

6. **Bypassing Orchestrator:** Lex must not call MCP agents directly; all actions must flow through Orchestrator for audit.

7. **Cross-Agent File Access:** Agents must only read/write files in their designated folders (see Section 3).

8. **Deleting Logs:** Logs are append-only; no agent may delete, modify, or truncate log files.

9. **Self-Modifying Autonomy:** Agents cannot change their autonomy tier or `.env` settings.

10. **Ignoring Expiry:** Agents must respect approval expiry times; cannot execute expired approvals.

11. **Concurrent Plan Execution at Bronze/Silver:** Lex must not execute multiple plans in parallel at Bronze/Silver tiers.

12. **Silent Failures:** All failures must be logged and escalated per Section 9; never fail silently.

13. **Vault Path Traversal:** Agents must not use `..` or absolute paths to access folders outside their jurisdiction.

14. **Storing PII in Plaintext:** Vault may contain email addresses; never store SSNs, credit card numbers, or passwords.

15. **Cloud Sync of Vault Without Explicit Approval:** Lex must not sync vault contents to cloud storage unless human explicitly enables this feature.

---

## 11. Final Authority Rule

### 11.1 Who Has Final Authority

The **Human Actor** (`human`) has absolute and irrevocable final authority over:

- All agent decisions
- Plan approvals and rejections
- Autonomy tier settings
- Security configuration
- System halt/resume
- Data retention and deletion
- Interpretation of this document

### 11.2 How Disputes Are Resolved

If agents disagree (e.g., lex and cex propose conflicting plans):

- Lex's assessment prevails for local execution
- Human review is automatically triggered (plan moved to `Pending_Approval/`)
- Human decides which approach to approve or rejects both

### 11.3 How Humans Override Agents

Humans can override agents at any time by:

- Moving any file from any folder to any other folder (including emergency halt)
- Creating `/Pending_Approval/HALT` (immediate system stop)
- Modifying `.env` to change autonomy tier
- Editing Dashboard.md with explicit instructions

Upon detecting override, lex must:

- Immediately halt current activity
- Read new instructions from Dashboard.md
- Adjust behavior accordingly
- Log override event to `/Logs/lex-decisions.json`

### 11.4 Humans Are Always Accountable

The human operator is ultimately accountable for:

- All agent actions (even auto-approved ones)
- System security and configuration
- Third-party service credentials
- Compliance with laws and regulations
- Data privacy and handling

**No agent bears legal or ethical responsibility. Agents are tools; responsibility rests entirely with the human operator.**

---

## 12. Governance and Evolution

### 12.1 Modification of AGENTS.md

This document can only be modified by the **Human Actor** through the following process:

1. Create a proposed change in `/Pending_Approval/agents-change.md`
2. Review changes for security and system integrity implications
3. Test changes in Bronze mode before applying
4. Update version and effective date
5. Announce change via Dashboard.md with migration instructions

### 12.2 Version Control

- **Current Version:** 1.0.0
- **Effective Date:** 2026-01-29
- **Last Modified:** 2026-01-29

### 12.3 Compliance Verification

Agents must verify compliance with this document at startup by:
- Lex: Checking existence and validity of required vault folders
- Orchestrator: Validating claim-by-move protocol integrity
- Human: Reviewing logs for any violations weekly

Violations must be logged, reported to Dashboard.md, and trigger immediate system halt until human intervention.
