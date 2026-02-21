# Agent Delegation Manager

Coordinate Local ↔ Cloud task ownership, approval sync, and vault sync flags.

## Overview

The Agent Delegation Manager enables seamless coordination between Local Executive Agent (lex) and Cloud Executive Agent (cex) for the Digital FTE workflow. It manages task delegation, ownership transfers, approval synchronization, and vault sync state while enforcing security boundaries to ensure sensitive data stays local.

## Key Features

- **Signal-Based Async Coordination**: Uses signal files for message passing between local and cloud agents
- **Security Boundaries**: Enforces `local_only` sync policy to prevent secrets from leaving local environment
- **Claim-by-Move Semantics**: Atomic file operations prevent race conditions
- **Timeout & Cleanup**: Automatic cleanup of orphaned signals
- **Approval Sync**: Synchronizes human approval decisions from cloud to local vault
- **Info Request Protocol**: Safe information sharing without leaking secrets

## Quick Start

### 1. Install

Copy the skill to your `.claude/skills/` directory:

```bash
cp -r agent_delegation_manager ~/.claude/skills/coordination/
```

### 2. Configure

Create a `.env` file in your project root:

```bash
cp .claude/skills/coordination/agent_delegation_manager/assets/.env.example .env
```

Edit `.env` and set:

```bash
VAULT_PATH_LOCAL="/path/to/your/local/vault"
VAULT_PATH_CLOUD="/path/to/your/cloud/vault"
SIGNALS_DIR_LOCAL="${VAULT_PATH_LOCAL}/.signals"
SIGNALS_DIR_CLOUD="${VAULT_PATH_CLOUD}/.signals"
```

### 3. Create Signal Directories

```bash
mkdir -p "$VAULT_PATH_LOCAL/.signals"
mkdir -p "$VAULT_PATH_CLOUD/.signals"
```

### 4. Verify Setup

```bash
# Check configuration
cat .env | grep -E "(VAULT_PATH|SIGNALS_DIR)"

# Verify directories exist
ls -la "$VAULT_PATH_LOCAL"
ls -la "$VAULT_PATH_CLOUD"
ls -la "$VAULT_PATH_LOCAL/.signals"
ls -la "$VAULT_PATH_CLOUD/.signals"
```

## Usage

### Delegate Task to Cloud

```javascript
// lex delegates task planning to cex
const taskId = "task-20250115-103000";
const signal = await delegateTaskToCloud(taskId, {
  action: "plan_task",
  context: {
    user_request: "Build email notification service",
    constraints: ["Must use SendGrid API", "Deploy to AWS Lambda"]
  }
});

console.log(`Delegation signal created: ${signal.signal_path}`);
```

### Receive Cloud Response

```javascript
// lex polls for cex response
const response = await waitForDelegationResponse(taskId, 30000); // 30 second timeout

if (response.status === "completed") {
  console.log(`Plan ready: ${response.plan_path}`);
  const plan = await readFile(response.plan_path);
  // Proceed with execution
} else if (response.status === "needs_info") {
  // Handle info request
  await handleInfoRequest(response.info_request);
}
```

### Sync Approval State

```javascript
// lex syncs approval decision from cloud vault
const approvalSignal = await readApprovalSignal(taskId);

if (approvalSignal.approval.decision === "approved") {
  await moveFile(
    `Pending_Approval/${taskId}.json`,
    `Approved/${taskId}.json`
  );
  console.log(`Task approved by ${approvalSignal.approval.approved_by}`);
}
```

### Handle Info Request

```javascript
// cex requests local-only information
const infoRequest = await readInfoRequest(taskId);

if (infoRequest.request.info_type === "secret_reference") {
  // Provide reference, not actual secret
  await createInfoResponse(taskId, {
    secret_name: infoRequest.request.query,
    reference: "USE_SENDGRID_API_KEY_FROM_LOCAL_ENV",
    instruction: "lex will substitute this at runtime"
  });
}
```

## Core Concepts

### Signal Files

Signal files are JSON files in `.signals/` directories that enable async message passing:

- **Delegation Request**: lex → cex (plan this task)
- **Delegation Response**: cex → lex (plan ready)
- **Approval Sync**: human → lex (task approved/rejected)
- **Info Request**: cex → lex (need local information)
- **Info Response**: lex → cex (here's the information)

### Sync Policies

Every file has a `sync_policy` metadata field:

- `"sync"`: Normal bidirectional sync (default)
- `"local_only"`: Never sync to cloud; cex can only see metadata
- `"cloud_only"`: Only exists in cloud vault (rare)

### Claim-by-Move

Agents use atomic file rename to claim ownership:

```javascript
// Attempt to claim signal
try {
  await fs.rename(
    ".signals/task-123.delegate.json",
    ".signals/task-123.claimed.json"
  );
  // Success! Process the signal
} catch (err) {
  if (err.code === "ENOENT") {
    // Another agent claimed it first
  }
}
```

### Timeout & Cleanup

Signals embed timeout metadata; cleanup job reclaims stale signals:

```json
{
  "task_id": "task-123",
  "created_at": "2025-01-15T10:00:00.000Z",
  "timeout_at": "2025-01-15T10:05:00.000Z"
}
```

Cleanup job runs every 60 seconds and deletes expired signals.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Local Environment                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Executive Agent (lex)                         │   │
│  │  - Creates delegation requests                       │   │
│  │  - Processes cloud responses                         │   │
│  │  - Syncs approval state                              │   │
│  │  - Handles info requests                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  vault_state_manager                                 │   │
│  │  - Low-level file operations                         │   │
│  │  - Permission enforcement                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Vault (VAULT_PATH_LOCAL)                      │   │
│  │  - Needs_Action/, Plans/, In_Progress/, etc.         │   │
│  │  - .signals/ (delegation coordination)               │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕
                    Cloud Sync Layer
                  (Dropbox / rsync / git)
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     Cloud Environment                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cloud Vault (VAULT_PATH_CLOUD)                      │   │
│  │  - Synced folders (Needs_Action/, Plans/, etc.)      │   │
│  │  - .signals/ (synced coordination files)             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cloud Executive Agent (cex)                         │   │
│  │  - Polls for delegation requests                     │   │
│  │  - Creates plans                                     │   │
│  │  - Writes delegation responses                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Security

### Secret Protection

The skill enforces strict security boundaries:

1. **Auto-detection**: Files matching secret patterns are marked `local_only`
2. **Enforcement**: Delegation requests reject `local_only` tasks
3. **Sanitization**: Info responses redact sensitive fields
4. **Validation**: Approval signals require valid signatures

### Secret Detection Patterns

```bash
SECRETS_PATTERN="*.env|*secret*|*key*|*token*|*.pem|*.cert|*.p12"
```

Regex patterns:
- `/API[_-]?KEY/i`
- `/SECRET[_-]?TOKEN/i`
- `/PASSWORD/i`
- `/CREDENTIALS/i`
- `/PRIVATE[_-]?KEY/i`

### Approval Signature Validation

Approval signals include HMAC signature (optional):

```json
{
  "approval": { "decision": "approved", "approved_by": "alice" },
  "signature": {
    "user": "alice",
    "timestamp": "2025-01-15T10:00:00.000Z",
    "hmac": "a1b2c3d4e5f6..."
  }
}
```

Enable with:

```bash
ENABLE_APPROVAL_HMAC="true"
APPROVAL_HMAC_SECRET="your-shared-secret-here"
```

## Monitoring

### Metrics

- **Delegation success rate**: % of delegations that complete without timeout
- **Approval sync latency**: Time from cloud approval to local sync
- **Secret leakage incidents**: MUST be zero
- **Signal orphan rate**: % of signals not cleaned up
- **Sync conflict rate**: % of sync operations that conflict

### Logs

Log files (configure in `.env`):

- `delegation.log`: All delegation events
- `approvals.log`: All approval events
- `delegation_timeouts.log`: Timeout events
- `orphaned_signals.log`: Orphaned signal cleanups
- `sync_conflicts.log`: Sync conflict resolutions

### Alerts

Recommended alerts:

- Delegation timeout rate > 10 per hour
- Approval sync latency > 60 seconds
- Secret leakage attempt (zero tolerance)
- Signal orphan rate > 5%
- Sync offline > 5 minutes

## Troubleshooting

### Delegation timeout

**Symptom**: Task never gets planned by cex

**Causes**:
1. Sync layer offline (Dropbox, rsync not running)
2. cex agent not running
3. Cloud vault path incorrect
4. Signal file permissions

**Debug**:
```bash
# Check sync status
ps aux | grep -i dropbox

# Check signal files
ls -la "$SIGNALS_DIR_LOCAL"
ls -la "$SIGNALS_DIR_CLOUD"

# Check lex logs
tail -f "${VAULT_PATH_LOCAL}/Logs/delegation_timeouts.log"
```

### Secret leakage

**Symptom**: Secrets appear in cloud vault

**Causes**:
1. `AUTO_MARK_SECRETS="false"`
2. Secret pattern not matched
3. User overrode sync policy

**Debug**:
```bash
# Check sync policies
find "$VAULT_PATH_CLOUD" -name "*.json" -exec jq -r '.sync_policy // "sync"' {} \; | sort | uniq -c

# Enable auto-detection
echo 'AUTO_MARK_SECRETS="true"' >> .env

# Test secret detection
grep -r "API_KEY\|SECRET\|TOKEN\|PASSWORD" "$VAULT_PATH_CLOUD"
```

### Orphaned signals

**Symptom**: Signal files accumulating in `.signals/`

**Causes**:
1. Cleanup job not running
2. Timeout too short
3. Agent crashed mid-processing

**Debug**:
```bash
# Check orphaned signals
find "$SIGNALS_DIR_LOCAL" -name "*.claimed.json" -mmin +5

# Manually trigger cleanup
.specify/scripts/bash/cleanup-signals.sh

# Check logs
tail -f "${VAULT_PATH_LOCAL}/Logs/orphaned_signals.log"
```

### Approval conflicts

**Symptom**: Approval in cloud vault not reflected locally

**Causes**:
1. Approval signal not created
2. Sync layer offline
3. Approval signature invalid

**Debug**:
```bash
# Check approval signals
ls -la "$SIGNALS_DIR_LOCAL" | grep ".approval.json"

# Check approval logs
tail -f "${VAULT_PATH_LOCAL}/Logs/approvals.log"

# Manually sync approval
cp "$SIGNALS_DIR_CLOUD/task-123.approval.json" "$SIGNALS_DIR_LOCAL/"
```

## Related Skills

- **vault_state_manager**: Low-level vault file operations
- **task_lifecycle_manager**: Task state transitions
- **approval_request_creator**: Approval workflow
- **needs_action_triage**: Task prioritization

## Related Documents

- **AGENTS.md**: Agent roles and permissions
- **VAULT_SKILLS_INTEGRATION.md**: Skill integration patterns
- **SKILL.md**: Full skill specification
- **patterns.md**: Design patterns
- **gotchas.md**: Edge cases and mitigation strategies
- **impact-checklist.md**: Deployment readiness checklist

## License

This skill is part of the AI-Employee project. See LICENSE file for details.
