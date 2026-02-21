# Plan MD Generator - Impact Checklist

Use this checklist when deploying or modifying the `plan_md_generator` skill.

---

## Pre-Deployment Checklist

### Environment Configuration

- [ ] `VAULT_PATH` set in `.env` (absolute path to Obsidian vault)
- [ ] `Plans/` folder exists in vault
- [ ] Write permissions verified for agent user
- [ ] Optional: `PLAN_MAX_STEPS` configured (default 20)
- [ ] Optional: `PLAN_MIN_STEPS` configured (default 3)
- [ ] Optional: `PLAN_REQUIRE_HUMAN_APPROVAL` keywords configured
- [ ] Optional: LLM API key set if using AI-assisted planning
- [ ] All environment variables documented in `.env.example`

### File System Validation

- [ ] Vault directory structure verified:
  ```
  $VAULT_PATH/
    Needs_Action/     (input)
    Plans/            (write plans here)
    In_Progress/      (during execution)
    Pending_Approval/ (awaiting approval)
    Approved/         (human approved)
    Done/             (completed)
  ```
- [ ] No symlinks in Plans/ (security risk)
- [ ] File permissions allow agent write access to Plans/
- [ ] Plans/ folder has sufficient disk space

### Dependencies

- [ ] `vault_state_manager` skill available
- [ ] `needs_action_triage` skill available (for input metadata)
- [ ] Node.js >=18 (if using JavaScript implementation)
- [ ] Optional: LLM SDK installed (Anthropic, OpenAI, etc.)

### Security

- [ ] API keys stored in environment variables (not hardcoded)
- [ ] Secret detection regex patterns configured
- [ ] Approval gate logic enforced for finance/high-risk
- [ ] Path validation enabled (no traversal attacks)
- [ ] Tool inventory maintained (prevent hallucinated APIs)

---

## Runtime Validation Checklist

### Input Validation

- [ ] Triage data validated (required fields present)
- [ ] Category verified (email, whatsapp, finance, file_drop, general)
- [ ] Priority score validated (1-10 range)
- [ ] High-risk keywords detected (payment, delete, etc.)

### Plan Generation

- [ ] Step count within limits (3-20 steps)
- [ ] Each step has success criteria
- [ ] Approval gates synced with approval steps
- [ ] Dependencies validated (no cycles)
- [ ] Rollback plans for high-risk operations
- [ ] Effort estimates calculated
- [ ] Acceptance criteria defined

### Approval Detection

- [ ] Finance operations flagged (always require approval)
- [ ] Destructive operations flagged (delete, drop, remove)
- [ ] External communications flagged (email, notification)
- [ ] High-risk steps flagged (risk_level: high)
- [ ] approval_gates array populated correctly

### Secret Protection

- [ ] No API keys in plan content
- [ ] No passwords in tool references
- [ ] No financial account numbers
- [ ] Only references to secrets (e.g., "from .env")

### Plan Structure

- [ ] Goal defined (one-sentence objective)
- [ ] Context provided (background info)
- [ ] Acceptance criteria list (what defines "done")
- [ ] Steps ordered sequentially
- [ ] Dependencies tracked
- [ ] Resources listed (APIs, credentials, files)
- [ ] Risk assessment included

---

## Plan Validation Checklist

### Mandatory Checks (Plan Invalid If Failed)

- [ ] Goal is not empty
- [ ] Acceptance criteria has at least 1 item
- [ ] Steps count >= 3
- [ ] Steps count <= 20
- [ ] Each step has `id`, `action`, `type`, `status`
- [ ] Each step has `success_criteria`
- [ ] High-risk steps have `rollback_steps`
- [ ] Approval steps count matches approval_gates count
- [ ] Finance category requires human approval
- [ ] No circular dependencies in steps
- [ ] All referenced tools exist in tool inventory

### Quality Checks (Plan Degraded If Failed)

- [ ] Effort estimate provided
- [ ] Duration estimate in reasonable range (1-120 min)
- [ ] Risk assessment has at least 1 risk
- [ ] Resources section populated
- [ ] Validation section defined
- [ ] Rollback plan provided for high-risk

### Category-Specific Checks

**Email:**
- [ ] If reply needed, includes "draft" and "send" steps
- [ ] Send step requires approval
- [ ] Email API referenced in tools

**Finance:**
- [ ] Always requires human approval
- [ ] Amount verification step included
- [ ] Payment step requires approval
- [ ] Rollback includes "void transaction"

**File Drop:**
- [ ] File read/parse step included
- [ ] Data validation step included
- [ ] If import, requires approval

**WhatsApp:**
- [ ] Context gathering step included
- [ ] If response needed, requires approval

---

## Execution Checklist

### Pre-Execution

- [ ] Plan validated (all checks passed)
- [ ] Plan not stale (created within 2 days)
- [ ] All approval gates satisfied (if required)
- [ ] Plan in correct folder (Approved/ or In_Progress/)
- [ ] Required tools/APIs available
- [ ] Credentials accessible

### During Execution

- [ ] Each step status updated (pending → in_progress → completed)
- [ ] Execution log appended after each step
- [ ] Success criteria verified before marking completed
- [ ] Approval gates checked before approval steps
- [ ] Rollback executed on failure

### Post-Execution

- [ ] All acceptance criteria met
- [ ] Plan status updated (completed | failed)
- [ ] Plan moved to Done/ or Rejected/
- [ ] Execution log complete
- [ ] Results documented

---

## Approval Workflow Checklist

### Before Requesting Approval

- [ ] All pre-approval steps completed
- [ ] Approval gate reason documented
- [ ] Risk assessment reviewed
- [ ] Rollback plan verified

### During Approval

- [ ] Plan moved to Pending_Approval/
- [ ] Human notified (dashboard/email)
- [ ] Approval context provided (summary, risks)
- [ ] Timeout configured (e.g., 24 hours)

### After Approval

- [ ] Approval gate updated (approved_at, approved_by)
- [ ] Plan moved to Approved/
- [ ] Execution resumed
- [ ] Audit log updated

### If Rejected

- [ ] Rejection reason captured
- [ ] Plan moved to Rejected/
- [ ] Execution halted
- [ ] Human notified of rejection

---

## Security Checklist

### Secret Protection

- [ ] No secrets in `tools_needed` fields
- [ ] No secrets in `context` or `goal`
- [ ] No secrets in execution log
- [ ] Only references: "api_key (from .env)"

### Approval Enforcement

- [ ] Finance operations ALWAYS require approval
- [ ] Destructive operations require approval
- [ ] External communications require approval
- [ ] High-risk operations flagged

### Tool Validation

- [ ] All tools in `tools_needed` exist in inventory
- [ ] No shell commands in steps
- [ ] No eval/exec patterns
- [ ] No path traversal in file operations

### Audit Trail

- [ ] All plan generations logged
- [ ] All executions logged
- [ ] All approvals/rejections logged
- [ ] Logs immutable (append-only)

---

## Testing Checklist

### Unit Tests

- [ ] `decomposeTask()` tested for all categories
- [ ] `requiresApproval()` catches all high-risk keywords
- [ ] `estimateEffort()` returns reasonable values
- [ ] `detectCircularDependencies()` finds cycles
- [ ] `sanitizeSecrets()` detects all secret patterns
- [ ] `validatePlan()` catches all structural errors

### Integration Tests

- [ ] End-to-end plan generation from triage
- [ ] Plan execution with approval workflow
- [ ] Rollback on step failure
- [ ] Stale plan rejection
- [ ] Finance operation approval enforcement

### Edge Cases

- [ ] Triage data missing optional fields
- [ ] Very simple task (2-step minimum)
- [ ] Very complex task (20-step maximum)
- [ ] All steps require approval
- [ ] No steps require approval
- [ ] Circular dependencies
- [ ] Invalid tool references
- [ ] Stale plan (>2 days old)

### Error Scenarios

- [ ] LLM API down (fallback to template)
- [ ] Invalid triage data
- [ ] Plan file already exists (collision)
- [ ] Disk full (cannot write plan)
- [ ] Approval timeout (no response)

---

## Performance Checklist

### Generation Speed

- [ ] Plan generation <5s for simple tasks
- [ ] Plan generation <15s for complex tasks
- [ ] LLM response time monitored
- [ ] Fallback to templates if LLM slow

### File Size

- [ ] Plan files <100KB (typical)
- [ ] Execution log truncated if >1000 entries
- [ ] No large data embedded in plan

### Scalability

- [ ] Handles 100+ plans in Plans/ folder
- [ ] No memory leaks on repeated generation
- [ ] Concurrent plan generation supported

---

## Deployment Checklist

### Pre-Deployment

- [ ] All environment variables configured
- [ ] Vault structure validated
- [ ] Dependencies installed
- [ ] Tests passing
- [ ] Documentation reviewed

### Deployment Steps

1. [ ] Backup vault (in case of issues)
2. [ ] Deploy skill files to `.claude/skills/vault/plan_md_generator/`
3. [ ] Verify skill loaded (check agent logs)
4. [ ] Run smoke test (generate plan for test triage item)
5. [ ] Validate plan structure
6. [ ] Test approval workflow
7. [ ] Verify execution tracking

### Post-Deployment

- [ ] Monitor agent logs for errors
- [ ] Check plan generation performance
- [ ] Verify approval gates working
- [ ] Validate effort estimates accuracy
- [ ] Review generated plans for quality
- [ ] Test rollback procedures

### Rollback Plan

- [ ] Backup of previous skill version available
- [ ] Rollback procedure documented
- [ ] Vault backup preserved (pre-deployment)
- [ ] Plans in progress can complete

---

## Monitoring Checklist

### Metrics to Track

- [ ] Plans generated per day
- [ ] Average steps per plan
- [ ] Average generation time
- [ ] Approval gate frequency
- [ ] Approval/rejection ratio
- [ ] Plan completion rate
- [ ] Rollback frequency
- [ ] Stale plan count

### Alerts

- [ ] Alert if plan generation fails >3 times in 1 hour
- [ ] Alert if approval pending >24 hours
- [ ] Alert if plan execution fails repeatedly
- [ ] Alert if rollback executed
- [ ] Alert if secrets detected in plan

### Dashboard

- [ ] Daily plan generation summary
- [ ] Approval queue status
- [ ] In-progress plans list
- [ ] Failed plans with reasons
- [ ] Effort estimate accuracy over time

---

## Maintenance Checklist

### Weekly

- [ ] Review generated plans for quality
- [ ] Check approval gate accuracy
- [ ] Verify effort estimates vs actual
- [ ] Update tool inventory if new APIs added
- [ ] Review stale plans (>2 days old)

### Monthly

- [ ] Review rollback procedures
- [ ] Update high-risk keywords list
- [ ] Tune effort estimation formula
- [ ] Archive old completed plans
- [ ] Review error patterns

### Quarterly

- [ ] Re-validate category decomposition logic
- [ ] Update documentation
- [ ] Review security (secret detection)
- [ ] Audit approval workflows
- [ ] Update dependencies

---

## Troubleshooting Checklist

### Issue: Plans missing approval gates

- [ ] Check `requiresApproval()` logic
- [ ] Verify finance category detection
- [ ] Check high-risk keyword list
- [ ] Validate approval_gates sync

### Issue: Plans too granular (>20 steps)

- [ ] Review decomposition algorithm
- [ ] Check if task should be split
- [ ] Adjust PLAN_MAX_STEPS limit
- [ ] Group related actions

### Issue: Plans too simple (1-2 steps)

- [ ] Enforce minimum 3 steps
- [ ] Add validation/verification steps
- [ ] Check if task needs planning at all
- [ ] Review category-specific decomposition

### Issue: Effort estimates wildly off

- [ ] Review estimation formula
- [ ] Add complexity multipliers
- [ ] Check if human time included (shouldn't be)
- [ ] Calibrate based on historical data

### Issue: Secrets leaked in plans

- [ ] Check secret detection patterns
- [ ] Verify sanitization executed
- [ ] Review input triage data
- [ ] Update regex patterns

---

## Sign-Off Checklist

Before marking deployment complete:

- [ ] All pre-deployment checks passed
- [ ] All runtime validations working
- [ ] Security checklist completed
- [ ] Integration tests passed
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Approval workflows operational
- [ ] Rollback plan documented
- [ ] Team trained on skill usage
- [ ] Deployment log entry created

---

**Deployment Date:** ___________
**Deployed By:** ___________
**Version:** ___________
**Sign-Off:** ___________
