# Error Recovery Planner - Impact Checklist

Use this checklist when deploying or modifying the Error Recovery Planner skill to ensure all impacts are considered.

---

## Environment Configuration Impact

### Required Configuration

- [ ] `VAULT_PATH` is set and points to valid directory
- [ ] `Recovery_Plans/` folder exists (or will be auto-created)
- [ ] Agent has write permissions to `Recovery_Plans/` folder
- [ ] `RECOVERY_MAX_RETRIES` is set to reasonable value (default: 3)
- [ ] `RECOVERY_MAX_BACKOFF_MS` is set to cap exponential growth (recommended: 300000ms / 5min)

### Optional Configuration (Review Defaults)

- [ ] `RECOVERY_BASE_BACKOFF_MS` appropriate for your use case (default: 1000ms)
- [ ] `RECOVERY_JITTER_FACTOR` configured (0.0 for dev, 0.2-0.3 for prod)
- [ ] `RECOVERY_STRATEGY` matches your error patterns (exponential | linear | fibonacci)
- [ ] `RECOVERY_ESCALATE_AFTER_ATTEMPTS` aligns with support capacity (default: 3)
- [ ] `RECOVERY_AUTO_ABANDON_THRESHOLD` prevents infinite retries (default: 5)
- [ ] `RECOVERY_TRANSIENT_ERROR_PATTERNS` includes your application-specific errors
- [ ] `RECOVERY_PERMANENT_ERROR_PATTERNS` includes your application-specific errors
- [ ] `RECOVERY_RETRY_HTTP_CODES` matches your API error handling

### Secrets Management

- [ ] Confirmed no secrets in recovery plan templates
- [ ] Error sanitization enabled (default: yes)
- [ ] Verified sensitive data patterns in `sanitizeError()` function
- [ ] Audit logs don't contain credentials or tokens
- [ ] Recovery plans stored in plaintext (acceptable - no secrets)

---

## Network & Service Dependencies Impact

### Service Topology

- [ ] Recovery planner operates on local filesystem only (no network)
- [ ] No ports required
- [ ] No external API calls
- [ ] Integration with `task_lifecycle_manager` confirmed (file-based)
- [ ] Integration with `vault_state_manager` confirmed (file-based)

### Concurrency

- [ ] Multiple agents can create recovery plans concurrently (atomic file writes)
- [ ] Recovery plans are read-only after creation (no conflicts)
- [ ] Lock files used if needed (optional, see gotchas.md #12)
- [ ] Thundering herd prevention configured (jitter enabled)
- [ ] Retry storms mitigated (exponential backoff, jitter)

### Containerization

- [ ] Vault mounted as read-write volume in container
- [ ] `Recovery_Plans/` folder writable from container
- [ ] No host network access required
- [ ] Environment variables passed to container
- [ ] No persistent storage beyond vault mount

---

## Authentication & Authorization Impact

### Access Control

- [ ] All agents can read recovery plans (no restrictions)
- [ ] All agents can write recovery plans (no restrictions)
- [ ] Only task owner can execute recovery actions (enforced by task lifecycle)
- [ ] Humans can review/override recovery plans (manual file edits)

### Audit Trail

- [ ] All recovery plans logged with agent identity
- [ ] Timestamps recorded in ISO 8601 format (UTC)
- [ ] Error classification logged for analysis
- [ ] Retry attempts tracked in plan metadata
- [ ] Escalation decisions logged with reason

---

## Performance & Resource Impact

### Disk Usage

- [ ] Recovery plans accumulate over time (cleanup strategy required)
- [ ] Each plan is small (~2-5 KB JSON file)
- [ ] Estimated disk usage: `<num_failures_per_day>` × 3 KB × 30 days
- [ ] Cleanup job scheduled (archive plans older than 30 days)
- [ ] Archived plans moved to separate folder

### Compute Impact

- [ ] Recovery planning is lightweight (< 10ms per call)
- [ ] No CPU-intensive operations
- [ ] Backoff calculations are O(1) complexity
- [ ] Error classification uses regex matching (fast)

### Memory Impact

- [ ] Recovery plans not kept in memory (written to disk immediately)
- [ ] No caching of plans (stateless operation)
- [ ] Error messages truncated to 500 characters (prevents large logs)

---

## Error Handling & Resilience Impact

### Failure Modes

- [ ] Recovery planner itself can fail (handle gracefully)
  - [ ] Fallback: use default retry logic if planning fails
  - [ ] Log planning failures separately from task failures
- [ ] Invalid error objects handled (missing fields, malformed)
  - [ ] Validation: check required fields before classification
  - [ ] Fallback: default to ambiguous classification
- [ ] File write failures handled (disk full, permissions)
  - [ ] Retry: attempt to write plan 3 times
  - [ ] Escalate: if plan can't be written, escalate task immediately

### Edge Cases

- [ ] Error with no message or code (handled)
- [ ] Duplicate recovery plans for same task (prevented or merged)
- [ ] Concurrent plan creation (atomic operations)
- [ ] Missing environment variables (defaults used)
- [ ] Invalid backoff strategy (fallback to exponential)

---

## Operational Readiness Impact

### Monitoring

- [ ] Track recovery plan creation rate (alerting if spike)
- [ ] Monitor retry success rate (are retries resolving issues?)
- [ ] Alert on escalation rate (high rate = systemic issue)
- [ ] Track backoff duration distribution (are delays appropriate?)
- [ ] Monitor disk usage for `Recovery_Plans/` folder

### Alerting

- [ ] Alert if recovery plan creation fails
- [ ] Alert if `RECOVERY_AUTO_ABANDON_THRESHOLD` reached (persistent failures)
- [ ] Alert if escalation queue grows > 50 tasks (support bottleneck)
- [ ] Alert if same error type occurs > 100 times (systemic issue)

### Runbooks

- [ ] Document how to manually retry failed task
- [ ] Document how to adjust retry limits for specific task
- [ ] Document how to force escalation (bypass retry)
- [ ] Document how to analyze recovery plan history
- [ ] Document cleanup procedure for old recovery plans

---

## Integration Impact

### Upstream Dependencies

- [ ] `task_lifecycle_manager` must be available
- [ ] `vault_state_manager` must be initialized
- [ ] Task metadata must include `retry_metadata` field
- [ ] Error objects must follow standard format (message, code, status)

### Downstream Consumers

- [ ] Agents must read and execute recovery plans (not automatic)
- [ ] Orchestrator must honor backoff schedules (wait before retry)
- [ ] Humans must review escalated tasks (approval workflow)
- [ ] Dashboard should display recovery statistics (optional)

### Breaking Changes

- [ ] New environment variables (graceful defaults provided)
- [ ] Recovery plan schema changes (version field included)
- [ ] File naming conventions (backward compatible)

---

## Testing Impact

### Unit Tests

- [ ] Test error classification (transient, permanent, ambiguous)
- [ ] Test backoff strategies (exponential, linear, fibonacci)
- [ ] Test sanitization (sensitive data removed)
- [ ] Test retry limit enforcement (max retries respected)
- [ ] Test escalation triggers (immediate for permanent errors)

### Integration Tests

- [ ] Test with `task_lifecycle_manager` (full workflow)
- [ ] Test concurrent plan creation (race conditions)
- [ ] Test file persistence (plans written correctly)
- [ ] Test plan retrieval and execution

### Load Tests

- [ ] Test with 100+ simultaneous failures (no bottleneck)
- [ ] Test recovery plan disk usage (cleanup works)
- [ ] Test retry storms (jitter prevents thundering herd)

---

## Migration Impact

### New Installation

- [ ] Recovery planner can be added without affecting existing tasks
- [ ] No database migrations required
- [ ] No schema changes to task files
- [ ] Environment variables have safe defaults

### Version Upgrade

- [ ] Recovery plan schema versioned (forward compatible)
- [ ] Old plans still readable after upgrade
- [ ] New fields added with defaults (backward compatible)

### Rollback

- [ ] Can disable recovery planner (fall back to old retry logic)
- [ ] Recovery plans can be ignored (no breaking dependencies)
- [ ] Remove environment variables to disable feature

---

## Security Impact

### Data Protection

- [ ] Sensitive data sanitized before logging
- [ ] Recovery plans don't contain credentials
- [ ] Error messages don't leak system internals
- [ ] File permissions restrict access to vault folder

### Denial of Service

- [ ] Retry storms prevented (exponential backoff + jitter)
- [ ] Max retries enforced (hard cap)
- [ ] Disk usage bounded (cleanup job)
- [ ] No infinite loops (abandon threshold)

### Audit & Compliance

- [ ] All recovery decisions logged
- [ ] Agent identity tracked for accountability
- [ ] Timestamps recorded for forensics
- [ ] Recovery plans retained for compliance period (configurable)

---

## Documentation Impact

### User-Facing Docs

- [ ] Recovery planner usage documented in README
- [ ] Environment variables documented
- [ ] Examples provided (see `patterns.md`)
- [ ] Integration guide for agents

### Internal Docs

- [ ] Architecture decision recorded (ADR)
- [ ] Design rationale documented
- [ ] Known limitations listed (see `gotchas.md`)
- [ ] Anti-patterns documented

---

## Summary Checklist

### Pre-Deployment (Must Complete)

- [ ] Environment variables configured
- [ ] `Recovery_Plans/` folder created
- [ ] Agent permissions verified
- [ ] Sensitive data sanitization tested
- [ ] Integration with task lifecycle confirmed

### Post-Deployment (Monitor)

- [ ] Recovery plan creation rate normal
- [ ] Retry success rate acceptable (> 50%)
- [ ] Escalation rate manageable (< 10%)
- [ ] Disk usage stable (cleanup working)
- [ ] No errors in recovery planner logs

### Ongoing Maintenance

- [ ] Review recovery statistics weekly
- [ ] Adjust retry limits based on success rate
- [ ] Update error patterns as new errors discovered
- [ ] Archive old recovery plans monthly
- [ ] Update documentation with lessons learned

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Retry storms** | Medium | High | Exponential backoff + jitter |
| **Disk space exhaustion** | Low | Medium | Cleanup job (30-day retention) |
| **Sensitive data leak** | Low | High | Error sanitization (enabled by default) |
| **Recovery plan conflicts** | Low | Low | Atomic file writes |
| **Planning failures** | Low | Medium | Fallback to default retry logic |
| **Escalation bottleneck** | Medium | Medium | Prioritize high-priority tasks |
| **Misclassified errors** | Medium | Low | Conservative retry limits |

**Overall Risk Level:** LOW (with proper configuration)

---

## Approval Signatures

- [ ] **Engineer:** Code reviewed and tested
- [ ] **Architect:** Design approved and documented
- [ ] **Security:** Sanitization and audit verified
- [ ] **Operations:** Monitoring and runbooks ready
- [ ] **Product:** Use cases validated

**Deployment Approved By:** ________________
**Date:** ________________
