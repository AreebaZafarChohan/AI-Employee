# Agent Claim Coordinator

Ensure no two agents work the same task, handle conflicts. Inspects In_Progress folders and resolves claims based on timestamps and rules.

## Overview

The Agent Claim Coordinator prevents duplicate work by ensuring only one agent can claim and work on a task at any given time. It detects claim conflicts, resolves them using configurable policies, and automatically reclaims tasks from crashed or stuck agents.

## Key Features

- **Claim-by-Move**: Atomic task claiming via filesystem rename
- **Heartbeat Protocol**: Detect crashed agents via stale heartbeat
- **Conflict Detection**: Identify competing claims
- **Multiple Resolution Policies**: first_claim_wins, agent_priority, human_resolve
- **Automatic Reclaim**: Recover tasks from dead agents
- **Graceful Degradation**: Handle unresolvable conflicts
- **Audit Trail**: Complete claim history in task metadata

## Quick Start

### 1. Configure

```bash
# Copy configuration template
cp .claude/skills/coordination/agent_claim_coordinator/assets/.env.example .env

# Edit configuration
VAULT_PATH="/path/to/vault"
CLAIM_RESOLUTION_POLICY="first_claim_wins"
CLAIM_TIMEOUT_MS="300000"  # 5 minutes
CLAIM_HEARTBEAT_INTERVAL_MS="30000"  # 30 seconds
```

### 2. Claim a Task

```javascript
const { claimTask } = require('./agent_claim_coordinator');

// Agent attempts to claim task
const result = await claimTask('task-123', 'lex');

if (result.success) {
  console.log(`Claimed task-123 with claim_id: ${result.claim_id}`);

  // Start heartbeat updates
  const heartbeat = setInterval(async () => {
    await updateHeartbeat('task-123', 'lex');
  }, 30000);

  // Do work...
  await processTask('task-123');

  // Release claim when done
  clearInterval(heartbeat);
  await releaseClaim('task-123', 'lex', 'completed');

} else {
  console.log(`Claim failed: ${result.reason}`);
}
```

### 3. Run Conflict Detection

```javascript
// Coordinator checks for conflicts periodically
setInterval(async () => {
  const conflicts = await detectConflicts();

  for (const conflict of conflicts) {
    console.log(`Conflict detected: ${conflict.task_id}`);
    await resolveConflict(conflict);
  }
}, 60000); // Every minute
```

### 4. Monitor Claims

```bash
# View claim log
tail -f "${VAULT_PATH}/Logs/claims.log"

# View conflicts
tail -f "${VAULT_PATH}/Logs/claim_conflicts.log"

# Check current claims
find "${VAULT_PATH}/In_Progress" -name "*.json" -exec jq -r '.claimed_by' {} \;
```

## Core Concepts

### Claim Metadata

Every claimed task has:

```json
{
  "task_id": "task-123",
  "claimed_by": "lex",
  "claimed_at": "2025-01-15T10:00:00.000Z",
  "claim_expires_at": "2025-01-15T10:05:00.000Z",
  "last_heartbeat": "2025-01-15T10:02:30.000Z",
  "claim_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "claim_history": [
    {
      "agent": "lex",
      "action": "claim",
      "timestamp": "2025-01-15T10:00:00.000Z",
      "claim_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    }
  ]
}
```

### Heartbeat Protocol

Agents update `last_heartbeat` every 30 seconds to prove they're alive:

```javascript
// Agent updates heartbeat while working
setInterval(async () => {
  const task = await readTaskFile(`In_Progress/${taskId}.json`);
  task.last_heartbeat = new Date().toISOString();
  await writeTaskFile(`In_Progress/${taskId}.json`, task);
}, CLAIM_HEARTBEAT_INTERVAL_MS);

// Coordinator checks for stale heartbeats
if (Date.now() - new Date(task.last_heartbeat).getTime() > CLAIM_TIMEOUT_MS) {
  await reclaimStaleTask(task.task_id);
}
```

### Conflict Resolution Policies

**first_claim_wins**: Agent with earliest `claimed_at` timestamp wins

```javascript
// Agent A claimed at 10:00:00
// Agent B claimed at 10:00:05
// Winner: Agent A (earlier timestamp)
```

**agent_priority**: Agent with highest priority wins

```env
AGENT_PRIORITIES="orch:1,lex:2,cex:3,watcher:4"
```

```javascript
// Agent lex (priority 2) vs Agent cex (priority 3)
// Winner: lex (lower number = higher priority)
```

**human_resolve**: Escalate to human for manual resolution

```javascript
// Creates conflict marker file
// Freezes task until human resolves
// Notifies human via configured method
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Claim Coordinator                 │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Conflict Detection                                │ │
│  │  • Scan In_Progress/ for conflicts                 │ │
│  │  • Detect stale heartbeats                         │ │
│  │  • Identify competing claims                       │ │
│  └────────────────────────────────────────────────────┘ │
│                         ↓                                │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Conflict Resolution                               │ │
│  │  • Apply resolution policy                         │ │
│  │  • Determine winner                                │ │
│  │  • Notify losing agents                            │ │
│  └────────────────────────────────────────────────────┘ │
│                         ↓                                │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Reclaim Management                                │ │
│  │  • Reclaim stale tasks                             │ │
│  │  • Move back to Needs_Action/                      │ │
│  │  • Log reclaim events                              │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                         ↕
        ┌────────────────────────────────┐
        │  Vault (In_Progress/ folder)   │
        │  • Task files with claim data  │
        │  • Atomic file operations      │
        └────────────────────────────────┘
```

## Operations

### Claim Task

```javascript
async function claimTask(taskId, agentName) {
  const task = await readTaskFile(`Needs_Action/${taskId}.json`);

  // Validate preconditions
  if (task.claimed_by) throw new Error('Already claimed');
  if (!canAgentClaimTask(agentName, task)) throw new Error('Permission denied');

  // Update claim metadata
  const claimId = uuidv4();
  task.claimed_by = agentName;
  task.claimed_at = new Date().toISOString();
  task.claim_expires_at = new Date(Date.now() + CLAIM_TIMEOUT_MS).toISOString();
  task.last_heartbeat = new Date().toISOString();
  task.claim_id = claimId;
  task.claim_history.push({ agent: agentName, action: 'claim', timestamp: new Date().toISOString(), claim_id: claimId });

  // Atomic move to In_Progress
  await atomicMove(`Needs_Action/${taskId}.json`, `In_Progress/${taskId}.json`);

  return { success: true, claim_id: claimId };
}
```

### Detect Conflicts

```javascript
async function detectConflicts() {
  const conflicts = [];
  const tasks = await listTasksInProgress();

  for (const task of tasks) {
    // Check for stale heartbeat
    const staleness = Date.now() - new Date(task.last_heartbeat).getTime();
    if (staleness > CLAIM_TIMEOUT_MS) {
      conflicts.push({ task_id: task.task_id, type: 'stale_claim', owner: task.claimed_by, staleness_ms: staleness });
    }

    // Check for multiple competing claims
    const recentClaims = task.claim_history.filter(h => h.action === 'claim' && new Date(h.timestamp).getTime() > Date.now() - CLAIM_TIMEOUT_MS);
    if (recentClaims.length > 1) {
      const competingAgents = [...new Set(recentClaims.map(c => c.agent))];
      conflicts.push({ task_id: task.task_id, type: 'multiple_claims', competing_agents: competingAgents });
    }
  }

  return conflicts;
}
```

### Resolve Conflict

```javascript
async function resolveConflict(conflict) {
  const task = await readTaskFile(`In_Progress/${conflict.task_id}.json`);
  const policy = process.env.CLAIM_RESOLUTION_POLICY || 'first_claim_wins';

  let winner, losers;

  if (policy === 'first_claim_wins') {
    ({ winner, losers } = resolveByFirstClaim(task, conflict.competing_agents));
  } else if (policy === 'agent_priority') {
    ({ winner, losers } = resolveByPriority(task, conflict.competing_agents));
  } else if (policy === 'human_resolve') {
    return escalateToHuman(task, conflict.competing_agents);
  }

  // Update task
  task.claimed_by = winner;
  task.conflict = { detected: true, detected_at: conflict.detected_at, competing_agents: conflict.competing_agents, resolution_policy: policy, resolved_by: winner, resolved_at: new Date().toISOString() };
  task.claim_history.push({ agent: winner, action: 'conflict_resolved', timestamp: new Date().toISOString(), policy: policy, losers: losers });

  await writeTaskFile(`In_Progress/${conflict.task_id}.json`, task);

  return { success: true, winner, losers };
}
```

### Reclaim Stale Task

```javascript
async function reclaimStaleTask(taskId) {
  const task = await readTaskFile(`In_Progress/${taskId}.json`);
  const staleness = Date.now() - new Date(task.last_heartbeat).getTime();

  if (staleness <= CLAIM_TIMEOUT_MS) return { reclaimed: false, reason: 'claim_still_active' };

  const previousOwner = task.claimed_by;

  // Release claim
  delete task.claimed_by;
  delete task.claimed_at;
  delete task.claim_expires_at;
  delete task.last_heartbeat;
  delete task.claim_id;

  task.claim_history.push({ agent: previousOwner, action: 'reclaimed_stale', timestamp: new Date().toISOString(), staleness_ms: staleness });

  // Move back to Needs_Action
  await atomicMove(`In_Progress/${taskId}.json`, `Needs_Action/${taskId}.json`);

  return { reclaimed: true, previous_owner: previousOwner };
}
```

## Monitoring

### Metrics

- **Claim success rate**: % of claim attempts that succeed
- **Conflict rate**: % of claims that result in conflicts
- **Reclaim rate**: % of tasks reclaimed due to stale heartbeat
- **Conflict resolution time**: Average time to resolve conflicts
- **Heartbeat failure rate**: % of heartbeat updates that fail

### Logs

```bash
# View claims
tail -f logs/claims.log

# View conflicts
tail -f logs/claim_conflicts.log

# View reclaims
tail -f logs/reclaims.log
```

### Alerts

```yaml
- name: high_conflict_rate
  condition: conflict_rate > 10%
  action: notify_admin

- name: high_reclaim_rate
  condition: reclaim_rate > 5%
  action: investigate_agent_health

- name: heartbeat_cascade_failure
  condition: heartbeat_failure_rate > 50%
  action: page_oncall
```

## Troubleshooting

### High Conflict Rate

**Symptom**: Many conflicts detected

**Causes**:
- Multiple agents competing for same tasks
- Claim thrashing (repeated conflicts)

**Debug**:
```bash
# Check conflict log
cat logs/claim_conflicts.log | jq '.competing_agents' | sort | uniq -c

# Enable backoff
echo 'CONFLICT_BACKOFF_BASE_MS="1000"' >> .env
```

### High Reclaim Rate

**Symptom**: Many tasks reclaimed

**Causes**:
- Agents crashing frequently
- Heartbeat updates failing
- Claim timeout too short

**Debug**:
```bash
# Check reclaim log
cat logs/reclaims.log | jq '.previous_owner' | sort | uniq -c

# Increase timeout
echo 'CLAIM_TIMEOUT_MS="600000"' >> .env  # 10 minutes
```

### Stale Heartbeats

**Symptom**: Tasks stuck in In_Progress with old heartbeat

**Causes**:
- Agent stopped updating heartbeat
- Filesystem write failures
- Network issues

**Debug**:
```bash
# Check heartbeat ages
find "${VAULT_PATH}/In_Progress" -name "*.json" -exec jq -r '"\(.task_id): \(.last_heartbeat)"' {} \;

# Enable automatic reclaim
echo 'ENABLE_AUTOMATIC_RECLAIM="true"' >> .env
```

## Best Practices

1. **Always update heartbeat** while working on task
2. **Release claims explicitly** when done (don't rely on timeout)
3. **Validate ownership** before critical actions
4. **Use backoff** after conflict losses
5. **Monitor logs** for unexpected conflicts
6. **Configure priorities** based on agent capabilities
7. **Test on local filesystem** before deploying to network filesystem
8. **Enable NTP sync** to prevent clock skew

## Related Skills

- [vault_state_manager](../vault/vault_state_manager/) - Low-level vault operations
- [task_lifecycle_manager](../vault/task_lifecycle_manager/) - Task state transitions
- [agent_delegation_manager](./agent_delegation_manager/) - Cross-agent coordination

## Related Documents

- [SKILL.md](./SKILL.md) - Complete skill specification
- [patterns.md](./references/patterns.md) - Design patterns
- [gotchas.md](./references/gotchas.md) - Edge cases and mitigations
- [impact-checklist.md](./references/impact-checklist.md) - Deployment checklist

## License

This skill is part of the AI-Employee project. See LICENSE file for details.
