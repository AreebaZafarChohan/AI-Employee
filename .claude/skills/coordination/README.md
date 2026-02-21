# Coordination Skills

Skills for coordinating agent activities, task delegation, and cross-environment synchronization.

## Skills in this Category

### agent_delegation_manager

Coordinate Local ↔ Cloud task ownership, approval sync, and vault sync flags.

**Key Features:**
- Signal-based async coordination between lex and cex
- Security boundaries (secrets stay local)
- Claim-by-move semantics for race condition prevention
- Automatic timeout and cleanup
- Approval synchronization from cloud to local
- Safe information sharing without secret leakage

**When to Use:**
- Delegating task planning from local to cloud agent
- Syncing approval decisions from cloud vault
- Managing task ownership transfers
- Coordinating cross-environment workflows

**Related Skills:**
- `vault/vault_state_manager` - Low-level vault operations
- `vault/task_lifecycle_manager` - Task state transitions
- `approval/approval_request_creator` - Approval workflow

[Full Documentation](./agent_delegation_manager/SKILL.md)

---

## Integration Patterns

### Local ↔ Cloud Coordination

```
┌─────────────────────────────────────────────────────────────┐
│                     Local Environment                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Executive Agent (lex)                         │   │
│  │  • Creates delegation requests                       │   │
│  │  • Processes cloud responses                         │   │
│  │  • Syncs approval state                              │   │
│  │  • Handles info requests                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agent_delegation_manager                            │   │
│  │  • Signal file operations                            │   │
│  │  • Sync policy enforcement                           │   │
│  │  • Timeout & cleanup                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Local Vault + Signal Directory                      │   │
│  │  • .signals/ (coordination files)                    │   │
│  │  • Needs_Action/, Plans/, etc.                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↕
                    Cloud Sync Layer
                  (Dropbox / rsync / git)
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                     Cloud Environment                        │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cloud Vault + Signal Directory                      │   │
│  │  • .signals/ (synced coordination files)             │   │
│  │  • Synced folders (Plans/, etc.)                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  agent_delegation_manager                            │   │
│  │  • Signal processing                                 │   │
│  │  • Response generation                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                         ↓                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Cloud Executive Agent (cex)                         │   │
│  │  • Polls for delegation requests                     │   │
│  │  • Creates plans                                     │   │
│  │  • Writes delegation responses                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Common Workflows

### 1. Task Delegation (lex → cex)

```
1. lex: Task arrives in Needs_Action/
2. lex: Check sync policy (not local_only)
3. lex: Create delegation request signal
4. Sync: Dropbox syncs signal to cloud
5. cex: Poll and claim signal
6. cex: Create plan in cloud vault
7. cex: Write delegation response signal
8. Sync: Dropbox syncs response to local
9. lex: Process response, validate plan
10. lex: Move task to In_Progress/
11. lex: Cleanup signals
```

### 2. Approval Sync (cloud → local)

```
1. Human: Approve task in cloud vault
2. Watcher: Detect approval (file move)
3. Watcher: Create approval signal
4. Sync: Dropbox syncs signal to local
5. lex: Poll for approval signals
6. lex: Validate approval signature
7. lex: Apply approval to local vault
8. lex: Log approval event
9. lex: Cleanup signal
```

### 3. Info Request (cex → lex → cex)

```
1. cex: Need local information (e.g., secret reference)
2. cex: Create info request signal
3. Sync: Dropbox syncs request to local
4. lex: Process info request
5. lex: Create info response (sanitized)
6. Sync: Dropbox syncs response to cloud
7. cex: Read info response
8. cex: Use information in plan
9. lex: Cleanup signals
```

---

## Security Considerations

### Secret Protection

Coordination skills enforce strict security boundaries:

1. **Sync Policy Enforcement**: Files marked `local_only` never leave local environment
2. **Secret Detection**: Auto-detect and mark files containing secrets
3. **Sanitization**: Info responses redact sensitive fields
4. **Validation**: Approval signals require valid signatures

### Security Checklist

- [ ] Secrets never written to signal files
- [ ] Local-only tasks rejected from delegation
- [ ] Approval signatures validated before applying
- [ ] Info responses sanitized (no secret leakage)
- [ ] Sync policy enforced at all boundaries

---

## Monitoring & Observability

### Key Metrics

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Delegation success rate | > 95% | < 90% |
| Approval sync latency | < 10s | > 60s |
| Secret leakage incidents | 0 | > 0 |
| Signal orphan rate | < 1% | > 5% |
| Sync conflict rate | < 5% | > 10% |

### Log Files

- `delegation.log`: All delegation events
- `approvals.log`: All approval events
- `delegation_timeouts.log`: Timeout events
- `orphaned_signals.log`: Orphaned signal cleanups
- `sync_conflicts.log`: Sync conflict resolutions

---

## Troubleshooting

### Common Issues

#### Delegation Timeout

**Symptom**: Task never gets planned by cex

**Debug**:
```bash
# Check sync status
ps aux | grep -i dropbox

# Check signal files
ls -la "$SIGNALS_DIR_LOCAL"
ls -la "$SIGNALS_DIR_CLOUD"

# Check logs
tail -f "${VAULT_PATH_LOCAL}/Logs/delegation_timeouts.log"
```

#### Secret Leakage

**Symptom**: Secrets appear in cloud vault

**Debug**:
```bash
# Check sync policies
find "$VAULT_PATH_CLOUD" -name "*.json" -exec jq -r '.sync_policy // "sync"' {} \; | sort | uniq -c

# Enable auto-detection
echo 'AUTO_MARK_SECRETS="true"' >> .env
```

#### Orphaned Signals

**Symptom**: Signal files accumulating in `.signals/`

**Debug**:
```bash
# Check orphaned signals
find "$SIGNALS_DIR_LOCAL" -name "*.claimed.json" -mmin +5

# Manually trigger cleanup
.specify/scripts/bash/cleanup-signals.sh
```

---

## Best Practices

### 1. Always Check Sync Policy Before Delegation

```javascript
if (task.sync_policy === "local_only") {
  await handleTaskLocally(taskId);
  return;
}
await delegateTaskToCloud(taskId);
```

### 2. Implement Timeout Logic

```javascript
const response = await waitForDelegationResponse(taskId, 30000);
if (!response) {
  // Fallback to local handling
  await handleTaskLocally(taskId);
}
```

### 3. Validate All External Inputs

```javascript
// Validate approval signature
if (signal.signature.hmac !== computeHMAC(data)) {
  throw new Error("Invalid signature");
}

// Validate timestamp
if (Date.now() - signal.created_at > MAX_AGE) {
  throw new Error("Signature expired");
}
```

### 4. Use Atomic Operations

```javascript
// Claim signal atomically
try {
  await fs.rename(signalPath, claimPath);
  // Successfully claimed
} catch (err) {
  if (err.code === "ENOENT") {
    // Another agent claimed first
  }
}
```

### 5. Clean Up Signal Files

```javascript
// After processing signal
await fs.unlink(requestSignalPath);
await fs.unlink(responseSignalPath);
```

---

## Future Enhancements

### Planned Features

- [ ] Multi-cloud support (AWS, Azure, GCP)
- [ ] End-to-end encryption for signal files
- [ ] Real-time sync via WebSockets (alternative to Dropbox)
- [ ] Automatic conflict resolution (ML-based)
- [ ] Signal file compression for large payloads
- [ ] Distributed tracing (OpenTelemetry)

### Experimental Features

- [ ] Peer-to-peer agent coordination (no cloud sync required)
- [ ] Blockchain-based approval verification
- [ ] Federated learning for task optimization

---

## Contributing

To add new coordination skills:

1. Create skill directory: `.claude/skills/coordination/<skill-name>/`
2. Follow standard skill structure (SKILL.md, README.md, EXAMPLES.md, references/, assets/)
3. Update this README with skill description
4. Add integration tests
5. Document security considerations

---

## Related Documentation

- [AGENTS.md](../../AGENTS.md) - Agent roles and permissions
- [VAULT_SKILLS_INTEGRATION.md](../vault/VAULT_SKILLS_INTEGRATION.md) - Skill integration patterns
- [vault/vault_state_manager](../vault/vault_state_manager/) - Low-level vault operations
- [vault/task_lifecycle_manager](../vault/task_lifecycle_manager/) - Task state transitions

---

## License

This skill category is part of the AI-Employee project. See LICENSE file for details.
