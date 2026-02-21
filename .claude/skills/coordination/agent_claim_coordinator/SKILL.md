---
name: agent_claim_coordinator
description: Ensure no two agents work the same task, handle conflicts. Inspects In_Progress folders and resolves claims based on timestamps and rules.
---

# Agent Claim Coordinator

## Purpose

This skill provides conflict detection and resolution for task claims in the Digital FTE workflow. It ensures that only one agent can work on a task at any given time, preventing duplicate work, race conditions, and inconsistent state updates.

The skill monitors task ownership, detects claim conflicts, and resolves them using configurable policies based on timestamps, agent priority, and business rules.

## When to Use This Skill

Use `agent_claim_coordinator` when:

- **Detecting claim conflicts**: Multiple agents attempt to claim the same task
- **Resolving ownership disputes**: Determine which agent should work on a conflicted task
- **Validating claims**: Verify that task ownership is legitimate and not stale
- **Reclaiming abandoned tasks**: Detect and reclaim tasks from crashed or stuck agents
- **Preventing duplicate work**: Ensure single-agent ownership before task execution
- **Auditing task ownership**: Track which agent owns which task
- **Enforcing agent permissions**: Validate that agent has permission to claim task

Do NOT use this skill when:

- **Creating new tasks**: Use `vault_state_manager` for task creation
- **Updating task content**: Use task-specific skills for content updates
- **Managing task lifecycle**: Use `task_lifecycle_manager` for state transitions
- **Delegating tasks**: Use `agent_delegation_manager` for cross-agent coordination

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"      # Vault root directory

# Optional: Conflict resolution policies
CLAIM_RESOLUTION_POLICY="first_claim_wins" # first_claim_wins | agent_priority | human_resolve
CLAIM_TIMEOUT_MS="300000"                  # 5 minutes (stale claim threshold)
CLAIM_HEARTBEAT_INTERVAL_MS="30000"        # 30 seconds (heartbeat update interval)

# Optional: Agent priorities (comma-separated, highest=1)
AGENT_PRIORITIES="orch:1,lex:2,cex:3,watcher:4"

# Optional: Conflict detection
CONFLICT_CHECK_INTERVAL_MS="60000"         # 1 minute (how often to check for conflicts)
ENABLE_AUTOMATIC_RECLAIM="true"            # Auto-reclaim stale tasks

# Optional: Logging
CLAIM_LOG_LEVEL="info"                     # debug | info | warn | error
CLAIM_LOG_FILE="${VAULT_PATH}/Logs/claims.log"
CONFLICT_LOG_FILE="${VAULT_PATH}/Logs/claim_conflicts.log"
```

**Secrets Management:**

- This skill does NOT handle secrets
- Task metadata may contain agent credentials (sanitized in logs)
- Agent authentication managed outside claim coordination

**Variable Discovery Process:**
```bash
# Check claim coordinator configuration
cat .env | grep -E "(CLAIM_|AGENT_PRIORITIES)"

# Verify In_Progress folder exists
test -d "$VAULT_PATH/In_Progress" || echo "In_Progress folder missing"

# Check for conflicted tasks
find "$VAULT_PATH/In_Progress" -name "*.json" -exec jq -r '.claimed_by' {} \; | sort | uniq -c
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Agent Claim Coordinator
  └── Vault State Manager (file operations)
      └── Filesystem (local disk)
          ├── In_Progress/ (active tasks)
          ├── Needs_Action/ (unclaimed tasks)
          └── Logs/ (audit trail)
```

**Topology Notes:**
- All operations are synchronous filesystem I/O
- No external services or network dependencies
- Compatible with network filesystems (NFS, SMB) but claim-by-move may have weaker guarantees

**Docker/K8s Implications:**

When containerizing:
- Mount vault as persistent volume: `-v /host/vault:/vault`
- Ensure In_Progress/ is writable by container user
- Use PersistentVolumeClaims in Kubernetes
- Be aware of filesystem atomicity guarantees in shared volumes

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication required (local filesystem)
- Agent authorization enforced by permission rules (see AGENTS.md §3)
- Claim ownership tracked in task metadata

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Claim hijacking** | Validate agent identity before allowing claim |
| **Stale claims** | Timeout stale claims; require heartbeat |
| **Race conditions** | Atomic file operations (claim-by-move) |
| **Privilege escalation** | Enforce agent permission rules |
| **Audit trail tampering** | Logs are append-only; detect size decreases |
| **Denial of service** | Rate limit claim attempts per agent |

**Agent Permission Rules:**

Per AGENTS.md §3, agents have different claim permissions:

| Agent | Can Claim From | Cannot Claim From |
|-------|----------------|-------------------|
| `lex` | `Needs_Action/`, `Plans/` | `Approved/` (orchestrator only) |
| `cex` | NONE (read-only via lex proxy) | ALL |
| `orch` | `Approved/` | `Needs_Action/`, `Plans/` |
| Watchers | NONE (write-only to Needs_Action/) | ALL |
| `human` | ALL (override authority) | N/A |

This skill MUST enforce these rules before allowing claims.

**Audit Requirements:**

Every claim operation must log:
- Timestamp (ISO 8601, UTC)
- Task ID
- Agent identity (claimed_by, previous_owner)
- Claim action (claim, release, conflict, reclaim)
- Resolution policy applied (if conflict)
- Outcome (success, rejected, escalated)

## Blueprints & Templates Used

### Blueprint: Claim Metadata Structure

**Purpose:** Standardize claim ownership tracking in task metadata

**Template Variables:**
```yaml
# Claim ownership fields (embedded in task JSON)
claimed_by: "{{AGENT_NAME}}"              # Current owner
claimed_at: "{{TIMESTAMP_ISO}}"           # When claimed
claim_expires_at: "{{EXPIRY_TIMESTAMP}}"  # Timeout threshold
last_heartbeat: "{{TIMESTAMP_ISO}}"       # Last activity signal
claim_id: "{{UNIQUE_CLAIM_ID}}"           # Unique claim identifier

# Claim history (append-only log)
claim_history:
  - agent: "{{AGENT_1}}"
    action: "claim"
    timestamp: "{{TIMESTAMP_1}}"
    claim_id: "{{CLAIM_ID_1}}"
  - agent: "{{AGENT_2}}"
    action: "conflict_detected"
    timestamp: "{{TIMESTAMP_2}}"
    resolution: "{{RESOLUTION_POLICY}}"
  - agent: "{{AGENT_1}}"
    action: "release"
    timestamp: "{{TIMESTAMP_3}}"

# Conflict metadata (added when conflict occurs)
conflict:
  detected: true
  detected_at: "{{TIMESTAMP_ISO}}"
  competing_agents: ["{{AGENT_1}}", "{{AGENT_2}}"]
  resolution_policy: "{{POLICY_NAME}}"
  resolved_by: "{{WINNING_AGENT}}"
  resolved_at: "{{TIMESTAMP_ISO}}"
```

**Impact Notes:**
- All timestamps must be ISO 8601 format (UTC)
- Claim IDs must be unique (UUID recommended)
- Claim history is append-only (never delete entries)
- Heartbeat must be updated within CLAIM_TIMEOUT_MS to keep claim alive

### Blueprint: Claim-by-Move Protocol

**Purpose:** Atomically claim tasks from Needs_Action/ to In_Progress/

**When to Use:**
- Agent wants to claim unclaimed task
- Prevents race conditions via filesystem atomicity

**Protocol Steps:**

```
1. Agent reads task from Needs_Action/<task_id>.json
2. Agent validates:
   - Task not already claimed (no claimed_by field)
   - Agent has permission to claim this task
   - Task meets agent's capability requirements
3. Agent updates task metadata:
   - Set claimed_by = agent_name
   - Set claimed_at = current_timestamp
   - Set claim_expires_at = current_timestamp + CLAIM_TIMEOUT_MS
   - Set last_heartbeat = current_timestamp
   - Set claim_id = generate_uuid()
   - Append to claim_history
4. Agent atomically moves file:
   fs.rename(
     "Needs_Action/<task_id>.json",
     "In_Progress/<task_id>.json"
   )
5. If rename succeeds: claim successful
6. If rename fails (ENOENT): another agent claimed first; retry with different task
```

**Impact Notes:**
- Atomic rename guarantees single winner
- POSIX filesystems provide atomicity guarantees
- Network filesystems (NFS) may have weaker guarantees; use locking
- Failed claims should be logged but are not errors (expected behavior)

### Blueprint: Conflict Resolution Policies

**Purpose:** Define how to resolve claim conflicts when detected

**Policy: first_claim_wins**

```yaml
name: first_claim_wins
description: Agent with earliest claimed_at timestamp wins
implementation: |
  function resolveConflict(task, competingAgents) {
    const claims = competingAgents.map(agent => ({
      agent: agent,
      claimed_at: task.claim_history.find(h => h.agent === agent && h.action === 'claim').timestamp
    }));

    // Sort by timestamp (earliest first)
    claims.sort((a, b) => new Date(a.claimed_at) - new Date(b.claimed_at));

    const winner = claims[0].agent;
    const losers = claims.slice(1).map(c => c.agent);

    return { winner, losers };
  }
```

**Policy: agent_priority**

```yaml
name: agent_priority
description: Agent with highest priority (lowest priority number) wins
configuration: |
  # In .env
  AGENT_PRIORITIES="orch:1,lex:2,cex:3,watcher:4"
implementation: |
  function resolveConflict(task, competingAgents) {
    const priorities = parsePriorities(process.env.AGENT_PRIORITIES);

    const claims = competingAgents.map(agent => ({
      agent: agent,
      priority: priorities[agent] || 999
    }));

    // Sort by priority (lowest number = highest priority)
    claims.sort((a, b) => a.priority - b.priority);

    const winner = claims[0].agent;
    const losers = claims.slice(1).map(c => c.agent);

    return { winner, losers };
  }
```

**Policy: human_resolve**

```yaml
name: human_resolve
description: Escalate conflict to human for manual resolution
implementation: |
  function resolveConflict(task, competingAgents) {
    // Create conflict marker file
    const conflictPath = `In_Progress/${task.task_id}.conflict`;
    fs.writeFileSync(conflictPath, JSON.stringify({
      task_id: task.task_id,
      competing_agents: competingAgents,
      detected_at: new Date().toISOString(),
      resolution_required: true
    }, null, 2));

    // Notify human
    notifyHuman({
      type: 'claim_conflict',
      task_id: task.task_id,
      agents: competingAgents,
      message: 'Multiple agents claim ownership. Please resolve manually.'
    });

    // Freeze task (no agent can proceed until resolved)
    return { winner: null, losers: competingAgents, escalated: true };
  }
```

**Impact Notes:**
- Policy is configured via CLAIM_RESOLUTION_POLICY env var
- first_claim_wins: Fast, deterministic, fair for equal-priority agents
- agent_priority: Respects agent hierarchy, useful for critical tasks
- human_resolve: Conservative, safest, but requires manual intervention

### Blueprint: Heartbeat Protocol

**Purpose:** Detect crashed or stuck agents and reclaim their tasks

**Protocol:**

```yaml
name: heartbeat_protocol
description: Agents update last_heartbeat field to prove they're alive
interval: 30 seconds (CLAIM_HEARTBEAT_INTERVAL_MS)
timeout: 5 minutes (CLAIM_TIMEOUT_MS)

agent_implementation: |
  // Agent updates heartbeat while working on task
  setInterval(async () => {
    const task = await readTaskFile(taskId);
    task.last_heartbeat = new Date().toISOString();
    await writeTaskFile(taskId, task);
  }, CLAIM_HEARTBEAT_INTERVAL_MS);

coordinator_implementation: |
  // Coordinator checks for stale claims
  async function reclaimStaleTasks() {
    const tasks = await listTasksInProgress();

    for (const task of tasks) {
      const lastHeartbeat = new Date(task.last_heartbeat || task.claimed_at);
      const now = new Date();
      const staleness = now - lastHeartbeat;

      if (staleness > CLAIM_TIMEOUT_MS) {
        console.warn(`Stale claim detected: ${task.task_id} by ${task.claimed_by}`);

        // Release claim
        delete task.claimed_by;
        delete task.claimed_at;
        delete task.claim_expires_at;
        delete task.last_heartbeat;

        // Add to claim history
        task.claim_history.push({
          agent: task.claimed_by,
          action: 'reclaimed_stale',
          timestamp: now.toISOString(),
          reason: `No heartbeat for ${staleness}ms`
        });

        // Move back to Needs_Action
        await moveFile(
          `In_Progress/${task.task_id}.json`,
          `Needs_Action/${task.task_id}.json`
        );

        // Log reclaim event
        await appendToLog('claims.log', {
          task_id: task.task_id,
          action: 'reclaim',
          previous_owner: task.claimed_by,
          staleness_ms: staleness,
          reclaimed_at: now.toISOString()
        });
      }
    }
  }

  // Run every 60 seconds
  setInterval(reclaimStaleTasks, 60000);
```

**Impact Notes:**
- Heartbeat interval should be < timeout / 2 to prevent false positives
- Clock skew between agents can cause premature reclaims; add tolerance
- Heartbeat updates should be lightweight (update single field only)

## Core Operations

### Operation: Claim Task

**Purpose:** Agent claims unclaimed task from Needs_Action/

**Preconditions:**
- Task exists in Needs_Action/
- Task not already claimed (no claimed_by field)
- Agent has permission to claim this task type
- Agent meets task capability requirements

**Steps:**
1. Read task from Needs_Action/<task_id>.json
2. Validate preconditions
3. Update task metadata:
   - Set claimed_by = agent_name
   - Set claimed_at = current_timestamp
   - Set claim_expires_at = current_timestamp + CLAIM_TIMEOUT_MS
   - Set last_heartbeat = current_timestamp
   - Set claim_id = generate_uuid()
   - Append to claim_history: { agent, action: "claim", timestamp }
4. Atomically move file to In_Progress/
5. Start heartbeat updates

**Postconditions:**
- Task in In_Progress/ with claimed_by = agent_name
- Heartbeat updates running
- Claim logged

**Error Handling:**
- If file move fails (ENOENT): another agent claimed first; return conflict
- If agent lacks permission: reject with error
- If task already claimed: return conflict

**Example:**
```javascript
async function claimTask(taskId, agentName) {
  const taskPath = `${VAULT_PATH}/Needs_Action/${taskId}.json`;
  const task = JSON.parse(await fs.readFile(taskPath, 'utf-8'));

  // Validate preconditions
  if (task.claimed_by) {
    throw new Error('Task already claimed');
  }

  if (!canAgentClaimTask(agentName, task)) {
    throw new Error('Agent lacks permission to claim this task');
  }

  // Update claim metadata
  const claimId = uuidv4();
  const now = new Date();

  task.claimed_by = agentName;
  task.claimed_at = now.toISOString();
  task.claim_expires_at = new Date(now.getTime() + CLAIM_TIMEOUT_MS).toISOString();
  task.last_heartbeat = now.toISOString();
  task.claim_id = claimId;

  if (!task.claim_history) task.claim_history = [];
  task.claim_history.push({
    agent: agentName,
    action: 'claim',
    timestamp: now.toISOString(),
    claim_id: claimId
  });

  // Write to temp file, then atomic rename
  const tempPath = `${VAULT_PATH}/Needs_Action/${taskId}.tmp`;
  await fs.writeFile(tempPath, JSON.stringify(task, null, 2));

  try {
    await fs.rename(tempPath, `${VAULT_PATH}/In_Progress/${taskId}.json`);
    console.log(`Claim successful: ${taskId} by ${agentName}`);

    // Start heartbeat
    startHeartbeat(taskId, agentName);

    return { success: true, claim_id: claimId };

  } catch (err) {
    await fs.unlink(tempPath); // Cleanup temp file
    if (err.code === 'ENOENT') {
      return { success: false, reason: 'already_claimed' };
    }
    throw err;
  }
}
```

### Operation: Detect Conflicts

**Purpose:** Scan In_Progress/ for tasks with conflicting claims

**Preconditions:**
- In_Progress/ folder exists and is readable

**Steps:**
1. List all tasks in In_Progress/
2. For each task:
   - Check if claimed_by matches current owner
   - Check if claim is stale (last_heartbeat too old)
   - Check if multiple agents have active claims (conflict)
3. Collect conflicts: { task_id, competing_agents, detected_at }
4. Return list of conflicts

**Postconditions:**
- List of conflicted tasks
- No state changes (detection only)

**Error Handling:**
- If In_Progress/ not readable: log error, return empty list
- If task file corrupted: log error, skip task

**Example:**
```javascript
async function detectConflicts() {
  const conflicts = [];
  const inProgressPath = `${VAULT_PATH}/In_Progress`;
  const taskFiles = await fs.readdir(inProgressPath);

  for (const taskFile of taskFiles) {
    if (!taskFile.endsWith('.json')) continue;

    const taskPath = `${inProgressPath}/${taskFile}`;
    const task = JSON.parse(await fs.readFile(taskPath, 'utf-8'));

    // Check for stale claim
    if (task.claimed_by && task.last_heartbeat) {
      const lastHeartbeat = new Date(task.last_heartbeat);
      const staleness = Date.now() - lastHeartbeat.getTime();

      if (staleness > CLAIM_TIMEOUT_MS) {
        conflicts.push({
          task_id: task.task_id,
          type: 'stale_claim',
          owner: task.claimed_by,
          staleness_ms: staleness,
          detected_at: new Date().toISOString()
        });
      }
    }

    // Check for multiple competing claims (shouldn't happen, but detect)
    if (task.claim_history) {
      const recentClaims = task.claim_history.filter(h =>
        h.action === 'claim' &&
        new Date(h.timestamp).getTime() > Date.now() - CLAIM_TIMEOUT_MS
      );

      if (recentClaims.length > 1) {
        const competingAgents = [...new Set(recentClaims.map(c => c.agent))];
        conflicts.push({
          task_id: task.task_id,
          type: 'multiple_claims',
          competing_agents: competingAgents,
          detected_at: new Date().toISOString()
        });
      }
    }
  }

  return conflicts;
}
```

### Operation: Resolve Conflict

**Purpose:** Apply resolution policy to conflicted task

**Preconditions:**
- Conflict detected (from detectConflicts)
- Resolution policy configured (CLAIM_RESOLUTION_POLICY)
- Task exists in In_Progress/

**Steps:**
1. Read conflict details (task_id, competing_agents)
2. Load resolution policy (first_claim_wins, agent_priority, human_resolve)
3. Apply policy to determine winner
4. Update task metadata:
   - Set claimed_by = winner
   - Update claim_expires_at
   - Add conflict entry to task.conflict
   - Append to claim_history: { action: "conflict_resolved", winner, losers }
5. Notify losing agents (optional)
6. Log conflict resolution

**Postconditions:**
- Task ownership assigned to winner
- Losing agents notified (if applicable)
- Conflict logged

**Error Handling:**
- If policy unknown: fallback to human_resolve
- If winner determination fails: escalate to human
- If task deleted during resolution: log warning, skip

**Example:**
```javascript
async function resolveConflict(conflict) {
  const task = await readTaskFile(`In_Progress/${conflict.task_id}.json`);
  const policy = process.env.CLAIM_RESOLUTION_POLICY || 'first_claim_wins';

  let winner, losers;

  switch (policy) {
    case 'first_claim_wins':
      ({ winner, losers } = resolveByFirstClaim(task, conflict.competing_agents));
      break;

    case 'agent_priority':
      ({ winner, losers } = resolveByPriority(task, conflict.competing_agents));
      break;

    case 'human_resolve':
      ({ winner, losers, escalated } = escalateToHuman(task, conflict.competing_agents));
      if (escalated) return { escalated: true };
      break;

    default:
      console.warn(`Unknown policy: ${policy}; escalating to human`);
      return escalateToHuman(task, conflict.competing_agents);
  }

  // Update task metadata
  task.claimed_by = winner;
  task.claim_expires_at = new Date(Date.now() + CLAIM_TIMEOUT_MS).toISOString();

  task.conflict = {
    detected: true,
    detected_at: conflict.detected_at,
    competing_agents: conflict.competing_agents,
    resolution_policy: policy,
    resolved_by: winner,
    resolved_at: new Date().toISOString()
  };

  task.claim_history.push({
    agent: winner,
    action: 'conflict_resolved',
    timestamp: new Date().toISOString(),
    policy: policy,
    losers: losers
  });

  await writeTaskFile(`In_Progress/${conflict.task_id}.json`, task);

  // Log resolution
  await appendToLog('claim_conflicts.log', {
    task_id: task.task_id,
    competing_agents: conflict.competing_agents,
    policy: policy,
    winner: winner,
    losers: losers,
    resolved_at: new Date().toISOString()
  });

  console.log(`Conflict resolved: ${task.task_id} → ${winner} (policy: ${policy})`);

  return { success: true, winner, losers };
}
```

### Operation: Reclaim Stale Task

**Purpose:** Reclaim task from agent that stopped updating heartbeat

**Preconditions:**
- Task in In_Progress/ with stale heartbeat (last_heartbeat > CLAIM_TIMEOUT_MS ago)
- ENABLE_AUTOMATIC_RECLAIM = true

**Steps:**
1. Validate staleness (last_heartbeat vs current time)
2. Update task metadata:
   - Delete claimed_by, claimed_at, claim_expires_at, last_heartbeat fields
   - Append to claim_history: { action: "reclaimed_stale", previous_owner, staleness }
3. Move task from In_Progress/ to Needs_Action/
4. Log reclaim event

**Postconditions:**
- Task in Needs_Action/ (unclaimed)
- Previous owner logged in claim_history
- Reclaim event logged

**Error Handling:**
- If task deleted during reclaim: log warning, skip
- If file move fails: log error, retry

**Example:**
```javascript
async function reclaimStaleTask(taskId) {
  const taskPath = `${VAULT_PATH}/In_Progress/${taskId}.json`;
  const task = JSON.parse(await fs.readFile(taskPath, 'utf-8'));

  const lastHeartbeat = new Date(task.last_heartbeat || task.claimed_at);
  const staleness = Date.now() - lastHeartbeat.getTime();

  if (staleness <= CLAIM_TIMEOUT_MS) {
    return { reclaimed: false, reason: 'claim_still_active' };
  }

  const previousOwner = task.claimed_by;

  // Release claim
  delete task.claimed_by;
  delete task.claimed_at;
  delete task.claim_expires_at;
  delete task.last_heartbeat;
  delete task.claim_id;

  task.claim_history.push({
    agent: previousOwner,
    action: 'reclaimed_stale',
    timestamp: new Date().toISOString(),
    staleness_ms: staleness,
    reason: `No heartbeat for ${Math.round(staleness / 1000)}s`
  });

  // Move back to Needs_Action
  await fs.writeFile(taskPath, JSON.stringify(task, null, 2));
  await fs.rename(taskPath, `${VAULT_PATH}/Needs_Action/${taskId}.json`);

  await appendToLog('claims.log', {
    task_id: taskId,
    action: 'reclaim',
    previous_owner: previousOwner,
    staleness_ms: staleness,
    reclaimed_at: new Date().toISOString()
  });

  console.log(`Reclaimed stale task: ${taskId} from ${previousOwner}`);

  return { reclaimed: true, previous_owner: previousOwner };
}
```

### Operation: Release Claim

**Purpose:** Agent voluntarily releases task (completed or aborted)

**Preconditions:**
- Task in In_Progress/ claimed by this agent
- Agent has permission to release

**Steps:**
1. Read task from In_Progress/
2. Validate agent owns task (claimed_by = agent_name)
3. Update task metadata:
   - Delete claimed_by, claimed_at, claim_expires_at, last_heartbeat fields
   - Append to claim_history: { action: "release", reason }
4. Move task based on reason:
   - If completed: move to Done/
   - If aborted: move to Needs_Action/
5. Stop heartbeat updates
6. Log release event

**Postconditions:**
- Task moved to appropriate folder
- Claim released
- Release event logged

**Error Handling:**
- If agent doesn't own task: reject with error
- If file move fails: log error, retry

**Example:**
```javascript
async function releaseClaim(taskId, agentName, reason = 'completed') {
  const taskPath = `${VAULT_PATH}/In_Progress/${taskId}.json`;
  const task = JSON.parse(await fs.readFile(taskPath, 'utf-8'));

  if (task.claimed_by !== agentName) {
    throw new Error(`Task not owned by ${agentName}`);
  }

  // Release claim
  delete task.claimed_by;
  delete task.claimed_at;
  delete task.claim_expires_at;
  delete task.last_heartbeat;
  delete task.claim_id;

  task.claim_history.push({
    agent: agentName,
    action: 'release',
    timestamp: new Date().toISOString(),
    reason: reason
  });

  // Determine target folder
  const targetFolder = reason === 'completed' ? 'Done' : 'Needs_Action';
  const targetPath = `${VAULT_PATH}/${targetFolder}/${taskId}.json`;

  await fs.writeFile(taskPath, JSON.stringify(task, null, 2));
  await fs.rename(taskPath, targetPath);

  // Stop heartbeat
  stopHeartbeat(taskId);

  await appendToLog('claims.log', {
    task_id: taskId,
    action: 'release',
    agent: agentName,
    reason: reason,
    released_at: new Date().toISOString()
  });

  console.log(`Claim released: ${taskId} by ${agentName} (${reason})`);

  return { success: true };
}
```

## Integration with Existing Skills

### With vault_state_manager

- Delegates low-level file operations to vault_state_manager
- Uses vault_state_manager's atomic move operations for claims
- Enforces vault_state_manager's permission system

### With task_lifecycle_manager

- Claim operations integrate with lifecycle state transitions
- Claiming task triggers state change: needs_action → in_progress
- Releasing task triggers state change: in_progress → done (or back to needs_action)

### With agent_delegation_manager

- Claim conflicts can trigger delegation to higher-priority agent
- Delegation signals respect claim ownership (only owner can delegate)

## Gotchas & Edge Cases

See `references/gotchas.md` for detailed edge case handling:
- Clock skew causing premature reclaims
- Network filesystem atomicity issues
- Heartbeat update failures
- Conflict detection race conditions
- Agent permission validation edge cases
- Orphaned claims after crashes

## Success Metrics

- **Claim success rate**: % of claim attempts that succeed
- **Conflict rate**: % of claims that result in conflicts
- **Reclaim rate**: % of tasks reclaimed due to stale heartbeat
- **Conflict resolution time**: Average time to resolve conflicts
- **Heartbeat failure rate**: % of heartbeat updates that fail

## Testing Checklist

- [ ] Claim unclaimed task (success)
- [ ] Claim already-claimed task (conflict)
- [ ] Detect stale claim (heartbeat timeout)
- [ ] Reclaim stale task (automatic)
- [ ] Resolve conflict (first_claim_wins)
- [ ] Resolve conflict (agent_priority)
- [ ] Resolve conflict (human_resolve)
- [ ] Release claim (completed)
- [ ] Release claim (aborted)
- [ ] Validate agent permissions
- [ ] Handle concurrent claim attempts
- [ ] Handle heartbeat update failures
- [ ] Handle clock skew between agents

---

**Related Skills:**
- `vault_state_manager` - Low-level vault operations
- `task_lifecycle_manager` - Task state transitions
- `agent_delegation_manager` - Cross-agent coordination

**Related Documents:**
- `AGENTS.md` - Agent roles and permissions
- `VAULT_SKILLS_INTEGRATION.md` - Skill integration patterns
