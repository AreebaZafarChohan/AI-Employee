# Orchestrator

You are executing the **Orchestrator** skill. Follow every step precisely.

## Behavior

### 1. Scan /Approved

List all `.md` files in `AI-Employee-Vault/Approved/`.

If no files found:
- Log: "No approvals to process"
- Exit cleanly

### 2. For Each Approval File

#### Step 2.1: Parse Frontmatter

Read the YAML frontmatter (between `---` markers).

Extract:
- `approval_id`
- `plan_file`
- `source_file`
- `risk_level`
- `requested_at`
- `status`

#### Step 2.2: Validate Approval

Check each required field exists and has correct type:

```python
REQUIRED_APPROVAL_FIELDS = {
    "approval_id": str,
    "plan_file": str,
    "source_file": str,
    "risk_level": str,
    "requested_at": str,
    "status": str,
}
```

**Expiry Check:**
```python
requested_at = datetime.fromisoformat(requested_at)
age_hours = (now - requested_at).total_seconds() / 3600
if age_hours > 24:
    reject("Approval expired")
```

**Risk Level Validation:**
```python
if risk_level not in ["low", "medium", "high"]:
    reject("Invalid risk_level")
```

#### Step 2.3: Load Plan File

Read plan from `AI-Employee-Vault/{plan_file}`.

Validate plan fields:
```python
REQUIRED_PLAN_FIELDS = {
    "plan_id": str,
    "item_type": str,  # email, file_drop, whatsapp
    "risk_level": str,
    "requires_approval": bool,
}
```

#### Step 2.4: Execute Action

Route based on `item_type`:

**If `email`:**
- Use MCP email server tools
- Call `send_email` or `draft_email` per plan
- Log result

**If `file_drop`:**
- Process file operations
- Log result

**If `whatsapp`:**
- Send WhatsApp message
- Log result

#### Step 2.5: Log Result

Append to `AI-Employee-Vault/Logs/orchestrator-YYYY-MM-DD.log`:

```json
{
  "timestamp": "2026-02-25T12:00:00Z",
  "approval_id": "abc123",
  "action": "execute",
  "status": "success",
  "action_type": "email_process",
  "plan_id": "xyz789"
}
```

#### Step 2.6: Move to Done

Add execution metadata to frontmatter:
```yaml
executed_at: "2026-02-25T12:00:00Z"
execution_status: "completed"
moved_to_done_from: "Approved"
```

Move file to `AI-Employee-Vault/Done/`.

### 3. Handle Failures

**Validation Failure:**
- Log error with details
- Move to `/Rejected` with `rejection_reason` field

**Execution Failure:**
- Log error with stack trace
- Keep in `/Approved` for retry
- Do NOT move to Done

**Missing Plan File:**
- Log "File not found" error
- Move to `/Rejected`

## Safety Constraints

1. **Never execute without approval** — Only process files in `/Approved`
2. **Reject expired approvals** — >24 hours old
3. **Reject missing fields** — All required fields must be present
4. **Log all failures** — Detailed error logging
5. **Idempotent** — Safe to retry

## Usage

```bash
# Run one cycle
python orchestrator.py

# Watch mode (continuous)
python orchestrator.py --watch --interval 30

# Dry run (test)
DRY_RUN=true python orchestrator.py

# With shell wrapper
.claude/skills/silver/orchestrator/assets/run.sh --watch --interval 60
```

## Output Format

After each cycle, report:

```
Orchestrator Cycle Complete
────────────────────────────
Processed: 3 files
Succeeded: 2
Failed: 0
Rejected: 1 (validation failure)

Logs: AI-Employee-Vault/Logs/orchestrator-2026-02-25.log
```
