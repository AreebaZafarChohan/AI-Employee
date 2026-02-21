# Vault State Manager Skill

A standardized Claude Code Agent Skill for managing Obsidian vault markdown files in a Digital FTE workflow.

## Quick Start

```bash
# 1. Initialize vault structure
VAULT_PATH=/path/to/vault bash assets/vault-init.sh

# 2. Configure environment
cp assets/.env.example .env
# Edit .env and set VAULT_PATH

# 3. Use in your agent
const vaultManager = require('./vault-state-manager');

// List pending work
const files = await vaultManager.listFolderFiles('Needs_Action');

// Read file
const { content, metadata } = await vaultManager.readVaultFile('Plans/plan-123.json', 'lex');

// Move file (claim work)
await vaultManager.moveFile('Needs_Action', 'file.json', 'Plans', 'lex');

// Write file atomically
await vaultManager.writeVaultFile('Plans/plan-456.json', jsonContent, 'lex');
```

## Documentation

| Document | Purpose |
|----------|---------|
| [`SKILL.md`](./SKILL.md) | Complete skill specification |
| [`references/patterns.md`](./references/patterns.md) | Code examples & workflows |
| [`references/impact-checklist.md`](./references/impact-checklist.md) | Deployment checklists |
| [`references/gotchas.md`](./references/gotchas.md) | Known issues & workarounds |

## Key Features

✅ **Safe Operations**
- Atomic file moves (claim-by-move protocol)
- Atomic writes (temp file + rename)
- Path validation (prevents traversal attacks)
- Agent permission enforcement

✅ **Multi-Agent Coordination**
- Conflict detection (file already claimed)
- Single-writer enforcement
- Idempotent operations (safe to retry)

✅ **Lifecycle Management**
- State machine enforcement (legal transitions only)
- Lifecycle folders: Needs_Action → Plans → In_Progress → Pending_Approval → Approved → Done
- Rejection paths: any stage → Rejected

✅ **Observability**
- Structured error types (PermissionError, ConflictError, etc.)
- Audit logging (all state changes logged)
- Metadata tracking (timestamps, agent identity)

## Folder Structure

```
vault/
├── Dashboard.md                  # Human-maintained status
├── Needs_Action/                 # Inbox from watchers
│   ├── emails/
│   ├── messages/
│   ├── files/
│   └── finance-alerts/
├── Plans/                        # Draft plans
├── In_Progress/                  # Active work
├── Pending_Approval/             # Awaiting human review
├── Approved/                     # Human approved
├── Rejected/                     # Human rejected
├── Done/                         # Completed work
├── Updates/                      # Non-actionable signals
├── Logs/                         # Append-only audit trail
└── Archive/                      # Old completed work
```

## Agent Permissions

Per AGENTS.md §3, agents have restricted write access:

| Agent | Can Write To | Cannot Write To |
|-------|--------------|-----------------|
| `lex` | Plans/, In_Progress/, Pending_Approval/, Logs/ | Approved/, Rejected/, Done/ |
| `cex` | NONE (read-only via lex proxy) | ALL |
| `orch` | Can MOVE files: Approved/ → In_Progress/ → Done/ | Cannot CREATE files |
| Watchers | Needs_Action/, Updates/, Logs/ | All other folders |
| `human` | ALL | N/A |

## API Reference

### List Files

```javascript
await vaultManager.listFolderFiles(folderName, options?)
```

- `folderName`: One of: Needs_Action, Plans, In_Progress, etc.
- `options.extension`: Filter by file extension (e.g., '.json')
- Returns: Array of `{ name, path, size, modified, created }`

### Read File

```javascript
await vaultManager.readVaultFile(relativePath, agentName)
```

- `relativePath`: Path relative to vault root (e.g., 'Plans/plan-123.json')
- `agentName`: Agent identity (for permission check)
- Returns: `{ content: string, metadata: { size, modified, path } }`

### Write File

```javascript
await vaultManager.writeVaultFile(relativePath, content, agentName)
```

- `relativePath`: Path relative to vault root
- `content`: File content (string)
- `agentName`: Agent identity (for permission check)
- Returns: `{ success: true, path: string }`

### Move File

```javascript
await vaultManager.moveFile(srcFolder, filename, dstFolder, agentName)
```

- `srcFolder`: Source folder name (e.g., 'Needs_Action')
- `filename`: File name (e.g., 'task-001.json')
- `dstFolder`: Destination folder name (e.g., 'Plans')
- `agentName`: Agent identity (for permission check)
- Returns: `{ success: true, newPath: string }`

## Error Types

```typescript
class PermissionError extends Error {}      // Agent lacks permission
class PathTraversalError extends Error {}   // Path validation failed
class FileNotFoundError extends Error {}    // File doesn't exist (or already claimed)
class ConflictError extends Error {}        // File already exists at destination
class IllegalTransitionError extends Error {} // Invalid state transition
class ReadError extends Error {}            // Read operation failed
class WriteError extends Error {}           // Write operation failed
class MoveError extends Error {}            // Move operation failed
```

## Assets

| File | Purpose |
|------|---------|
| `.env.example` | Configuration template |
| `plan-file.template.json` | Plan file structure |
| `completion-update.template.json` | Completion metadata |
| `docker-compose.example.yml` | Multi-agent Docker setup |
| `k8s-vault-pvc.template.yml` | Kubernetes deployment |
| `vault-init.sh` | Vault initialization script |
| `gitignore.example` | Git ignore rules |

## Deployment Scenarios

### Local Development

```bash
# Initialize vault
VAULT_PATH=./vault bash assets/vault-init.sh

# Configure
cp assets/.env.example .env
# Edit .env: VAULT_PATH=./vault

# Run agents
node agents/lex.js
```

### Docker Compose

```bash
# Use provided template
cp assets/docker-compose.example.yml docker-compose.yml
# Edit docker-compose.yml: update paths, credentials

# Start all agents
docker-compose up -d

# Monitor logs
docker-compose logs -f lex
```

### Kubernetes

```bash
# Use provided template
cp assets/k8s-vault-pvc.template.yml k8s-vault-pvc.yml
# Edit k8s-vault-pvc.yml: update namespace, storage class, registry

# Deploy
kubectl apply -f k8s-vault-pvc.yml

# Verify
kubectl get pvc vault-storage
kubectl get pods -l app=lex-agent
```

## Best Practices

1. ✅ **Always validate paths** before operations
2. ✅ **Check permissions** before writes/moves
3. ✅ **Use atomic operations** (write to temp, then rename)
4. ✅ **Handle conflicts gracefully** (file already claimed)
5. ✅ **Log all state changes** for audit trail
6. ✅ **Return structured errors** (not generic exceptions)
7. ✅ **Clean up temp files** on failure
8. ✅ **Retry transient errors** with backoff
9. ✅ **Never skip lifecycle stages** (enforce state machine)
10. ✅ **Use relative paths** in all APIs (not absolute)

## Common Workflows

### Workflow 1: Lex Processes Email

```
1. Watcher writes email → Needs_Action/emails/
2. Lex reads email
3. Lex creates plan → Plans/
4. Lex moves plan → In_Progress/
5. Lex executes steps
6. Lex moves plan → Pending_Approval/
7. Human approves → Approved/
8. Orchestrator claims plan → In_Progress/
9. Orchestrator executes via MCP
10. Orchestrator moves plan → Done/
```

### Workflow 2: Human Approval

```bash
# Human reviews plan
cat vault/Pending_Approval/plan-123.json

# Human approves
mv vault/Pending_Approval/plan-123.json vault/Approved/

# Or rejects
mv vault/Pending_Approval/plan-123.json vault/Rejected/
echo "Too risky" > vault/Rejected/plan-123.rejection.md
```

## Troubleshooting

### Issue: Permission Denied

```
Error: EACCES: permission denied
```

**Solution:** Check file ownership and permissions

```bash
# Fix ownership (Docker)
sudo chown -R $(id -u):$(id -g) vault/

# Fix permissions
chmod -R u+rw vault/
```

### Issue: File Not Found (After List)

```
Error: FileNotFoundError: File not found
```

**Solution:** Another agent claimed file (race condition)

```javascript
// This is NOT an error, just concurrent access
try {
  await moveFile('Needs_Action', file, 'Plans', 'lex');
} catch (err) {
  if (err instanceof FileNotFoundError) {
    console.log('Already claimed by another agent');
    // Continue to next file
  }
}
```

### Issue: Disk Full

```
Error: ENOSPC: no space left on device
```

**Solution:** Archive old plans, rotate logs

```bash
# Archive old completed plans
mv vault/Done/* vault/Archive/

# Compress logs
gzip vault/Logs/*.json
```

## Security Considerations

⚠️ **Path Traversal Prevention**
- All paths validated before use
- `..` and absolute paths rejected
- Symlinks rejected

⚠️ **Agent Permission Enforcement**
- Checked before every write/move
- Defined in AGENTS.md §3
- Enforced by vault manager

⚠️ **Audit Trail**
- All state changes logged
- Logs are append-only
- Cannot be tampered

⚠️ **Secrets Management**
- Never read/write .env via vault manager
- Never write credentials to vault
- Use external secret stores (Kubernetes secrets, etc.)

## License

This skill follows the Digital FTE project license. See project root for details.

## Related Documentation

- [AGENTS.md](../../../../AGENTS.md) - Agent jurisdictions and rules
- [CLAUDE.md](../../../../CLAUDE.md) - Claude agent rules
- [Skill Standard Enforcer](../../meta/skill-standard-enforcer/SKILL.md) - Skill creation standard

## Support

For issues or questions:
1. Check [gotchas.md](./references/gotchas.md) for known issues
2. Review [patterns.md](./references/patterns.md) for examples
3. Consult [SKILL.md](./SKILL.md) for complete specification
