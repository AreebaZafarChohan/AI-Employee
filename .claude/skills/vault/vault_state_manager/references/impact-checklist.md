# Vault State Manager Impact Checklist

This checklist ensures all deployment environments are considered when using the Vault State Manager skill.

---

## Environment Compatibility Checklist

### Local Development

- [ ] **VAULT_PATH set correctly** in `.env`
- [ ] **All lifecycle folders exist** (Needs_Action, Plans, In_Progress, etc.)
- [ ] **File permissions allow read/write** for agent user
- [ ] **No symlinks in vault** (security risk)
- [ ] **Agent identity configured** (lex, cex, orch, watchers)
- [ ] **Log rotation configured** (prevent log files from growing unbounded)
- [ ] **Backup strategy in place** (vault should be backed up regularly)

### Docker Container

- [ ] **Vault mounted as volume**: `-v /host/vault:/vault`
- [ ] **Volume mount is read-write** (not read-only)
- [ ] **Container user has write permissions** to vault
- [ ] **VAULT_PATH environment variable set** to mounted path
- [ ] **Volume persists across container restarts** (not tmpfs)
- [ ] **File ownership correct** (container user matches host user)
- [ ] **No filesystem differences** (ext4 vs NTFS behavior)

### Docker Compose

- [ ] **Vault volume defined** in `docker-compose.yml`
- [ ] **Volume shared correctly** between services
- [ ] **All agent containers mount same volume** (for shared vault access)
- [ ] **Volume driver supports atomic moves** (local, NFS with proper config)
- [ ] **Service dependencies defined** (database before app, etc.)
- [ ] **Network allows inter-service communication**

### Kubernetes

- [ ] **PersistentVolumeClaim created** for vault
- [ ] **Volume mounted in all agent pods**
- [ ] **AccessMode is ReadWriteMany** (multiple pods may need write access)
- [ ] **Storage class supports atomic operations**
- [ ] **Volume reclaim policy is Retain** (prevent data loss)
- [ ] **Init containers create folder structure** if needed
- [ ] **File permissions set correctly** via securityContext

---

## Security Checklist

### Path Validation

- [ ] **All paths validated** via `validatePath()` before use
- [ ] **No path traversal allowed** (`..`, absolute paths rejected)
- [ ] **Symlinks rejected** (prevent escaping vault)
- [ ] **Relative paths resolved** within VAULT_PATH only
- [ ] **Null bytes rejected** in filenames

### Agent Permissions

- [ ] **Agent identity verified** before every write
- [ ] **Write permissions enforced** per AGENTS.md §3
- [ ] **lex cannot write to Approved/** (only human can)
- [ ] **cex cannot write at all** (read-only via lex proxy)
- [ ] **orch can only move files** (cannot create new files)
- [ ] **Watchers limited to their folders** (emails, messages, etc.)

### File Operations

- [ ] **Writes use temp files** (atomic via rename)
- [ ] **Temp files cleaned up** on failure
- [ ] **Moves are atomic** (`fs.rename` on same filesystem)
- [ ] **No partial writes** (rollback on error)
- [ ] **File locks respected** (claim-by-move protocol)

### Secrets Management

- [ ] **Never read .env via vault manager**
- [ ] **Never write credentials to vault**
- [ ] **Log redaction for sensitive data** (email addresses, etc.)
- [ ] **Audit logs protected** (append-only, no deletion)

---

## Data Integrity Checklist

### Idempotency

- [ ] **All operations safe to retry** (no double-processing)
- [ ] **Watchers use unique IDs** (email ID, message ID, etc.)
- [ ] **Plan IDs checked for collisions** before creation
- [ ] **Move operations detect conflicts** (EEXIST error)
- [ ] **Failed operations leave consistent state**

### Concurrency Control

- [ ] **Claim-by-move enforced** (atomic file moves only)
- [ ] **No copy-then-delete** for claims (race condition)
- [ ] **Conflicts detected and reported** (ConflictError thrown)
- [ ] **Single-writer rule enforced** (no concurrent edits)
- [ ] **List operations return consistent snapshots**

### State Machine Enforcement

- [ ] **Legal transitions defined** (Needs_Action → Plans → In_Progress → ...)
- [ ] **Illegal transitions rejected** (cannot skip stages)
- [ ] **Status field matches folder** (file in Plans/ has status='planned')
- [ ] **Lifecycle documented** in AGENTS.md §4

---

## Performance Checklist

### Filesystem Considerations

- [ ] **Vault on fast storage** (SSD, not spinning disk)
- [ ] **Avoid network filesystems** (NFS, SMB) if possible (latency issues)
- [ ] **Monitor disk usage** (prevent vault from filling up)
- [ ] **Log rotation configured** (prevent unbounded growth)
- [ ] **Archive old plans** (move to Archive/ after 30 days)

### Agent Efficiency

- [ ] **List operations cached** (don't list every second)
- [ ] **Polling intervals reasonable** (5-60 seconds, not milliseconds)
- [ ] **Batch operations where possible** (process multiple files per loop)
- [ ] **Avoid unnecessary reads** (cache metadata if unchanged)

---

## Monitoring & Observability Checklist

### Logging

- [ ] **All state changes logged** (moves, writes)
- [ ] **Agent identity included** in every log entry
- [ ] **Timestamps in ISO 8601 format** (UTC)
- [ ] **Structured logging** (JSON format preferred)
- [ ] **Log levels configurable** (debug, info, warn, error)

### Metrics

- [ ] **Track file counts** per folder (gauge metric)
- [ ] **Track operation latency** (histogram)
- [ ] **Track error rates** per operation type
- [ ] **Track claim conflicts** (how often files are already claimed)
- [ ] **Track plan processing time** (end-to-end duration)

### Alerts

- [ ] **Alert on permission errors** (indicates misconfiguration)
- [ ] **Alert on disk full** (vault cannot write)
- [ ] **Alert on old files stuck** in Pending_Approval (human action needed)
- [ ] **Alert on high error rates** (something is broken)

---

## Error Handling Checklist

### Structured Errors

- [ ] **All errors extend base Error class**
- [ ] **Error types match failure modes** (PermissionError, ConflictError, etc.)
- [ ] **Error messages include context** (filename, agent, folder)
- [ ] **Errors logged before throwing** (for debugging)

### Retry Logic

- [ ] **Transient errors retried** with exponential backoff
- [ ] **Permanent errors not retried** (PermissionError, IllegalTransitionError)
- [ ] **Max retries enforced** (prevent infinite loops)
- [ ] **Retry attempts logged** (for debugging)

### Graceful Degradation

- [ ] **Missing files handled** (FileNotFoundError → log and skip)
- [ ] **Concurrent claims handled** (move fails → another agent claimed it)
- [ ] **Filesystem errors handled** (disk full → alert and halt)

---

## Testing Checklist

### Unit Tests

- [ ] **Path validation tested** (traversal attacks blocked)
- [ ] **Permission checks tested** (unauthorized writes rejected)
- [ ] **Atomic operations tested** (temp file cleanup on failure)
- [ ] **Conflict detection tested** (EEXIST handled)
- [ ] **Error handling tested** (all error types covered)

### Integration Tests

- [ ] **Multi-agent scenarios tested** (concurrent claims)
- [ ] **Full lifecycle tested** (Needs_Action → Done)
- [ ] **Watcher integration tested** (write to vault, lex picks up)
- [ ] **Orchestrator integration tested** (approved actions executed)
- [ ] **Human approval flow tested** (manual file moves)

### Failure Scenarios

- [ ] **Disk full scenario** (write fails gracefully)
- [ ] **Filesystem unmounted** (operations fail safely)
- [ ] **Corrupted files** (JSON parse errors handled)
- [ ] **Missing folders** (created on startup or error reported)
- [ ] **Permission changes** (runtime permission errors handled)

---

## Deployment Checklist

### Pre-Deployment

- [ ] **Vault folder structure created**
- [ ] **File permissions set correctly**
- [ ] **VAULT_PATH configured in .env**
- [ ] **Agent identities configured**
- [ ] **Backup strategy verified**
- [ ] **Monitoring enabled**

### Post-Deployment

- [ ] **Vault accessible by all agents**
- [ ] **No permission errors in logs**
- [ ] **Files moving through lifecycle**
- [ ] **Logs being written**
- [ ] **Disk usage monitored**
- [ ] **Performance acceptable** (latency < 100ms for reads/writes)

---

## Maintenance Checklist

### Daily

- [ ] **Check for files stuck** in Pending_Approval
- [ ] **Review error logs** for anomalies
- [ ] **Monitor disk usage**

### Weekly

- [ ] **Archive old plans** (Done → Archive)
- [ ] **Rotate logs** (compress old logs)
- [ ] **Review agent permissions** (audit log for unauthorized access attempts)

### Monthly

- [ ] **Review lifecycle metrics** (how long do plans stay in each stage?)
- [ ] **Optimize slow operations** (if latency increasing)
- [ ] **Test backup restore** (ensure backups are valid)
- [ ] **Update documentation** if workflows changed

---

## Compliance Checklist

### Audit Trail

- [ ] **All actions logged** (who, what, when)
- [ ] **Logs tamper-proof** (append-only, no deletion)
- [ ] **Log retention policy defined** (how long to keep logs)
- [ ] **Logs backed up** (separate from vault)

### Data Privacy

- [ ] **PII redacted from logs** (email addresses, names, etc.)
- [ ] **Sensitive files encrypted** at rest (if required)
- [ ] **Access logs reviewed** regularly
- [ ] **Unauthorized access attempts detected** and alerted

---

## Sign-Off

Before deploying Vault State Manager to production, verify:

- [ ] **All environment checklists complete**
- [ ] **All security checks passed**
- [ ] **All error handling tested**
- [ ] **Monitoring configured**
- [ ] **Documentation up to date**
- [ ] **Team trained on workflows**

**Deployment Approved By:** _______________
**Date:** _______________
**Environment:** _______________
