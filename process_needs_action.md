# Agent Skill: Process Needs Action

**Tier:** Bronze | **Version:** 1.0.0

---

## Skill Identity

| Field | Value |
|-------|-------|
| Name | `process_needs_action` |
| Trigger | Manual / scheduled scan |
| Scope | Vault-only (no external I/O) |
| Output mode | Draft only — all plans created as `status: pending` |

---

## Behavior

For each file in `/Needs_Action`:

### 1. Read & Analyse
- Read the file content
- Extract the **Objective** (first heading or first sentence)
- Extract **Steps** (bullet points, numbered items)
- If no structured steps exist, generate sensible defaults

### 2. Create Plan
Write a new file to `/Plans/plan-<filename>.md`:

```markdown
---
source: "original-filename.md"
created_at: "2026-02-22T12:00:00Z"
status: pending
---

# Plan: <Objective>

## Objective
<extracted objective>

## Steps
- [ ] Step 1
- [ ] Step 2
- [ ] Step 3

## Status
**pending** — awaiting human review or agent execution.
```

### 3. Archive Original
- Move the processed file from `/Needs_Action` to `/Done`
- Move its metadata sidecar (`.meta.md`) alongside it
- If a filename collision occurs in `/Done`, append a timestamp suffix

### 4. Log Action
Append a JSON entry to `/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-02-22T12:00:00.000000+00:00",
  "skill": "process_needs_action",
  "file": "task-name.md",
  "plan_path": "Plans/plan-task-name.md",
  "status": "processed"
}
```

On error, the entry includes an `"error"` field instead.

---

## Constraints

| Rule | Enforcement |
|------|-------------|
| No external actions | No API calls, no network, no shell |
| Vault-only I/O | All paths resolve inside vault root |
| No payments | Per Company Handbook financial rules |
| No deletions | Files move to Done/, never deleted |
| All actions logged | JSON log for every file processed |
| Draft-only output | Plans created with `status: pending` |

---

## Usage

### Python API

```python
from src.claude.agent_skills.process_needs_action import ProcessNeedsAction

skill = ProcessNeedsAction(vault_path="./AI-Employee-Vault")
result = skill.run({"patterns": ["*.md", "*.txt"]})

print(f"Processed: {result['processed']}/{result['found']}")
for plan in result["plans_created"]:
    print(f"  Plan: {plan}")
```

### From the CLI (via file_processor)

The skill integrates with the existing `FileProcessor` pipeline in `src/vault/file_processor.py`.

---

## Error Handling

- **Per-file isolation**: one failure does not block other files
- **Graceful fallback**: if content has no structure, generic steps are generated
- **Dual logging**: Python logger (console + file) and vault JSON log
- **Duplicate safety**: timestamp suffix prevents overwrites in Done/

---

## File Flow

```
Needs_Action/task.md          →  (read + analyse)
                               →  Plans/plan-task.md        [created]
                               →  Done/task.md              [moved]
                               →  Done/task.meta.md         [moved]
                               →  Logs/2026-02-22.json      [appended]
```
