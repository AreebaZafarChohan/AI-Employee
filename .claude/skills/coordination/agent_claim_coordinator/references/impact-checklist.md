# Impact Checklist for Agent Claim Coordinator

Use this checklist before deploying or modifying the agent_claim_coordinator skill.

## 1. Environment Variables & Configuration

- [ ] Verified VAULT_PATH configured and exists
- [ ] Verified In_Progress/ folder exists and writable
- [ ] Set CLAIM_RESOLUTION_POLICY (first_claim_wins | agent_priority | human_resolve)
- [ ] Configured CLAIM_TIMEOUT_MS (recommended: 300000 = 5 minutes)
- [ ] Configured CLAIM_HEARTBEAT_INTERVAL_MS (recommended: 30000 = 30 seconds)
- [ ] Configured AGENT_PRIORITIES (if using agent_priority policy)
- [ ] Verified log files writable (claims.log, claim_conflicts.log)

## 2. Network & Topology

- [ ] Confirmed filesystem type (POSIX local | NFS | SMB)
- [ ] Verified atomic rename support (test fs.rename())
- [ ] Tested claim-by-move on target filesystem
- [ ] Configured file locking (if network filesystem)
- [ ] Measured filesystem latency (heartbeat update time)

## 3. Auth / Security

- [ ] Validated agent permission rules (per AGENTS.md)
- [ ] Tested permission enforcement (unauthorized claims rejected)
- [ ] Verified audit logging (all claims logged)
- [ ] Configured log retention policy
- [ ] Tested permission revocation handling

## 4. Core Operations

- [ ] Tested claim task (success case)
- [ ] Tested claim task (already claimed - conflict)
- [ ] Tested detect conflicts (stale heartbeat)
- [ ] Tested detect conflicts (multiple competing claims)
- [ ] Tested resolve conflict (first_claim_wins)
- [ ] Tested resolve conflict (agent_priority)
- [ ] Tested resolve conflict (human_resolve)
- [ ] Tested reclaim stale task
- [ ] Tested release claim (completed)
- [ ] Tested release claim (aborted)

## 5. Heartbeat Protocol

- [ ] Tested heartbeat updates (normal operation)
- [ ] Tested heartbeat timeout detection
- [ ] Tested heartbeat failure handling (agent aborts work)
- [ ] Tested heartbeat race conditions (grace period)
- [ ] Measured heartbeat update latency

## 6. Conflict Resolution

- [ ] Tested first_claim_wins policy
- [ ] Tested agent_priority policy
- [ ] Tested human_resolve policy
- [ ] Tested conflict marker file creation
- [ ] Tested human notification on conflict
- [ ] Tested graceful degradation (if enabled)

## 7. Edge Cases & Gotchas

- [ ] Tested clock skew handling (NTP sync verified)
- [ ] Tested network filesystem atomicity (locking if needed)
- [ ] Tested heartbeat update race (grace period effective)
- [ ] Tested concurrent conflict detection (single coordinator)
- [ ] Tested permission validation race
- [ ] Tested orphaned claim recovery (process killed)
- [ ] Tested claim thrashing mitigation (backoff working)
- [ ] Tested heartbeat failure cascade (circuit breaker)

## 8. Monitoring & Observability

### Metrics
- [ ] Claim success rate: _____ % (target: > 95%)
- [ ] Conflict rate: _____ % (target: < 5%)
- [ ] Reclaim rate: _____ % (target: < 2%)
- [ ] Conflict resolution time: _____ ms (target: < 1000ms)
- [ ] Heartbeat failure rate: _____ % (target: < 0.1%)

### Logging
- [ ] Claims logged to claims.log
- [ ] Conflicts logged to claim_conflicts.log
- [ ] Reclaims logged with staleness
- [ ] Releases logged with reason

### Alerting
- [ ] Alert on high conflict rate (> 10%)
- [ ] Alert on high reclaim rate (> 5%)
- [ ] Alert on heartbeat failure cascade
- [ ] Alert on permission violations

## 9. Integration Testing

- [ ] Tested with vault_state_manager
- [ ] Tested with task_lifecycle_manager
- [ ] Tested with agent_delegation_manager
- [ ] Tested multi-agent coordination (2+ agents)
- [ ] Tested agent crash recovery

## 10. Stress Testing

- [ ] Tested high claim rate (100+ claims/min)
- [ ] Tested concurrent claims (10+ agents)
- [ ] Tested many tasks (1000+ in In_Progress/)
- [ ] Tested long-running tasks (> 1 hour)
- [ ] Tested agent restarts during claims

## 11. Deployment Readiness

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Documentation complete
- [ ] Example configurations provided
- [ ] Monitoring dashboards configured
- [ ] Alerts configured and tested
- [ ] Runbook created for common issues

## 12. Rollback Plan

### Triggers
- [ ] Claim success rate < 80%
- [ ] Conflict rate > 20%
- [ ] System-wide heartbeat failures

### Procedure
1. [ ] Stop coordinator
2. [ ] Revert to manual claim management
3. [ ] Archive conflict files
4. [ ] Notify team
5. [ ] Restore from backup (if needed)

## Sign-Off

- [ ] Technical lead approved
- [ ] Security team approved (if required)
- [ ] **Deployment date**: _______________
- [ ] **Approved by**: _______________
