# Time Event Scheduler Impact Checklist

This checklist ensures all system impacts are considered when deploying or modifying the Time Event Scheduler skill.

## Pre-Deployment Checklist

### Environment Configuration

- [ ] **VAULT_PATH** is set and writable
- [ ] **Schedules/** folder exists with proper permissions
- [ ] **Calendars/** folder created (if using calendar export)
- [ ] **TIMEZONE_DEFAULT** is set to appropriate value
- [ ] **Audit_Logs/Schedules/** folder exists
- [ ] All optional environment variables documented in `.env.example`
- [ ] No hardcoded paths in schedule files
- [ ] Timezone database (IANA) is up to date

### File System Impact

- [ ] Schedules/ folder size is monitored (alert if >1000 files)
- [ ] Old schedules are archived (retention policy defined)
- [ ] File naming convention is consistent (`<name>.schedule.json`)
- [ ] Schedule files are valid JSON (validated on save)
- [ ] No race conditions on concurrent file access
- [ ] File locking mechanism is in place (if needed)
- [ ] Disk space is monitored for vault growth

### Network & Integration

- [ ] No network ports required for core functionality
- [ ] Calendar API credentials configured (if using integrations)
- [ ] Rate limits documented for external APIs (Google Calendar, etc.)
- [ ] Webhook endpoints tested (if using notifications)
- [ ] DNS resolution works for external services
- [ ] Firewall rules allow outbound HTTPS (if using APIs)
- [ ] TLS certificates valid for external integrations

### Authentication & Authorization

- [ ] Only lex/orch agents can create schedules (enforced in code)
- [ ] Watcher agents cannot create schedules (read-only access)
- [ ] Human approval required for critical schedules (documented)
- [ ] Schedule creator tracked in metadata (audit trail)
- [ ] Agent identity verified before schedule execution
- [ ] No privilege escalation via schedule assignment
- [ ] Calendar export doesn't leak sensitive data

### Security

- [ ] Template content is sanitized (no code injection)
- [ ] Cron expressions validated before saving
- [ ] Timezone identifiers validated (prevent path traversal)
- [ ] No secrets in schedule files (use .env references)
- [ ] Audit logs capture all schedule operations
- [ ] Failed executions logged with details
- [ ] Rate limiting on schedule creation (prevent abuse)
- [ ] Max occurrences enforced (prevent runaway schedules)
- [ ] Timeout protection on task execution (prevent hanging)
- [ ] Error messages don't leak system information

---

## Operational Checklist

### Monitoring

- [ ] Schedule execution success rate tracked
- [ ] Failed schedules alert on-call engineer
- [ ] Missed schedules detected and logged
- [ ] Clock drift monitored (NTP sync checked)
- [ ] Disk space alerts for vault folder
- [ ] Agent utilization tracked (lex, orch)
- [ ] Average task duration recorded
- [ ] Schedule count tracked over time

### Performance

- [ ] Schedule evaluation loop runs every 1 minute (configurable)
- [ ] Only due schedules loaded (not all schedules on every tick)
- [ ] Schedule index cached in memory (reduce file reads)
- [ ] Parallel execution enabled (multiple schedules at once)
- [ ] Parallel execution limit enforced (prevent resource exhaustion)
- [ ] Long-running tasks use background workers
- [ ] Calendar export optimized (lazy loading, pagination)
- [ ] Timezone conversions cached (avoid repeated calculations)

### Reliability

- [ ] System restarts don't lose schedules (persistent storage)
- [ ] Crash recovery tested (next_occurrence preserved)
- [ ] DST transitions handled correctly (or documented as limitation)
- [ ] Leap seconds handled (use UTC to avoid issues)
- [ ] Schedule version conflicts detected (optimistic locking)
- [ ] Retry logic implemented for transient failures
- [ ] Exponential backoff used for retries
- [ ] Dead letter queue for permanently failed schedules

---

## Deployment Checklist

### Before Deployment

- [ ] All environment variables set in production .env
- [ ] Vault folder backed up
- [ ] Timezone database updated to latest version
- [ ] Integration tests passed (all supported timezones)
- [ ] Load testing completed (1000+ schedules)
- [ ] Security scan completed (no vulnerabilities)
- [ ] Documentation reviewed and updated
- [ ] Runbook created for common operations

### During Deployment

- [ ] Deploy during low-traffic window (if possible)
- [ ] Monitor logs for errors during startup
- [ ] Verify schedule evaluation loop starts
- [ ] Check first few schedule executions
- [ ] Validate timezone conversions
- [ ] Test manual schedule execution
- [ ] Verify calendar export functionality
- [ ] Check audit log writes

### After Deployment

- [ ] Monitor schedule execution rate for 24 hours
- [ ] Review error logs for unexpected failures
- [ ] Verify no schedules were missed during deployment
- [ ] Check disk usage hasn't increased unexpectedly
- [ ] Validate external integrations still work
- [ ] Confirm notifications are sent correctly
- [ ] Update status page / documentation
- [ ] Communicate changes to team

---

## Agent-Specific Checklist

### Local Executive Agent (lex)

- [ ] Can create new schedules
- [ ] Can update existing schedules
- [ ] Can delete (archive) schedules
- [ ] Can manually trigger schedules
- [ ] Cannot approve own tasks (moves to Pending_Approval/)
- [ ] Respects parallel execution limit
- [ ] Logs all schedule operations

### Orchestrator Agent (orch)

- [ ] Can execute scheduled tasks
- [ ] Cannot create new schedules (lex only)
- [ ] Respects timeout limits
- [ ] Handles task failures gracefully
- [ ] Reports execution status back to schedule
- [ ] Updates execution_count and last_executed
- [ ] Writes to audit log

### Cloud Executive Agent (cex)

- [ ] Cannot create schedules directly (via lex proxy)
- [ ] Can recommend schedules to lex
- [ ] Read-only access to schedule files
- [ ] Can query schedule status
- [ ] Cannot modify running schedules

### Watcher Agents

- [ ] Cannot create schedules (read-only)
- [ ] Cannot modify schedules
- [ ] Can read schedule files (for context)
- [ ] Cannot trigger schedule execution

---

## Compliance Checklist

### Data Privacy

- [ ] Schedule files don't contain PII (customer names, emails)
- [ ] Template content sanitized (no sensitive data)
- [ ] Audit logs don't expose secrets
- [ ] Calendar exports don't leak internal data
- [ ] Notification messages are generic (no details)
- [ ] External API calls encrypted (HTTPS only)
- [ ] Data retention policy documented

### Audit Trail

- [ ] All schedule creations logged
- [ ] All schedule modifications logged
- [ ] All schedule deletions logged
- [ ] All executions logged (success and failure)
- [ ] Agent identity captured in logs
- [ ] Timestamps are UTC (consistent)
- [ ] Log retention policy defined (90 days recommended)

### Business Continuity

- [ ] Backup strategy for schedule files
- [ ] Disaster recovery plan documented
- [ ] Failover mechanism tested
- [ ] Schedule restoration procedure documented
- [ ] Critical schedules identified and flagged
- [ ] On-call engineer has access to runbook
- [ ] Escalation procedure defined

---

## Testing Checklist

### Unit Tests

- [ ] Cron expression parsing tested
- [ ] Timezone conversion tested (multiple zones)
- [ ] Template rendering tested (all variables)
- [ ] Natural language parsing tested
- [ ] Validation rules tested (invalid inputs)
- [ ] Calendar export tested (all formats)
- [ ] Error handling tested (edge cases)

### Integration Tests

- [ ] Schedule creation end-to-end
- [ ] Schedule execution end-to-end
- [ ] Task creation from schedule
- [ ] Notification delivery
- [ ] Calendar export to file
- [ ] Audit log writes
- [ ] Agent authorization enforcement

### Performance Tests

- [ ] 1000 schedules loaded in <1 second
- [ ] 100 schedules executed in parallel
- [ ] Calendar export of 500 events in <5 seconds
- [ ] Schedule evaluation loop latency <100ms
- [ ] Memory usage stable over 24 hours
- [ ] CPU usage <10% during evaluation

### Timezone Tests

- [ ] UTC schedule tested
- [ ] Multiple timezone schedules tested
- [ ] DST transition tested (spring forward)
- [ ] DST transition tested (fall back)
- [ ] Leap year tested (Feb 29)
- [ ] Timezone database update tested
- [ ] Invalid timezone rejected

### Edge Case Tests

- [ ] Schedule during DST transition
- [ ] Schedule at midnight (00:00)
- [ ] Schedule on Feb 29 (leap year)
- [ ] Schedule with max_occurrences reached
- [ ] Schedule with missing template variable
- [ ] Schedule with invalid cron expression
- [ ] Schedule with invalid timezone
- [ ] Schedule with very long description
- [ ] Concurrent schedule modifications
- [ ] System restart during execution

---

## Maintenance Checklist

### Daily

- [ ] Check error logs for failed schedules
- [ ] Verify schedule execution rate is normal
- [ ] Monitor disk space usage
- [ ] Check for stale schedules (not executed in >7 days)

### Weekly

- [ ] Review audit logs for anomalies
- [ ] Archive old schedules (completed or expired)
- [ ] Update schedule documentation
- [ ] Check timezone database for updates

### Monthly

- [ ] Performance review (execution times, success rate)
- [ ] Capacity planning (schedule count growth)
- [ ] Security audit (authorization, logging)
- [ ] Backup validation (restore test)

### Quarterly

- [ ] Disaster recovery drill
- [ ] Load testing (increased schedule count)
- [ ] Documentation review
- [ ] User training (if applicable)

---

## Incident Response Checklist

### Schedule Not Executing

1. [ ] Check if schedule is enabled (`enabled: true`)
2. [ ] Verify next_occurrence is in the past
3. [ ] Check cron expression is valid
4. [ ] Verify timezone is correct
5. [ ] Check agent is running (lex/orch)
6. [ ] Review error logs for failures
7. [ ] Check file permissions (schedule file readable)
8. [ ] Verify disk space available
9. [ ] Test manual execution (`executeSchedule(id)`)
10. [ ] Check system clock is synced (NTP)

### Schedule Executing Late

1. [ ] Check system clock drift (NTP status)
2. [ ] Review schedule evaluation loop latency
3. [ ] Check CPU/memory usage (resource contention)
4. [ ] Verify no blocking tasks (long-running execution)
5. [ ] Check parallel execution limit (too restrictive)
6. [ ] Review disk I/O performance (slow file reads)
7. [ ] Check if too many schedules (scale issue)

### Schedule Executing Twice

1. [ ] Check for DST transition (fall back)
2. [ ] Verify next_occurrence updated after execution
3. [ ] Check for race condition (concurrent execution)
4. [ ] Review execution_count (should increment)
5. [ ] Check for duplicate schedule files (naming collision)

### Failed Task Creation

1. [ ] Check vault permissions (Needs_Action/ writable)
2. [ ] Verify template variables provided
3. [ ] Check task file format (valid JSON)
4. [ ] Review disk space (out of space)
5. [ ] Check agent authorization (lex/orch only)
6. [ ] Review error logs (detailed error message)

### Calendar Export Failing

1. [ ] Check Calendars/ folder exists and is writable
2. [ ] Verify schedule IDs are valid
3. [ ] Check for invalid timezone in schedules
4. [ ] Review calendar format (ical vs google)
5. [ ] Check for too many events (size limit)
6. [ ] Verify external API credentials (if using API)

---

## Rollback Checklist

### Before Rollback

- [ ] Capture current state (schedule files, logs)
- [ ] Document reason for rollback
- [ ] Notify stakeholders (team, users)
- [ ] Backup current configuration

### During Rollback

- [ ] Stop schedule evaluation loop
- [ ] Restore previous version (code + config)
- [ ] Restore schedule files from backup (if needed)
- [ ] Verify timezone database version
- [ ] Restart schedule evaluation loop
- [ ] Check first few executions

### After Rollback

- [ ] Monitor for 1 hour (watch for errors)
- [ ] Verify no schedules missed
- [ ] Review rollback logs
- [ ] Update status page
- [ ] Post-mortem scheduled

---

## Sign-Off Checklist

Before production deployment, all stakeholders must review and approve:

- [ ] **Engineering Lead**: Code review, architecture approved
- [ ] **Operations**: Monitoring configured, runbook complete
- [ ] **Security**: Security review passed, no vulnerabilities
- [ ] **Product**: Requirements met, acceptance criteria passed
- [ ] **Compliance**: Data privacy requirements met
- [ ] **Documentation**: User docs and API docs updated

**Deployment Approval:**

- Approved by: ___________________
- Date: ___________________
- Deployment Window: ___________________

---

## Post-Deployment Validation

### Immediate (within 1 hour)

- [ ] Schedule evaluation loop running
- [ ] No critical errors in logs
- [ ] First schedule executed successfully
- [ ] Manual execution tested
- [ ] Calendar export tested
- [ ] Notifications delivered

### Short-term (within 24 hours)

- [ ] All timezone schedules executed correctly
- [ ] DST-affected schedules (if applicable) handled
- [ ] Performance metrics within baseline
- [ ] Error rate acceptable (<1%)
- [ ] No user complaints
- [ ] Audit logs capturing all events

### Long-term (within 1 week)

- [ ] Schedule execution rate stable
- [ ] Disk usage trending as expected
- [ ] No memory leaks detected
- [ ] External integrations stable
- [ ] User feedback positive
- [ ] No security incidents

---

## Summary

**Minimum Requirements for Production:**

1. Environment configured (VAULT_PATH, TIMEZONE_DEFAULT)
2. File permissions correct (Schedules/ writable)
3. Agent authorization enforced (lex/orch only)
4. Security validations in place (sanitization, validation)
5. Monitoring configured (error alerts, execution tracking)
6. Audit logging enabled (all operations logged)
7. Testing completed (unit, integration, timezone, performance)
8. Documentation updated (README, EXAMPLES, runbook)
9. Backup strategy defined (schedule files, configuration)
10. Rollback plan tested (can revert quickly)

**Critical Success Factors:**

- Cron expressions validated before execution
- Timezone handling robust (DST, leap year, etc.)
- Error handling comprehensive (retry, timeout, logging)
- Performance optimized (caching, parallel execution)
- Security enforced (authorization, sanitization, audit)

**Risk Mitigation:**

- Test in staging environment first
- Deploy gradually (canary deployment)
- Monitor closely for first 24 hours
- Have rollback plan ready
- Document all incidents and resolutions
