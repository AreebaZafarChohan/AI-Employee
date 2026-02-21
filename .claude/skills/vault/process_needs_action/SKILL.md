# Process Needs Action Skill

**Version:** 1.0.0
**Tier:** Bronze
**Category:** vault

## Purpose

Reads all files in `Needs_Action/`, analyses each one, creates a structured Plan in `Plans/`, moves the original to `Done/`, and logs every action to `Logs/YYYY-MM-DD.json`.

## Trigger

Manual invocation or scheduled scan. No autonomous execution.

## Behavior

```
for each file in Needs_Action/:
    1. Read file content
    2. Analyse → extract Objective + Steps
    3. Write Plans/plan-<name>.md
    4. Move original file → Done/
    5. Move metadata sidecar (.meta.md) → Done/
    6. Append JSON log entry → Logs/YYYY-MM-DD.json
```

## Plan File Format

```markdown
---
source: "original-filename.md"
created_at: "2026-02-22T12:00:00Z"
status: pending
---

# Plan: <Objective>

## Objective
<extracted or inferred objective>

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Status
**pending** — awaiting human review or agent execution.
```

## Log Entry Format

```json
{
  "timestamp": "2026-02-22T12:00:00.000000+00:00",
  "skill": "process_needs_action",
  "file": "task-name.md",
  "plan_path": "/path/to/Plans/plan-task-name.md",
  "status": "processed"
}
```

## Constraints (Bronze Tier)

1. **No external actions** — no API calls, no network, no shell commands.
2. **Vault-only I/O** — all reads and writes stay inside the vault directory.
3. **No payments or financial execution** — per Company Handbook.
4. **No deletions** — files are moved to Done/, never deleted.
5. **All actions logged** — every file touch produces a JSON log entry.
6. **Draft-only output** — plans are created with `status: pending`.

## Inputs

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vault_path` | string | — | Absolute path to the Obsidian vault |
| `patterns` | list | `["*.md", "*.txt"]` | Glob patterns for files to process |

## Outputs

| Field | Type | Description |
|-------|------|-------------|
| `success` | bool | Overall success flag |
| `found` | int | Files found in Needs_Action |
| `processed` | int | Files successfully processed |
| `errors` | list | Error messages for failed files |
| `plans_created` | list | Paths to created plan files |

## Error Handling

- Per-file try/catch: one failure does not block the rest.
- Errors are logged to both Python logger and Logs/YYYY-MM-DD.json.
- Metadata sidecars (.meta.md) are moved alongside their source file.
- Duplicate filenames in Done/ are resolved with a timestamp suffix.

## Dependencies

- `src/claude/agent_skills/process_needs_action.py` — Python implementation
- `src/utils/file_utils.py` — file operations
- `src/utils/logger.py` — structured logging
