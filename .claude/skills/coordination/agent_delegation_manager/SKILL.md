---
name: agent_delegation_manager
description: Coordinate Local ↔ Cloud task ownership, approval sync, and vault sync flags. Manages signal files between local and cloud folders, respecting sensitive secrets stay local rules.
---

# Agent Delegation Manager

## Purpose

This skill provides coordination between Local Executive Agent (lex) and Cloud Executive Agent (cex) for the Digital FTE workflow. It manages task delegation, ownership transfers, approval synchronization, and vault sync state while enforcing security boundaries (sensitive data stays local).

The skill ensures:
- Clean handoffs between local and cloud execution contexts
- Proper signal file management for async coordination
- Secrets never leave local environment
- Vault sync state tracking
- Approval workflow coordination

## When to Use This Skill

Use `agent_delegation_manager` when:

- **Delegating to cloud**: lex needs cex to plan a task (lex → cex handoff)
- **Returning from cloud**: cex completed planning, returning control to lex (cex → lex handoff)
- **Syncing approval state**: Human approved/rejected task in cloud vault, sync to local
- **Managing sync flags**: Track which files are safe to sync vs local-only
- **Coordinating ownership**: Prevent both agents from working on same task
- **Signal file operations**: Create/read/delete delegation signals
- **Security boundary enforcement**: Mark files as `local_only` when they contain secrets

Do NOT use this skill when:

- **Pure local operations**: Use `vault_state_manager` for local-only workflows
- **Pure cloud operations**: Use standard vault operations for cloud-native tasks
- **File content operations**: Use `vault_state_manager` for reading/writing task content
- **Direct approval**: Humans approve via file moves, not via this skill
- **Secret storage**: Never use this to transmit secrets between environments

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH_LOCAL="/absolute/path/to/local/vault"   # Local vault root
VAULT_PATH_CLOUD="/absolute/path/to/cloud/vault"   # Cloud vault root (synced)

# Required: Signal directories
SIGNALS_DIR_LOCAL="${VAULT_PATH_LOCAL}/.signals"   # Local signal files
SIGNALS_DIR_CLOUD="${VAULT_PATH_CLOUD}/.signals"   # Cloud signal files

# Optional: Delegation policies
DELEGATION_TIMEOUT_MS="30000"                       # Timeout for cloud response
DELEGATION_MAX_RETRIES="3"                          # Max retries for failed delegation
DELEGATION_SYNC_INTERVAL_MS="5000"                  # Poll interval for cloud responses

# Optional: Security policies
SECRETS_PATTERN="*.env|*secret*|*key*|*token*"      # Patterns for local-only files
AUTO_MARK_SECRETS="true"                            # Auto-detect and mark secret files
ALLOW_CLOUD_APPROVAL="false"                        # Allow approvals via cloud (risky)
```

**Secrets Management:**

- This skill enforces secret locality (secrets stay on local machine)
- Never sync files matching SECRETS_PATTERN to cloud vault
- Mark sensitive files with `sync_policy: local_only` metadata
- Cloud agent (cex) can only reference secrets by name, never read them

**Variable Discovery Process:**
```bash
# Check delegation configuration
cat .env | grep -E "(VAULT_PATH|SIGNALS_DIR|DELEGATION_)"

# Verify signal directories exist
for env in LOCAL CLOUD; do
  eval "dir=\$SIGNALS_DIR_$env"
  test -d "$dir" || echo "Missing: $dir"
done

# Check sync policy enforcement
find "$VAULT_PATH_LOCAL" -name "*.json" -exec jq -r '.sync_policy // "sync"' {} \; | sort | uniq -c
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on filesystem only.

**Cloud sync assumed to be handled by external tool** (e.g., Dropbox, rsync, git, Obsidian Sync).

**Dependency Topology:**

```
Agent Delegation Manager
  ├── Vault State Manager (file operations)
  │   └── Local Filesystem (VAULT_PATH_LOCAL)
  ├── Cloud Sync Layer (external: Dropbox/rsync/git)
  │   └── Remote Filesystem (VAULT_PATH_CLOUD)
  └── Signal File Protocol (.signals/ directories)
```

**Topology Notes:**
- Local and cloud vaults are separate filesystem paths
- Sync layer (Dropbox, rsync, etc.) handles file replication
- Signal files use claim-by-move semantics for coordination
- No direct network communication between lex and cex

**Docker/K8s Implications:**

When containerizing:
- Mount local vault: `-v /host/vault_local:/vault_local`
- Mount cloud vault: `-v /host/vault_cloud:/vault_cloud` (synced folder)
- Ensure signal directories are writable by both lex and cloud sync process
- Use volume claims in Kubernetes for persistent storage

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication required (local filesystem)
- Agent authorization enforced by signal file ownership
- Cloud sync handled by external tool (Dropbox OAuth, SSH keys, etc.)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Secret leakage to cloud** | Enforce `local_only` sync policy; reject cloud access |
| **Task hijacking** | Signal files are atomic (claim-by-move); ownership tracked |
| **Approval tampering** | Approval signals require human signature (timestamp + user) |
| **Stale signals** | Timeout stale signals after DELEGATION_TIMEOUT_MS |
| **Sync conflicts** | Last-write-wins for metadata; signal files prevent race |
| **Malicious cloud response** | Validate all cloud responses; reject unexpected state changes |

**Security Rules:**

Per AGENTS.md and security best practices:

| Agent | Can Do | Cannot Do |
|-------|--------|-----------|
| `lex` | Create delegation signals, read cloud responses, mark `local_only` | Send secrets to cloud, approve own tasks |
| `cex` | Create plan responses, request info via signals | Read `local_only` files, execute tasks, approve tasks |
| `human` | Approve/reject via file moves in either vault | N/A (full authority) |

**Sync Policy Enforcement:**

Every file has metadata field:
```yaml
sync_policy: "sync" | "local_only" | "cloud_only"
```

Rules:
- `sync`: Normal bidirectional sync
- `local_only`: Never sync to cloud; cex can only see metadata
- `cloud_only`: Only exists in cloud vault (rare; for cloud-native logs)

**Audit Requirements:**

Every delegation event must log:
- Timestamp (ISO 8601, UTC)
- Task ID
- Delegation direction (lex→cex or cex→lex)
- Signal file path
- Sync policy of delegated task
- Agent identities
- Outcome (success, timeout, rejected)

## Blueprints & Templates Used

### Blueprint: Signal File Structure

**Purpose:** Coordinate async handoffs between lex and cex

**Signal Types:**

1. **Delegation Request** (`<task_id>.delegate.json` in `SIGNALS_DIR_LOCAL`)
   ```json
   {
     "signal_type": "delegation_request",
     "task_id": "{{TASK_ID}}",
     "from_agent": "lex",
     "to_agent": "cex",
     "created_at": "{{TIMESTAMP_ISO}}",
     "timeout_at": "{{TIMEOUT_TIMESTAMP}}",
     "request": {
       "action": "plan_task",
       "task_path": "Needs_Action/{{TASK_ID}}.json",
       "sync_policy": "sync",
       "context": {
         "user_request": "{{USER_REQUEST}}",
         "constraints": ["{{CONSTRAINT_1}}", "{{CONSTRAINT_2}}"]
       }
     },
     "metadata": {
       "priority": "medium",
       "autonomy_tier": "silver"
     }
   }
   ```

2. **Delegation Response** (`<task_id>.response.json` in `SIGNALS_DIR_CLOUD`)
   ```json
   {
     "signal_type": "delegation_response",
     "task_id": "{{TASK_ID}}",
     "from_agent": "cex",
     "to_agent": "lex",
     "created_at": "{{TIMESTAMP_ISO}}",
     "in_response_to": "{{DELEGATION_REQUEST_ID}}",
     "response": {
       "status": "completed" | "failed" | "needs_info",
       "plan_path": "Plans/{{TASK_ID}}.json",
       "sync_policy": "sync",
       "outcome": "{{OUTCOME_DESCRIPTION}}",
       "next_action": "{{RECOMMENDED_NEXT_STEP}}"
     },
     "errors": []
   }
   ```

3. **Approval Sync** (`<task_id>.approval.json` in `SIGNALS_DIR_CLOUD`)
   ```json
   {
     "signal_type": "approval_sync",
     "task_id": "{{TASK_ID}}",
     "from_agent": "human",
     "to_agent": "lex",
     "created_at": "{{TIMESTAMP_ISO}}",
     "approval": {
       "decision": "approved" | "rejected",
       "reason": "{{HUMAN_REASON}}",
       "approved_by": "{{HUMAN_USER}}",
       "task_path": "Approved/{{TASK_ID}}.json",
       "sync_policy": "sync"
     }
   }
   ```

4. **Info Request** (`<task_id>.info_request.json` in `SIGNALS_DIR_CLOUD`)
   ```json
   {
     "signal_type": "info_request",
     "task_id": "{{TASK_ID}}",
     "from_agent": "cex",
     "to_agent": "lex",
     "created_at": "{{TIMESTAMP_ISO}}",
     "request": {
       "info_type": "secret_reference" | "file_content" | "env_var",
       "query": "{{QUERY_DESCRIPTION}}",
       "required_for": "{{REASONING}}"
     }
   }
   ```

**Impact Notes:**
- Signal files are ephemeral (deleted after processing)
- Use atomic writes (write to temp file, then rename)
- Signal filenames include task_id for uniqueness
- Timeout logic prevents orphaned signals

### Blueprint: Delegation Workflow

**Purpose:** Coordinate lex → cex → lex handoff

**Workflow Steps:**

```
1. lex: Task arrives in Needs_Action/
2. lex: Create delegation request signal in SIGNALS_DIR_LOCAL
3. Sync: Dropbox syncs signal to SIGNALS_DIR_CLOUD
4. cex: Polls SIGNALS_DIR_CLOUD, finds delegation request
5. cex: Claims task (via signal file claim-by-move)
6. cex: Creates plan in Plans/ (cloud vault)
7. cex: Writes delegation response signal to SIGNALS_DIR_CLOUD
8. Sync: Dropbox syncs response to SIGNALS_DIR_LOCAL
9. lex: Finds delegation response signal
10. lex: Validates plan, moves to In_Progress/ (local vault)
11. lex: Deletes signal files (cleanup)
```

**Timeout Handling:**

If cex doesn't respond within DELEGATION_TIMEOUT_MS:
- lex deletes delegation request signal
- lex logs timeout event
- lex handles task locally (fallback) or escalates to human

**Conflict Resolution:**

If both lex and cex try to claim same signal:
- First agent to move signal file wins (atomic filesystem operation)
- Second agent gets "file not found" error and retries with different task

### Blueprint: Sync Policy Enforcement

**Purpose:** Prevent secrets from leaving local environment

**Enforcement Points:**

1. **File Creation**: When creating new task/plan files
   ```javascript
   // Pseudo-code
   function createTaskFile(content) {
     const syncPolicy = detectSecretsInContent(content)
       ? "local_only"
       : "sync";

     const metadata = {
       ...content,
       sync_policy: syncPolicy,
       created_at: new Date().toISOString()
     };

     writeFile(taskPath, metadata);

     if (syncPolicy === "local_only") {
       createLocalOnlyMarker(taskPath);
     }
   }
   ```

2. **Delegation Request**: Check sync policy before delegating
   ```javascript
   function delegateToCloud(taskId) {
     const task = readTaskFile(taskId);

     if (task.sync_policy === "local_only") {
       throw new Error("Cannot delegate local-only task to cloud");
     }

     createDelegationSignal(taskId);
   }
   ```

3. **Cloud Access**: cex cannot read local-only files
   ```javascript
   function readTaskFile(taskId, agentName) {
     const task = readTaskMetadata(taskId);

     if (agentName === "cex" && task.sync_policy === "local_only") {
       // Return sanitized metadata only (no content)
       return {
         task_id: task.task_id,
         title: task.title,
         sync_policy: "local_only",
         message: "Content restricted to local agent"
       };
     }

     return task;
   }
   ```

**Secret Detection Patterns:**

Auto-detect and mark as `local_only` if content matches:
- Regex: `/API[_-]?KEY|SECRET|TOKEN|PASSWORD|CREDENTIALS/i`
- Filenames: `*.env`, `*secret*`, `*key*`, `*token*`
- File extensions: `.pem`, `.key`, `.cert`, `.p12`
- Environment variable references: `${API_KEY}`, `$SECRET_TOKEN`

## Core Operations

### Operation: Delegate Task to Cloud

**Purpose:** Hand off task planning from lex to cex

**Preconditions:**
- Task exists in Needs_Action/ or Plans/
- Task sync_policy != "local_only"
- No existing delegation signal for this task
- SIGNALS_DIR_LOCAL is writable

**Steps:**
1. Read task metadata
2. Validate sync policy allows cloud access
3. Create delegation request signal in SIGNALS_DIR_LOCAL
4. Set timeout timer (DELEGATION_TIMEOUT_MS)
5. Return signal ID to caller
6. (Async) Poll for delegation response signal in SIGNALS_DIR_LOCAL

**Postconditions:**
- Delegation request signal exists in SIGNALS_DIR_LOCAL
- Task ownership transferred to cex
- Timeout scheduled

**Error Handling:**
- If sync_policy="local_only": reject with error
- If signal already exists: wait for completion or timeout
- If SIGNALS_DIR_LOCAL not writable: fallback to local planning

### Operation: Receive Cloud Response

**Purpose:** Process cex's delegation response

**Preconditions:**
- Delegation request signal was created by lex
- Delegation response signal exists in SIGNALS_DIR_LOCAL (synced from cloud)
- Response timeout not exceeded

**Steps:**
1. Read delegation response signal
2. Validate response matches original request (task_id, request_id)
3. Check response status (completed, failed, needs_info)
4. If completed: read plan file from Plans/, validate structure
5. If failed: log error, fallback to local planning
6. If needs_info: handle info request (see Operation: Handle Info Request)
7. Delete both delegation request and response signals (cleanup)

**Postconditions:**
- Plan file exists in Plans/ (if response=completed)
- Signal files deleted
- Task ready for next stage

**Error Handling:**
- If response invalid: log error, retry or fallback
- If plan file missing: log error, request recreation
- If timeout exceeded: abandon response, handle locally

### Operation: Sync Approval State

**Purpose:** Sync human approval from cloud vault to local vault

**Preconditions:**
- Human approved/rejected task in cloud vault (Approved/ or Rejected/)
- Approval sync signal exists in SIGNALS_DIR_LOCAL (synced from cloud)
- Task exists in local vault

**Steps:**
1. Read approval sync signal from SIGNALS_DIR_LOCAL
2. Validate approval signature (timestamp, user)
3. Locate task in local vault (In_Progress/ or Pending_Approval/)
4. Move task to Approved/ or Rejected/ in local vault (matching cloud)
5. Update task metadata with approval details
6. Delete approval sync signal
7. Log approval event

**Postconditions:**
- Local vault approval state matches cloud vault
- Task in Approved/ or Rejected/ (local)
- Approval event logged

**Error Handling:**
- If task not found locally: log warning, sync task from cloud
- If approval signature invalid: reject and alert human
- If approval conflicts with local state: human resolves

### Operation: Handle Info Request

**Purpose:** Respond to cex request for local-only information

**Preconditions:**
- Info request signal exists in SIGNALS_DIR_LOCAL (synced from cloud)
- lex has access to requested information
- Information request is safe (no secret leakage)

**Steps:**
1. Read info request signal
2. Validate request type (secret_reference, file_content, env_var)
3. If secret_reference: provide reference name only (e.g., "USE_API_KEY_FROM_ENV")
4. If file_content: check sync_policy; reject if local_only
5. If env_var: provide non-sensitive vars only
6. Create info response signal in SIGNALS_DIR_LOCAL
7. Delete info request signal

**Postconditions:**
- Info response signal created
- No secrets leaked
- Request satisfied or rejected with reason

**Error Handling:**
- If request asks for secrets: reject with error message
- If requested resource doesn't exist: return error response
- If request type unknown: reject and log

## Integration with Existing Skills

### With vault_state_manager

- Delegates low-level file operations to vault_state_manager
- Uses vault_state_manager's permission system
- Extends vault_state_manager with cross-vault coordination

### With task_lifecycle_manager

- Coordinates with task_lifecycle_manager for state transitions
- Delegation events trigger lifecycle state changes
- Approval sync updates lifecycle metadata

### With approval_request_creator

- Approval requests created by approval_request_creator trigger approval sync
- Delegation manager syncs approval decisions back to local vault

## Gotchas & Edge Cases

See `references/gotchas.md` for detailed edge case handling:
- Signal file race conditions
- Sync conflicts between local and cloud vaults
- Orphaned signal files after crashes
- Clock skew between local and cloud environments
- Partial sync failures (signal synced but task file not synced)
- Circular delegation loops
- Secret detection false positives/negatives

## Success Metrics

- **Delegation success rate**: % of delegations that complete without timeout
- **Approval sync latency**: Time from cloud approval to local sync
- **Secret leakage incidents**: MUST be zero
- **Signal file orphan rate**: % of signals not cleaned up
- **Sync conflict rate**: % of sync operations that conflict

## Testing Checklist

- [ ] Delegate task to cloud (success case)
- [ ] Delegate task to cloud (timeout case)
- [ ] Receive cloud response (completed)
- [ ] Receive cloud response (failed)
- [ ] Receive cloud response (needs_info)
- [ ] Sync approval state (approved)
- [ ] Sync approval state (rejected)
- [ ] Handle info request (safe request)
- [ ] Handle info request (reject secret request)
- [ ] Enforce local_only sync policy
- [ ] Detect secrets in task content
- [ ] Clean up signal files after processing
- [ ] Handle signal file race conditions
- [ ] Handle sync conflicts
- [ ] Handle orphaned signals (timeout cleanup)

---

**Related Skills:**
- `vault_state_manager` - Low-level vault operations
- `task_lifecycle_manager` - Task state transitions
- `approval_request_creator` - Approval workflow

**Related Documents:**
- `AGENTS.md` - Agent roles and permissions
- `VAULT_SKILLS_INTEGRATION.md` - Skill integration patterns
