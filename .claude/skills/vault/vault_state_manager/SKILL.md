---
name: vault_state_manager
description: Provides structured access to Obsidian vault markdown files for the Digital FTE workflow. Supports read, write, list, and move operations across lifecycle folders (Needs_Action, In_Progress, Done) with safe failure handling.
---

# Vault State Manager

## Purpose

This skill provides agents with standardized, safe operations for interacting with the Obsidian vault that implements the Digital FTE workflow. It enforces the claim-by-move protocol, single-writer rules, and idempotency requirements defined in AGENTS.md.

The skill is designed to be used by both Local Executive Agent (lex) and Cloud Executive Agent (cex) when they need to:
- List pending work
- Read file contents and metadata
- Update file states
- Move files between lifecycle folders

## When to Use This Skill

Use `vault_state_manager` when:

- **Listing pending work**: Get all files in `Needs_Action/`, `Plans/`, `In_Progress/`, `Pending_Approval/`, `Approved/`, `Done/`
- **Reading task details**: Parse markdown or JSON files for metadata, content, and status
- **Writing progress updates**: Append status updates to files in `In_Progress/`
- **Moving files between stages**: Transition files through the lifecycle (respecting agent permissions)
- **Checking for conflicts**: Verify if a plan ID already exists before creating new work
- **Reading logs**: Access append-only logs for audit trails
- **Querying file metadata**: Get timestamps, file sizes, last modified dates

Do NOT use this skill when:

- **Direct file system operations**: Use native Read/Write tools for simple single-file operations
- **Non-vault files**: This skill is vault-specific; use Bash/Read/Write for other directories
- **Secret management**: Never use this to read/write `.env` files or credentials
- **Dashboard updates**: Dashboard.md is human-maintained; agents must not modify it

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"  # Root directory of Obsidian vault

# Optional
VAULT_CLAIM_TIMEOUT_MS="5000"         # File lock claim timeout
VAULT_READ_TIMEOUT_MS="3000"          # Read operation timeout
VAULT_LOG_LEVEL="info"                # debug | info | warn | error
```

**Secrets Management:**

- This skill does NOT handle secrets
- Never read or write to `.env` via this skill
- Agent credentials must be managed outside vault operations
- Vault paths should be absolute; no credential interpolation

**Variable Discovery Process:**
```bash
# Check vault configuration
cat .env | grep VAULT_PATH
ls -la "$VAULT_PATH"  # Verify vault structure

# Verify folder structure exists
for dir in Needs_Action Plans In_Progress Pending_Approval Approved Rejected Done Updates Logs Archive; do
  test -d "$VAULT_PATH/$dir" || echo "Missing: $dir"
done
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Vault State Manager
  └── Filesystem (local disk)
      ├── Obsidian vault directory (read/write)
      ├── No external services
      └── No network dependencies
```

**Topology Notes:**
- All operations are synchronous filesystem I/O
- No remote calls or API dependencies
- Works in Docker containers if vault is mounted as volume
- Compatible with network filesystems (NFS, SMB) but performance may degrade

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as persistent volume: `-v /host/vault:/vault`
- Use volume claims in Kubernetes: `PersistentVolumeClaim`
- Ensure file permissions allow container user to read/write
- Consider shared volumes for multi-agent access (with claim-by-move coordination)

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication required (local filesystem access)
- Permissions controlled by OS-level file permissions
- Agent authorization enforced by folder write rules (see AGENTS.md §3)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Race conditions** | Atomic file moves via `mv` (POSIX guarantee) |
| **Partial writes** | Write to temp file, then rename atomically |
| **Concurrent access** | Claim-by-move protocol enforces single-writer |
| **Path traversal** | Validate all paths are within VAULT_PATH |
| **File injection** | Reject paths with `..`, absolute paths, or symlinks |
| **Log tampering** | Logs are append-only; detect size decreases |

**Validation Rules:**

Before ANY file operation:
```javascript
// Pseudo-code validation
function validatePath(requestedPath) {
  const resolved = path.resolve(VAULT_PATH, requestedPath);
  if (!resolved.startsWith(VAULT_PATH)) {
    throw new Error("Path traversal detected");
  }
  if (fs.lstatSync(resolved).isSymbolicLink()) {
    throw new Error("Symlinks not allowed");
  }
  return resolved;
}
```

**Agent Permission Enforcement:**

Per AGENTS.md §3, agents have different write permissions:

| Agent | Can Write To | Cannot Write To |
|-------|--------------|-----------------|
| `lex` | `Plans/`, `In_Progress/`, `Pending_Approval/`, `Logs/` | `Approved/`, `Rejected/`, `Done/`, `Dashboard.md` |
| `cex` | NONE (read-only via lex proxy) | ALL |
| `orch` | Can MOVE files: `Approved/` → `In_Progress/` → `Done/` | Cannot CREATE files |
| Watchers | `Needs_Action/`, `Updates/`, `Logs/` | All other folders |
| `human` | ALL | N/A (no restrictions) |

This skill MUST enforce these rules by checking agent identity before writes.

## Blueprints & Templates Used

### Blueprint: Vault File Structure

**Purpose:** Standardize metadata and content format for vault files

**Template Variables:**
```yaml
# File metadata (JSON front-matter for .json files, YAML for .md)
plan_id: "{{PLAN_ID}}"                    # Unique identifier (timestamp-based)
created_at: "{{TIMESTAMP_ISO}}"           # ISO 8601 creation time
created_by: "{{AGENT_NAME}}"              # Agent that created this file
status: "{{STATUS}}"                      # needs_action | planned | in_progress | pending_approval | approved | done | rejected
priority: "{{PRIORITY}}"                  # low | medium | high | critical
tags: ["{{TAG1}}", "{{TAG2}}"]            # Searchable tags
source: "{{SOURCE_TYPE}}"                 # email | message | file | manual
autonomy_required: "{{AUTONOMY_TIER}}"    # bronze | silver | gold | platinum

# Content structure
title: "{{TASK_TITLE}}"
goal: "{{TASK_GOAL}}"
steps:
  - action: "{{ACTION_1}}"
    status: "{{STEP_STATUS}}"
  - action: "{{ACTION_2}}"
    status: "{{STEP_STATUS}}"

# Completion metadata (added when moved to Done/)
completed_at: "{{TIMESTAMP_ISO}}"
completed_by: "{{AGENT_NAME}}"
outcome: "{{SUCCESS|FAILURE}}"
log_reference: "{{LOG_FILE_PATH}}"
```

**Impact Notes:**
- All timestamps must be ISO 8601 format (UTC)
- Plan IDs must be unique; use collision detection
- Status transitions must follow lifecycle: needs_action → planned → in_progress → pending_approval → approved → done
- Cannot skip stages (e.g., cannot go directly from needs_action to done)

### Blueprint: Claim-by-Move Protocol

**Purpose:** Ensure single-writer access via atomic file moves

**When to Use:**
- Moving files between lifecycle folders
- Claiming work for processing
- Releasing completed work

**Implementation Pattern:**
```bash
# Claim file for processing (lex claims from Needs_Action)
move_file() {
  local src="$VAULT_PATH/Needs_Action/file.json"
  local dst="$VAULT_PATH/Plans/file.json"

  # Atomic move (POSIX guarantee: fails if dst exists)
  if mv "$src" "$dst"; then
    echo "Claimed successfully"
    return 0
  else
    echo "Claim failed (already claimed or file missing)"
    return 1
  fi
}
```

**Impact Notes:**
- `mv` is atomic on same filesystem (POSIX)
- If vault crosses filesystems, use `mv` with fallback to copy+delete
- Always check return code; failed move means conflict
- Never use `cp` for claiming; it creates race conditions

### Blueprint: Read Operation (Safe)

**Purpose:** Read file contents with validation and error handling

**Template:**
```javascript
async function readVaultFile(relativePath, agentName) {
  const fullPath = validatePath(relativePath);

  // Check agent read permissions
  if (!canAgentRead(agentName, fullPath)) {
    throw new PermissionError(`${agentName} cannot read ${relativePath}`);
  }

  try {
    const content = await fs.readFile(fullPath, 'utf8');
    const metadata = {
      size: fs.statSync(fullPath).size,
      modified: fs.statSync(fullPath).mtime,
      path: relativePath
    };

    return { content, metadata };
  } catch (err) {
    if (err.code === 'ENOENT') {
      throw new FileNotFoundError(`File not found: ${relativePath}`);
    }
    throw new ReadError(`Failed to read ${relativePath}: ${err.message}`);
  }
}
```

**Impact Notes:**
- Always validate paths before reading
- Return structured error types (not generic errors)
- Include metadata with every read (for caching/validation)
- Never expose full filesystem paths to agents (use relative paths)

### Blueprint: Write Operation (Safe)

**Purpose:** Write file contents atomically with validation

**Template:**
```javascript
async function writeVaultFile(relativePath, content, agentName) {
  const fullPath = validatePath(relativePath);
  const folder = path.dirname(fullPath);

  // Check agent write permissions per AGENTS.md §3
  if (!canAgentWrite(agentName, fullPath)) {
    throw new PermissionError(`${agentName} cannot write to ${relativePath}`);
  }

  // Check folder writability
  const allowedFolders = getAgentWritableFolders(agentName);
  if (!allowedFolders.some(f => folder.includes(f))) {
    throw new PermissionError(`${agentName} cannot write to folder: ${folder}`);
  }

  // Atomic write via temp file
  const tempPath = `${fullPath}.tmp`;
  try {
    await fs.writeFile(tempPath, content, 'utf8');
    await fs.rename(tempPath, fullPath);  // Atomic on same filesystem

    logWrite(agentName, relativePath, content.length);
    return { success: true, path: relativePath };
  } catch (err) {
    await fs.unlink(tempPath).catch(() => {});  // Clean up temp file
    throw new WriteError(`Failed to write ${relativePath}: ${err.message}`);
  }
}
```

**Impact Notes:**
- Always write to `.tmp` file first, then rename (atomic)
- Log all writes for audit trail
- Clean up temp files on failure
- Validate agent permissions BEFORE attempting write

### Blueprint: List Files in Folder

**Purpose:** List all files in a lifecycle folder with metadata

**Template:**
```javascript
async function listFolderFiles(folderName, options = {}) {
  const folderPath = validatePath(folderName);

  // Validate folder is in allowed set
  const allowedFolders = [
    'Needs_Action', 'Plans', 'In_Progress',
    'Pending_Approval', 'Approved', 'Rejected',
    'Done', 'Updates', 'Logs', 'Archive'
  ];

  if (!allowedFolders.includes(folderName)) {
    throw new InvalidFolderError(`Invalid folder: ${folderName}`);
  }

  try {
    const entries = await fs.readdir(folderPath, { withFileTypes: true });
    const files = [];

    for (const entry of entries) {
      if (entry.isFile()) {
        const filePath = path.join(folderPath, entry.name);
        const stats = await fs.stat(filePath);

        files.push({
          name: entry.name,
          path: path.join(folderName, entry.name),
          size: stats.size,
          modified: stats.mtime,
          created: stats.birthtime
        });
      }
    }

    // Sort by creation time (oldest first)
    files.sort((a, b) => a.created - b.created);

    // Apply filters if requested
    if (options.extension) {
      return files.filter(f => f.name.endsWith(options.extension));
    }

    return files;
  } catch (err) {
    if (err.code === 'ENOENT') {
      throw new FolderNotFoundError(`Folder not found: ${folderName}`);
    }
    throw new ListError(`Failed to list ${folderName}: ${err.message}`);
  }
}
```

**Impact Notes:**
- Always return sorted results (oldest first) for deterministic processing
- Include creation time (not just modified time)
- Support filtering by extension (.json, .md)
- Return relative paths (within vault), not absolute paths

### Blueprint: Move File Between Folders

**Purpose:** Implement claim-by-move protocol for lifecycle transitions

**Template:**
```javascript
async function moveFile(srcFolder, filename, dstFolder, agentName) {
  const srcPath = validatePath(path.join(srcFolder, filename));
  const dstPath = validatePath(path.join(dstFolder, filename));

  // Validate lifecycle transition is legal
  const legalTransitions = {
    'Needs_Action': ['Plans'],
    'Plans': ['In_Progress', 'Rejected'],
    'In_Progress': ['Pending_Approval', 'Rejected'],
    'Pending_Approval': ['Approved', 'Rejected'],
    'Approved': ['In_Progress'],
    'In_Progress': ['Done', 'Rejected'],
    'Done': ['Archive'],
    'Rejected': ['Archive']
  };

  if (!legalTransitions[srcFolder]?.includes(dstFolder)) {
    throw new IllegalTransitionError(
      `Cannot move from ${srcFolder} to ${dstFolder}`
    );
  }

  // Check agent permissions for this transition
  if (!canAgentMove(agentName, srcFolder, dstFolder)) {
    throw new PermissionError(
      `${agentName} cannot move files from ${srcFolder} to ${dstFolder}`
    );
  }

  // Atomic move
  try {
    await fs.rename(srcPath, dstPath);
    logMove(agentName, srcPath, dstPath);
    return { success: true, newPath: path.join(dstFolder, filename) };
  } catch (err) {
    if (err.code === 'ENOENT') {
      throw new FileNotFoundError(`Source file not found: ${srcPath}`);
    }
    if (err.code === 'EEXIST') {
      throw new ConflictError(`Destination file already exists: ${dstPath}`);
    }
    throw new MoveError(`Failed to move file: ${err.message}`);
  }
}
```

**Impact Notes:**
- Enforce state machine transitions (no skipping stages)
- Log all moves for audit trail
- Return new path on success
- Detect conflicts (EEXIST) and return structured error

## Validation Checklist

### Mandatory Checks (Skill Invalid If Failed)

- [x] Uses canonical folder structure: `SKILL.md`, `references/`, `assets/`
- [x] Contains complete impact analysis (Env, Network, Auth)
- [x] No `localhost` hardcoding in any template (N/A - filesystem only)
- [x] No secrets or passwords in templates or examples
- [x] Auth/CORS impact explicitly documented (filesystem permissions)
- [x] Supports containerization (Docker volume mounts documented)
- [x] Gotchas document has known failures and mitigation
- [x] Anti-patterns list common mistakes
- [x] All templates use parameterized placeholders `{{VARIABLE}}`
- [x] Templates include IMPACT NOTES comments
- [x] References folder has all three files (patterns, impact-checklist, gotchas)
- [x] SKILL.md contains all 9 required sections

### Quality Checks (Skill Degraded If Failed)

- [x] Default values only for non-sensitive variables
- [x] `.example` files show realistic placeholder values
- [x] Variable naming follows consistent pattern
- [x] Ports documented (N/A - no network ports)
- [x] Dependencies have startup order documented
- [x] Health check endpoints identified (N/A - no health checks for filesystem)
- [x] Graceful degradation scenarios outlined

### Environment Readiness Checks

- [x] Variables compatible with:
  - [x] Local development (`.env` files)
  - [x] Docker Compose (volume mounts)
  - [x] Kubernetes (PersistentVolumeClaim)
- [x] Network configuration works in: (N/A - filesystem only)
- [x] Auth configuration handles: (filesystem permissions documented)

### Vault-Specific Checks

- [x] Enforces agent write permissions per AGENTS.md §3
- [x] Implements claim-by-move protocol correctly
- [x] Validates all paths to prevent traversal attacks
- [x] Uses atomic operations for writes and moves
- [x] Logs all state-changing operations
- [x] Returns structured errors (not generic exceptions)
- [x] Detects and reports conflicts (file already exists)
- [x] Supports idempotency (safe to retry operations)

## Anti-Patterns

### ❌ Direct file writes without temp file

**Problem:** Partial writes leave corrupted state

**Example:**
```javascript
// WRONG - not atomic
await fs.writeFile(fullPath, content);

// CORRECT - atomic via rename
const tempPath = `${fullPath}.tmp`;
await fs.writeFile(tempPath, content);
await fs.rename(tempPath, fullPath);
```

### ❌ Copy instead of move for claiming

**Problem:** Creates race conditions; two agents can claim same file

**Example:**
```bash
# WRONG - not atomic
cp source dest && rm source

# CORRECT - atomic
mv source dest
```

### ❌ Skipping path validation

**Problem:** Path traversal attacks possible

**Example:**
```javascript
// WRONG - no validation
const fullPath = path.join(VAULT_PATH, userInput);

// CORRECT - validate first
const fullPath = validatePath(userInput);
if (!fullPath.startsWith(VAULT_PATH)) throw new Error("Invalid path");
```

### ❌ Ignoring agent permissions

**Problem:** Agents can write to folders they shouldn't access

**Example:**
```javascript
// WRONG - no permission check
await fs.writeFile(path.join(VAULT_PATH, 'Approved', 'file.json'), content);

// CORRECT - check permissions
if (!canAgentWrite(agentName, 'Approved')) {
  throw new PermissionError("lex cannot write to Approved/");
}
```

### ❌ Not handling file conflicts

**Problem:** Overwriting existing files silently

**Example:**
```javascript
// WRONG - overwrites silently
await fs.rename(src, dst);

// CORRECT - detect conflicts
try {
  await fs.rename(src, dst);
} catch (err) {
  if (err.code === 'EEXIST') {
    throw new ConflictError(`File already exists: ${dst}`);
  }
}
```

### ❌ Exposing absolute paths to agents

**Problem:** Leaks filesystem structure; breaks when vault moves

**Example:**
```javascript
// WRONG - returns absolute path
return { path: '/Users/john/vault/Plans/file.json' };

// CORRECT - returns relative path
return { path: 'Plans/file.json' };
```

### ❌ No logging of state changes

**Problem:** Cannot audit who did what

**Example:**
```javascript
// WRONG - no audit trail
await fs.rename(src, dst);

// CORRECT - log all changes
await fs.rename(src, dst);
logMove(agentName, src, dst);
```

### ❌ Not cleaning up temp files on failure

**Problem:** Leaves garbage files in vault

**Example:**
```javascript
// WRONG - temp file persists on failure
await fs.writeFile(tempPath, content);
throw new Error("Something failed");  // temp file orphaned

// CORRECT - cleanup on failure
try {
  await fs.writeFile(tempPath, content);
  await fs.rename(tempPath, fullPath);
} catch (err) {
  await fs.unlink(tempPath).catch(() => {});  // Clean up
  throw err;
}
```

### ❌ Illegal state transitions

**Problem:** Files skip required approval stages

**Example:**
```javascript
// WRONG - skips approval
moveFile('Needs_Action', file, 'Done');  // Should be rejected

// CORRECT - enforce state machine
if (!isLegalTransition(srcFolder, dstFolder)) {
  throw new IllegalTransitionError(`Cannot skip from ${srcFolder} to ${dstFolder}`);
}
```

## Enforcement Behavior

When this skill is active:

### Agent Responsibilities

1. **Always validate paths** before any filesystem operation
2. **Check permissions** against AGENTS.md §3 before writes/moves
3. **Use atomic operations** for all writes and moves
4. **Log all state changes** to audit trail
5. **Return structured errors** (not generic exceptions)
6. **Clean up temp files** on failure
7. **Respect single-writer rule** (never edit files in folders owned by other agents)

### User Expectations

- All vault operations are safe and atomic
- Failed operations leave vault in consistent state
- Agent permissions are strictly enforced
- Audit logs track all state changes
- Path traversal attacks are prevented
- Race conditions are avoided via claim-by-move

### Error Handling

All functions must return structured errors:

```typescript
// Error types
class PermissionError extends Error {}
class PathTraversalError extends Error {}
class FileNotFoundError extends Error {}
class ConflictError extends Error {}
class IllegalTransitionError extends Error {}
class ReadError extends Error {}
class WriteError extends Error {}
class MoveError extends Error {}
```

Agents must catch these errors and handle appropriately:
- `PermissionError`: Log and halt (do not retry)
- `ConflictError`: Log and retry with new plan ID
- `FileNotFoundError`: Log and skip (file may have been claimed by another agent)
- Other errors: Log and report to human via `Pending_Approval/`

## Integration with AGENTS.md

This skill implements the vault protocol defined in AGENTS.md §4:

- **§4.2 Claim-by-Move Rule**: Implemented via `moveFile()` function
- **§4.3 Single-Writer Rules**: Enforced via `canAgentWrite()` permission checks
- **§4.4 Conflict Avoidance**: Implemented via plan ID collision detection
- **§4.5 Idempotency Expectations**: All operations are safe to retry

All agents using this skill MUST respect the jurisdictions defined in AGENTS.md §3.

## Usage Examples

See `references/patterns.md` for concrete code examples and workflow patterns.
