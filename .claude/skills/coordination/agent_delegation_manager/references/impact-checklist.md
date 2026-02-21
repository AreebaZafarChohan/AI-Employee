# Impact Checklist for Agent Delegation Manager

Use this checklist before deploying or modifying the agent_delegation_manager skill to assess operational impact across key dimensions.

## 1. Environment Variables & Configuration

### Discovery
- [ ] Identified all required environment variables (VAULT_PATH_LOCAL, VAULT_PATH_CLOUD, SIGNALS_DIR_*)
- [ ] Documented optional tuning parameters (timeouts, retries, policies)
- [ ] Verified signal directories exist and are writable
- [ ] Checked folder structure matches expected layout (Needs_Action/, Plans/, etc.)

### Build vs Runtime
- [ ] Confirmed no build-time variables required (runtime-only skill)
- [ ] Validated environment variables are loaded from .env
- [ ] Tested with missing optional variables (graceful degradation)

### Secrets Management
- [ ] Confirmed skill never handles secrets directly
- [ ] Validated SECRETS_PATTERN covers all sensitive patterns
- [ ] Tested AUTO_MARK_SECRETS detection (false positive rate acceptable?)
- [ ] Verified secrets never written to signal files

### Validation
```bash
# Run this validation script before deployment
cat .env | grep -E "(VAULT_PATH|SIGNALS_DIR|DELEGATION_)" || echo "Missing config"
test -d "$VAULT_PATH_LOCAL" || echo "Local vault missing"
test -d "$VAULT_PATH_CLOUD" || echo "Cloud vault missing"
test -w "$SIGNALS_DIR_LOCAL" || echo "Local signals dir not writable"
test -w "$SIGNALS_DIR_CLOUD" || echo "Cloud signals dir not writable"
```

---

## 2. Network & Topology

### Port Discovery
- [ ] Confirmed no network ports required (filesystem-only)
- [ ] Verified sync tool (Dropbox, rsync, git) doesn't require firewall rules

### Dependency Topology
- [ ] Mapped dependencies: vault_state_manager → filesystem
- [ ] Identified external sync tool (Dropbox, rsync, git, Obsidian Sync)
- [ ] Documented sync latency (measured: _____ ms average)
- [ ] Tested behavior with sync tool offline

### Docker/K8s Implications
- [ ] Designed volume mounts for local vault (`-v /host/vault_local:/vault_local`)
- [ ] Designed volume mounts for cloud vault (`-v /host/vault_cloud:/vault_cloud`)
- [ ] Ensured signal directories are writable by container user
- [ ] Configured PersistentVolumeClaims (if Kubernetes)
- [ ] Tested file permissions in containerized environment

### Concurrency
- [ ] Verified claim-by-move semantics work in target filesystem (POSIX-compliant?)
- [ ] Tested concurrent delegation from multiple lex instances
- [ ] Measured contention rate (% of failed claims due to race)

---

## 3. Auth / CORS / Security

### Authentication
- [ ] Confirmed no authentication required (local filesystem)
- [ ] Verified sync tool handles cloud authentication (Dropbox OAuth, SSH keys, etc.)
- [ ] Documented agent authorization model (lex vs cex permissions)

### Security Risks
- [ ] **Secret leakage**: Validated `local_only` sync policy enforcement
- [ ] **Task hijacking**: Tested signal claim-by-move prevents unauthorized access
- [ ] **Approval tampering**: Verified approval signatures are validated
- [ ] **Stale signals**: Tested timeout cleanup prevents orphaned signals
- [ ] **Sync conflicts**: Implemented conflict resolution policy
- [ ] **Malicious responses**: Validated all cloud responses before applying

### Validation Rules
- [ ] Path traversal checks (reject `..`, absolute paths, symlinks)
- [ ] Signal signature validation (HMAC if enabled)
- [ ] Approval timestamp validation (not expired)
- [ ] Sync policy enforcement (reject cloud access to local_only files)

### Audit Trail
- [ ] All delegation events logged (timestamp, task_id, agents, outcome)
- [ ] All approval events logged (decision, user, timestamp)
- [ ] All timeout/orphan events logged
- [ ] All security violations logged (rejected operations)

### Compliance
- [ ] Verified compliance with company data residency policy (secrets stay local)
- [ ] Documented audit log retention policy
- [ ] Tested log tamper detection (append-only; size decreases detected)

---

## 4. Blueprints & Templates

### Signal File Templates
- [ ] Validated delegation_request template (all fields present)
- [ ] Validated delegation_response template
- [ ] Validated approval_sync template
- [ ] Validated info_request template
- [ ] Tested template variable substitution (no placeholders left)

### Workflow Templates
- [ ] Tested delegation workflow (lex → cex → lex)
- [ ] Tested approval sync workflow (human → lex)
- [ ] Tested info request workflow (cex → lex → cex)
- [ ] Tested timeout workflow (cleanup orphaned signals)

### Asset Availability
- [ ] Checked if `.env.example` exists in `assets/` folder
- [ ] Checked if signal templates exist in `assets/` folder
- [ ] Checked if workflow diagrams exist (if applicable)

---

## 5. Core Operations

### Delegate Task to Cloud
- [ ] Tested successful delegation (task planned by cex)
- [ ] Tested delegation rejection (local_only task)
- [ ] Tested delegation timeout (cex doesn't respond)
- [ ] Tested delegation failure (cex returns error)
- [ ] Tested delegation retry (transient failure)

### Receive Cloud Response
- [ ] Tested successful response processing (plan file validated)
- [ ] Tested failed response handling (error logged, fallback triggered)
- [ ] Tested needs_info response (info request created)
- [ ] Tested response validation (task_id mismatch rejected)
- [ ] Tested signal cleanup (request + response deleted)

### Sync Approval State
- [ ] Tested approval sync (approved in cloud → approved in local)
- [ ] Tested rejection sync (rejected in cloud → rejected in local)
- [ ] Tested approval signature validation (valid signature accepted)
- [ ] Tested approval signature rejection (invalid signature rejected)
- [ ] Tested approval conflict resolution (local edits overridden by approval)

### Handle Info Request
- [ ] Tested safe info request (env_var on allow-list)
- [ ] Tested unsafe info request (secret rejected)
- [ ] Tested secret reference request (reference returned, not secret)
- [ ] Tested file metadata request (metadata returned, not content)
- [ ] Tested info response delivery (response signal created)

---

## 6. Integration with Other Skills

### vault_state_manager
- [ ] Verified delegation manager uses vault_state_manager for file operations
- [ ] Tested permission enforcement (lex permissions respected)
- [ ] Tested atomic file moves (claim-by-move works)

### task_lifecycle_manager
- [ ] Verified delegation triggers lifecycle state changes
- [ ] Tested task ownership transfer (lex → cex)
- [ ] Tested approval sync updates lifecycle metadata

### approval_request_creator
- [ ] Verified approval requests trigger approval sync
- [ ] Tested approval signal creation
- [ ] Tested approval signal processing

---

## 7. Gotchas & Edge Cases

- [ ] **Clock skew**: Tested with local/cloud time difference (mitigation works?)
- [ ] **Partial sync**: Tested signal synced but task not synced (retry works?)
- [ ] **Race conditions**: Tested concurrent claims (ENOENT handled gracefully?)
- [ ] **Circular delegation**: Tested max depth limit (prevents infinite loop?)
- [ ] **Orphaned signals**: Tested heartbeat + cleanup (stale signals reclaimed?)
- [ ] **False positives**: Tested secret detection (context-aware logic works?)
- [ ] **Approval conflicts**: Tested concurrent approval + edit (approval wins?)
- [ ] **Network partition**: Tested sync offline (fallback triggered?)

---

## 8. Monitoring & Observability

### Metrics
- [ ] **Delegation success rate**: _____ % (target: > 95%)
- [ ] **Approval sync latency**: _____ ms (target: < 10 seconds)
- [ ] **Secret leakage incidents**: _____ (target: 0)
- [ ] **Signal orphan rate**: _____ % (target: < 1%)
- [ ] **Sync conflict rate**: _____ % (target: < 5%)

### Logging
- [ ] Delegation events logged to `delegation.log`
- [ ] Approval events logged to `approvals.log`
- [ ] Timeout events logged to `delegation_timeouts.log`
- [ ] Orphan events logged to `orphaned_signals.log`
- [ ] Sync conflict events logged to `sync_conflicts.log`

### Alerting
- [ ] Alert on delegation timeout (threshold: > 10 per hour)
- [ ] Alert on approval sync failure (threshold: > 1 per day)
- [ ] Alert on secret leakage attempt (threshold: 0 tolerance)
- [ ] Alert on high orphan rate (threshold: > 5% of signals)
- [ ] Alert on sync offline (threshold: > 5 minutes)

---

## 9. Testing & Validation

### Unit Tests
- [ ] Test signal file creation (all fields present)
- [ ] Test signal file parsing (valid JSON)
- [ ] Test claim-by-move logic (race condition handling)
- [ ] Test timeout calculation (relative vs absolute)
- [ ] Test secret detection (regex patterns)

### Integration Tests
- [ ] Test end-to-end delegation (lex → cex → lex)
- [ ] Test approval sync (cloud → local)
- [ ] Test info request (cex → lex → cex)
- [ ] Test conflict resolution (local vs cloud)
- [ ] Test cleanup jobs (orphaned signals removed)

### Stress Tests
- [ ] Test high delegation rate (100+ per minute)
- [ ] Test concurrent claims (10+ agents claiming same signal)
- [ ] Test large task files (> 1 MB)
- [ ] Test slow sync (latency > 30 seconds)
- [ ] Test crash recovery (agent crashes mid-delegation)

### Security Tests
- [ ] Test secret leakage prevention (local_only enforced)
- [ ] Test approval tampering (invalid signature rejected)
- [ ] Test path traversal (`.., absolute paths rejected)
- [ ] Test signal injection (malicious signal rejected)

---

## 10. Deployment Readiness

### Pre-Deployment
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] All security tests passing
- [ ] Documentation complete (SKILL.md, patterns.md, gotchas.md)
- [ ] Example templates in `assets/` folder
- [ ] `.env.example` file provided

### Deployment
- [ ] Environment variables configured in production .env
- [ ] Signal directories created and writable
- [ ] Sync tool (Dropbox, rsync) configured and running
- [ ] Cleanup jobs scheduled (cron or systemd timer)
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested

### Post-Deployment
- [ ] Monitor delegation success rate (first 24 hours)
- [ ] Monitor approval sync latency (first 24 hours)
- [ ] Check for secret leakage incidents (continuous)
- [ ] Validate orphan cleanup rate (first week)
- [ ] Review logs for unexpected errors (first week)

---

## 11. Rollback Plan

### Rollback Triggers
- [ ] Delegation success rate < 80%
- [ ] Approval sync latency > 60 seconds
- [ ] Secret leakage incident detected
- [ ] Signal orphan rate > 10%
- [ ] Critical security vulnerability discovered

### Rollback Procedure
1. [ ] Stop delegation (disable agent_delegation_manager skill)
2. [ ] Revert to local-only mode (lex handles all tasks)
3. [ ] Archive signal files (for forensics)
4. [ ] Notify team (incident report)
5. [ ] Restore from backup (if data corrupted)

---

## 12. Risk Assessment

### High-Impact Risks
- [ ] **Secret leakage**: Mitigation in place? (sync policy enforcement)
- [ ] **Data loss**: Mitigation in place? (atomic writes, backups)
- [ ] **Infinite loops**: Mitigation in place? (delegation depth limit)
- [ ] **Approval bypass**: Mitigation in place? (signature validation)

### Medium-Impact Risks
- [ ] **Slow sync**: Mitigation in place? (timeout logic)
- [ ] **Orphaned signals**: Mitigation in place? (cleanup jobs)
- [ ] **False positives**: Mitigation in place? (context-aware detection)
- [ ] **Conflict rate**: Mitigation in place? (conflict resolution policy)

### Low-Impact Risks
- [ ] **Clock skew**: Mitigation in place? (relative timeouts)
- [ ] **Partial sync**: Mitigation in place? (retry with backoff)
- [ ] **Race conditions**: Mitigation in place? (ENOENT handling)

---

## Sign-Off

### Checklist Completion
- [ ] All "High-Impact Risks" addressed
- [ ] All "Pre-Deployment" items completed
- [ ] All "Security Tests" passed
- [ ] All "Monitoring & Observability" configured
- [ ] Rollback plan documented and tested

### Approvals
- [ ] Technical lead reviewed and approved
- [ ] Security team reviewed and approved (if required)
- [ ] Product owner reviewed and approved (if required)

### Deployment Authorization
- [ ] **Date**: _______________
- [ ] **Approved by**: _______________
- [ ] **Deployment window**: _______________

---

**Notes:**
- This checklist should be completed BEFORE deploying agent_delegation_manager to production
- Re-run this checklist after major changes to the skill
- Keep this checklist under version control alongside SKILL.md
