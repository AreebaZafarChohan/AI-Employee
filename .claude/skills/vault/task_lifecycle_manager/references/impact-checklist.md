# Task Lifecycle Manager Impact Checklist

This checklist ensures correct task lifecycle management across all deployment environments.

---

## State Machine Compliance Checklist

### Transition Rules

- [ ] **All transitions follow state machine** (no invalid jumps)
- [ ] **Illegal transitions rejected** with clear error messages
- [ ] **Agent permissions checked** before every transition
- [ ] **Transitions logged** to audit trail
- [ ] **Metadata updated** on every transition (status, last_transition)

### State Machine Tests

- [ ] **needs_action → planned**: Agent can claim task
- [ ] **needs_action → X**: Cannot skip to other states directly
- [ ] **planned → in_progress**: Agent can start work
- [ ] **planned → rejected**: Agent can reject invalid tasks
- [ ] **in_progress → pending_approval**: Agent can request approval
- [ ] **in_progress → needs_action**: Agent can retry failed tasks
- [ ] **in_progress → done**: Only via approved stage (cannot skip)
- [ ] **pending_approval → approved**: Only human can approve
- [ ] **pending_approval → rejected**: Only human can reject
- [ ] **approved → in_progress**: Orchestrator can claim for execution
- [ ] **rejected → archive**: Human can clean up
- [ ] **done → archive**: Human can clean up old tasks

---

## Claim Semantics Checklist

### Claim-by-Move Enforcement

- [ ] **Atomic file move** for claim (no copy+delete)
- [ ] **First mover wins** (FileNotFoundError for second agent)
- [ ] **Claim ownership recorded** in task metadata (claimed_by, claimed_at)
- [ ] **Claim failure handled** gracefully (not considered error)
- [ ] **No double claims** possible

### Claim Validation

- [ ] **Task exists** before claim attempt
- [ ] **Task is valid JSON** (not corrupted)
- [ ] **Task has required fields** (plan_id, status, title, etc.)
- [ ] **Agent has permission** to claim task type
- [ ] **Task not already in progress** (no re-claiming)

### Claim Conflict Scenarios

- [ ] **Two agents claim same task**: First succeeds, second gets `already_claimed`
- [ ] **Agent crashes mid-claim**: Task stuck in Plans/ (recovered by stale claim job)
- [ ] **Task file deleted**: Claim fails with `FileNotFoundError`
- [ ] **Task file corrupted**: Claim fails with `invalid_task`

---

## Retry Logic Checklist

### Retry Configuration

- [ ] **Max retries configurable** via `TASK_MAX_RETRIES` (default: 3)
- [ ] **Backoff strategy** uses exponential backoff
- [ ] **Retry metadata tracked** (attempts, last_error, first_failure_at)
- [ ] **Next retry time calculated** and recorded

### Retry Behavior

- [ ] **Transient errors trigger retry** (move back to Needs_Action)
- [ ] **Permanent errors reject task** (move to Rejected)
- [ ] **Max retries exceeded** → task permanently failed
- [ ] **Retry counter preserved** across attempts
- [ ] **Error history preserved** for debugging

### Retry Tests

- [ ] Task fails once → retries
- [ ] Task fails twice → retries
- [ ] Task fails 3 times (max) → rejected
- [ ] Task succeeds after retry → completed
- [ ] Retry delay increases exponentially

---

## Conflict Resolution Checklist

### Stale Claim Recovery

- [ ] **Stale threshold configurable** (default: 60 minutes)
- [ ] **Periodic recovery job runs** (every 5-10 minutes)
- [ ] **Stale tasks moved back** to Needs_Action
- [ ] **Stale recovery logged** with original owner info
- [ ] **Stale metadata preserved** for audit

### Orphaned Task Recovery

- [ ] **Orphan threshold configurable** (default: 30 minutes)
- [ ] **Orphaned tasks detected** (In_Progress + no updates)
- [ ] **Orphaned tasks moved back** to Needs_Action
- [ ] **Orphan recovery logged** with reason
- [ ] **Heartbeat mechanism** (optional) for liveness detection

### Duplicate Detection

- [ ] **Duplicate task IDs detected** across folders
- [ ] **Oldest task kept** when duplicates found
- [ ] **Duplicate tasks rejected** with -duplicate suffix
- [ ] **Duplicate resolution logged**

### Corrupted File Handling

- [ ] **Corrupted files detected** (JSON parse fails)
- [ ] **Corrupted files moved** to Rejected/
- [ ] **Rejection reason added** (corruption details)
- [ ] **Corruption logged** for investigation

---

## Audit Trail Checklist

### Logging Requirements

- [ ] **All transitions logged** (who, what, when, why)
- [ ] **Log format is JSON** (structured, parseable)
- [ ] **Timestamps in ISO 8601** (UTC)
- [ ] **Agent identity recorded** in every log entry
- [ ] **Reason field included** for failures/rejections

### Log Content

- [ ] Task ID
- [ ] Previous state
- [ ] New state
- [ ] Timestamp
- [ ] Agent name
- [ ] Reason (if applicable)
- [ ] Error details (if failure)

### Log Security

- [ ] **Sensitive data sanitized** (no secrets, PII in logs)
- [ ] **Logs append-only** (no editing)
- [ ] **Logs size-bounded** (rotation configured)
- [ ] **Logs backed up** separately from vault

---

## Performance Checklist

### Polling Efficiency

- [ ] **Polling interval reasonable** (5-60 seconds, not milliseconds)
- [ ] **No busy-wait loops** (use setTimeout)
- [ ] **Batch processing** where possible
- [ ] **List operations cached** (don't list every second)

### Recovery Job Efficiency

- [ ] **Recovery jobs run periodically** (not continuously)
- [ ] **Recovery job interval configurable**
- [ ] **Recovery jobs don't block main loop**
- [ ] **Recovery jobs have timeout**
- [ ] **Recovery jobs log performance metrics**

### Memory Management

- [ ] **Task objects released** after processing
- [ ] **No memory leaks** in long-running agents
- [ ] **File handles closed** properly
- [ ] **Large files not loaded into memory** (stream if needed)

---

## Security Checklist

### Agent Permission Enforcement

- [ ] **lex cannot approve own tasks** (must go to Pending_Approval)
- [ ] **orch cannot create new tasks** (only execute approved)
- [ ] **cex cannot execute tasks** (read-only)
- [ ] **Watchers cannot claim tasks** (only write to Needs_Action)
- [ ] **Human has override authority** (can move anywhere)

### Task Ownership

- [ ] **Owner tracked** in metadata (claimed_by)
- [ ] **Only owner can update** task in In_Progress
- [ ] **Ownership transfer** only via state transition
- [ ] **Ownership logged** in audit trail

### Data Sanitization

- [ ] **Secrets never in task metadata** (use references)
- [ ] **PII redacted** in logs
- [ ] **Error messages sanitized** (no internal paths)
- [ ] **Task metadata validated** before logging

---

## Integration Checklist

### Vault State Manager Integration

- [ ] **Uses vault_state_manager** for all file operations
- [ ] **Path validation** delegated to vault manager
- [ ] **Permission checks** delegated to vault manager
- [ ] **No direct filesystem calls**

### AGENTS.md Compliance

- [ ] **Follows jurisdictions** defined in AGENTS.md §3
- [ ] **Implements claim-by-move** per AGENTS.md §4.2
- [ ] **Enforces single-writer** per AGENTS.md §4.3
- [ ] **Avoids conflicts** per AGENTS.md §4.4
- [ ] **Maintains idempotency** per AGENTS.md §4.5

### Watcher Integration

- [ ] **Processes watcher outputs** from Needs_Action/
- [ ] **Handles watcher formats** (emails, messages, files, alerts)
- [ ] **Validates watcher metadata**

### Orchestrator Integration

- [ ] **Orchestrator polls Approved/**
- [ ] **Orchestrator claims via lifecycle manager**
- [ ] **Orchestrator reports results** (success/failure)
- [ ] **Orchestrator moves to Done/**

---

## Failure Scenario Checklist

### Agent Crashes

- [ ] **Agent crash during claim**: Task recovered by stale claim job
- [ ] **Agent crash during work**: Task recovered by orphan job
- [ ] **Agent crash during transition**: Partial state detected and fixed

### Filesystem Errors

- [ ] **Disk full**: Tasks queue safely, alert triggered
- [ ] **Permission denied**: Error logged, task moved to Rejected
- [ ] **File locked**: Retry with backoff
- [ ] **Filesystem unmounted**: Agents halt gracefully

### Network Errors (for orchestrator)

- [ ] **MCP server down**: Task retries automatically
- [ ] **API timeout**: Task retries with backoff
- [ ] **Rate limit hit**: Task retries after delay

### Data Errors

- [ ] **Corrupted JSON**: Task moved to Rejected
- [ ] **Missing fields**: Task rejected with reason
- [ ] **Invalid state**: Task rejected with reason

---

## Testing Checklist

### Unit Tests

- [ ] **Test all state transitions** (legal and illegal)
- [ ] **Test claim conflicts** (concurrent claims)
- [ ] **Test retry logic** (transient vs permanent failures)
- [ ] **Test recovery jobs** (stale, orphaned, duplicates)
- [ ] **Test error handling** (all error types)

### Integration Tests

- [ ] **Test full lifecycle** (Needs_Action → Done)
- [ ] **Test human approval flow** (Pending_Approval → Approved)
- [ ] **Test rejection flow** (any stage → Rejected)
- [ ] **Test concurrent agents** (multiple lex instances)
- [ ] **Test orchestrator execution** (Approved → Done)

### Failure Tests

- [ ] **Test agent crash recovery**
- [ ] **Test disk full scenario**
- [ ] **Test corrupted files**
- [ ] **Test max retries exceeded**
- [ ] **Test stale claim recovery**
- [ ] **Test orphaned task recovery**

---

## Deployment Checklist

### Pre-Deployment

- [ ] **Configuration validated** (TASK_* variables set)
- [ ] **Recovery jobs enabled** (stale claim, orphan)
- [ ] **Polling intervals set** appropriately
- [ ] **Max retries configured** (default: 3)
- [ ] **Audit logging enabled**

### Post-Deployment

- [ ] **Tasks flowing through lifecycle** (Needs_Action → Done)
- [ ] **No tasks stuck** in intermediate stages
- [ ] **Recovery jobs running** (check logs)
- [ ] **Audit trail complete** (all transitions logged)
- [ ] **No permission errors** in logs

### Monitoring

- [ ] **Track task counts** per stage (gauge metric)
- [ ] **Track transition latency** (histogram)
- [ ] **Track retry rate** (counter)
- [ ] **Track recovery job effectiveness** (stale/orphan counts)
- [ ] **Track error rates** (by type)

---

## Maintenance Checklist

### Daily

- [ ] **Check for stuck tasks** (In_Progress > 1 hour)
- [ ] **Review error logs** (failures, rejections)
- [ ] **Monitor task throughput** (tasks/hour)

### Weekly

- [ ] **Run full health check** (stale, orphan, duplicate detection)
- [ ] **Review retry patterns** (are retries effective?)
- [ ] **Review rejection reasons** (fix common issues)
- [ ] **Archive old Done tasks** (move to Archive/)

### Monthly

- [ ] **Review lifecycle metrics** (average time per stage)
- [ ] **Optimize slow transitions** (if latency increasing)
- [ ] **Update recovery thresholds** (if needed)
- [ ] **Clean up Archive/** (compress or delete old tasks)

---

## Sign-Off

Before deploying Task Lifecycle Manager to production, verify:

- [ ] **All state machine tests passed**
- [ ] **Claim semantics validated**
- [ ] **Retry logic tested**
- [ ] **Recovery jobs functional**
- [ ] **Audit trail complete**
- [ ] **Integration tests passed**
- [ ] **Documentation updated**
- [ ] **Team trained on workflows**

**Deployment Approved By:** _______________
**Date:** _______________
**Environment:** _______________
