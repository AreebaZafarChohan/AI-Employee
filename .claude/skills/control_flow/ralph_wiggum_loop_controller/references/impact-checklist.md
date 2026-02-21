# Impact Checklist for Ralph Wiggum Loop Controller

Use this checklist before deploying or modifying the ralph_wiggum_loop_controller skill.

## 1. Environment Variables & Configuration

- [ ] Verified VAULT_PATH configured and exists
- [ ] Created Loops/ directory structure (Loops/Active/, Loops/Archive/, Loops/Checkpoints/)
- [ ] Created Signals/ directory structure (Signals/Pending/{agent}/, Signals/Responses/)
- [ ] Set LOOP_CHECK_INTERVAL_MS (recommended: 5000 = 5 seconds)
- [ ] Set MAX_CONCURRENT_LOOPS (recommended: 10)
- [ ] Set LOOP_TIMEOUT_DEFAULT_MS (recommended: 600000 = 10 minutes)
- [ ] Set MAX_LOOP_ITERATIONS (recommended: 100)

## 2. Stop Hooks

- [ ] Every loop has at least one success hook
- [ ] Every loop has a timeout hook (safety net)
- [ ] File paths in hooks are absolute, not relative
- [ ] Custom scripts in hooks have execute permissions (chmod +x)
- [ ] Custom scripts have timeout_ms configured
- [ ] Hook priorities are correctly ordered (timeout > resource > failure > success > retry)

## 3. Prompt Injection

- [ ] Prompt templates validated for syntax
- [ ] Prompt variables sanitized to prevent injection attacks
- [ ] Signal file expiry times are sufficient for target agent
- [ ] Target agent is configured to monitor Signals/Pending/ directory
- [ ] Prompt injection rate limiting configured (if needed)

## 4. Retry & Backoff

- [ ] max_retries is reasonable (< 10)
- [ ] Backoff strategy matches use case (exponential for transient failures)
- [ ] Maximum backoff delay is capped (recommended: 60000ms = 1 minute)
- [ ] Jitter enabled for multi-agent environments
- [ ] Circuit breaker configured for production loops

## 5. Resource Limits

- [ ] max_duration_ms set for all loops
- [ ] max_memory_mb set for long-running loops
- [ ] max_cpu_percent set for intensive loops
- [ ] Global max_concurrent_loops enforced
- [ ] Monitoring configured for resource usage

## 6. Monitoring & Observability

- [ ] Audit logging integrated (via audit_log_writer)
- [ ] Metrics collection enabled (loop iterations, success rate, etc.)
- [ ] Alerts configured for:
  - [ ] Loop timeout
  - [ ] Loop failure
  - [ ] Resource limit exceeded
  - [ ] Zombie loop detected
- [ ] Dashboard configured to display:
  - [ ] Active loops count
  - [ ] Average loop duration
  - [ ] Success/failure rate
  - [ ] Resource usage

## 7. Error Handling

- [ ] Hook evaluation errors are caught and logged
- [ ] Signal file write failures have retry logic
- [ ] Loop state updates use atomic operations
- [ ] Graceful degradation on resource exhaustion
- [ ] Recovery strategy for crashed agents

## 8. Testing

- [ ] Unit tests for hook evaluation
- [ ] Unit tests for backoff calculation
- [ ] Integration tests for complete loop lifecycle
- [ ] Tested file_exists hooks with actual files
- [ ] Tested custom script hooks with sample scripts
- [ ] Tested timeout hooks with time-delayed completion
- [ ] Load tested with multiple concurrent loops

## 9. Security

- [ ] Prompt variable sanitization enabled
- [ ] Custom script paths validated (no path traversal)
- [ ] Signal files have appropriate permissions (644 or 600)
- [ ] Loop task files have appropriate permissions (644 or 600)
- [ ] Audit log enabled for all loop operations

## 10. Integration with Other Skills

- [ ] agent_delegation_manager: Delegation signals supported
- [ ] agent_claim_coordinator: Loop claiming integrated
- [ ] audit_log_writer: Logging configured

## 11. Cleanup & Maintenance

- [ ] Orphaned signal cleanup job scheduled (hourly)
- [ ] Zombie loop detector scheduled (every 1 minute)
- [ ] Archived loop pruning scheduled (weekly)
- [ ] Checkpoint pruning configured (keep last 3)
- [ ] Log rotation configured for loop logs

## 12. Documentation

- [ ] Loop configuration template documented
- [ ] Stop hook examples documented
- [ ] Troubleshooting guide reviewed
- [ ] Runbook created for common operations:
  - [ ] Start loop
  - [ ] Stop loop manually
  - [ ] Recover from crash
  - [ ] Debug stuck loop

## 13. Rollback Plan

- [ ] Backup of current loop configurations
- [ ] Procedure to gracefully stop all active loops
- [ ] Procedure to rollback to previous version
- [ ] Contact information for on-call engineer

## 14. Specific Use Case Validation

### For Email Processing Loops
- [ ] Custom script checks inbox is empty
- [ ] Timeout sufficient for large inbox (recommend: 1800000ms = 30 min)
- [ ] Retry logic handles temporary API failures

### For API Sync Loops
- [ ] Retry hook configured with exponential backoff
- [ ] Failure hook configured for auth errors (do not retry)
- [ ] Rate limiting configured for API calls

### For Batch Processing Loops
- [ ] Resource limits set (memory, CPU)
- [ ] Checkpoint interval configured (every 10 iterations)
- [ ] Variable updater configured (if paginated)

### For Delegated Loops
- [ ] Integration with agent_delegation_manager tested
- [ ] Delegation response signal path correct
- [ ] Timeout accounts for cloud processing time

## 15. Production Readiness

- [ ] All tests passing
- [ ] Code review completed
- [ ] Security review completed (if handling sensitive data)
- [ ] Performance testing completed
- [ ] Documentation updated
- [ ] Monitoring dashboards created
- [ ] Alerting configured
- [ ] Runbooks created
- [ ] On-call team trained
- [ ] Rollback plan tested

## Post-Deployment Verification

After deploying, verify:

- [ ] Start a test loop and verify it runs
- [ ] Stop a test loop manually and verify it stops
- [ ] Verify timeout hook triggers correctly
- [ ] Verify success hook triggers correctly
- [ ] Verify retry hook with backoff works
- [ ] Verify signal files are created
- [ ] Verify audit logs are written
- [ ] Verify metrics are collected
- [ ] Verify orphaned signal cleanup runs
- [ ] Verify zombie loop detector runs

## Emergency Procedures

### Stop All Loops
```bash
# Manually stop all active loops
for loop in Loops/Active/*.json; do
  loop_id=$(basename "$loop" .json)
  node -e "require('./ralph_wiggum_loop_controller').stopLoop({loop_id: '$loop_id', reason: 'Emergency stop'})"
done
```

### Clear Orphaned Signals
```bash
# Delete all expired signal files
find Signals/Pending/ -name "*.json" -mmin +60 -delete
```

### Check Zombie Loops
```bash
# List loops with stale heartbeats
node -e "require('./ralph_wiggum_loop_controller').checkZombieLoops()"
```

---

## Sign-Off

- [ ] Developer: _________________ Date: _______
- [ ] Reviewer: _________________ Date: _______
- [ ] Security: _________________ Date: _______
- [ ] Operations: _________________ Date: _______

Notes:
_________________________________________
_________________________________________
_________________________________________
