# Silver Process Engine

You are executing the **Silver Process Engine** skill. Follow every step precisely.

## Behavior

1. **Scan** `/Needs_Action` for all `.md` files.

2. **Classify** each item's type:
   - Check YAML frontmatter `type:` field first
   - Fall back to filename pattern: `email-*` → `email`, `whatsapp-*` → `whatsapp`, else `file_drop`

3. **Assess Risk Level** (`low` / `medium` / `high`):
   - `high`: priority=high AND type=email
   - `medium`: priority=high or medium (non-email), OR type=file_drop with no priority
   - `low`: priority=low or type=email with no priority
   - **Escalate one level** if content contains: urgent, legal, payment, password, terminate, lawsuit, critical, breach, emergency

4. **Create Plan** in `/Plans/<slug>-<id>-plan.md`:
   ```
   ---
   plan_id: <8-char uuid>
   source_file: <original filename>
   item_type: email | file_drop | whatsapp
   risk_level: low | medium | high
   requires_approval: true | false
   status: pending_approval | ready_to_execute
   created_at: "<ISO8601>"
   ---

   # Plan: Process <Type>: <Subject>

   ## Objective
   ## Context Summary
   ## Risk Level
   ## Steps
   ## Requires Approval?
   ## Source Excerpt
   ```

5. **If risk_level is medium or high**: Create approval request in `/Pending_Approval/<slug>-<id>-approval.md`:
   ```
   ---
   approval_id: <8-char uuid>
   plan_file: Plans/<plan-filename>
   source_file: <original filename>
   risk_level: medium | high
   requested_at: "<ISO8601>"
   status: pending
   ---

   # Approval Request: <Subject>

   ## Why Approval Is Required
   ## Proposed Plan Summary
   ## Action Required
   - [ ] Review linked plan
   - [ ] Approve → move to /Approved
   - [ ] Reject → move to /Rejected
   ```

6. **Log** every action to `/Logs/silver-process-engine-<YYYY-MM-DD>.log` using `log_action()`.

7. **Move** the source file from `/Needs_Action/` to `/Done/` — only after plan creation succeeds.

## Hard Constraints

- **NEVER** execute real-world actions (no email sends, no API calls, no external writes)
- **NEVER** delete source files — only move to `/Done`
- **ALWAYS** create plan before moving to Done
- **ALWAYS** create approval request for medium and high risk
- If an item fails to process, log the error and leave it in `/Needs_Action`

## Execution

Run the engine:
```bash
PYTHONPATH=/tmp/gapi python3 .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py
```

Or dry run:
```bash
SILVER_PE_DRY_RUN=true python3 .claude/skills/silver/silver_process_engine/assets/silver_process_engine.py
```

After running, report:
- How many items were processed
- For each item: filename, type, risk level, plan filename
- Whether any approval requests were created
- Any errors encountered
