# Needs Action Triage - Impact Checklist

Use this checklist when deploying or modifying the `needs_action_triage` skill.

---

## Pre-Deployment Checklist

### Environment Configuration

- [ ] `VAULT_PATH` set in `.env` (absolute path to Obsidian vault)
- [ ] `Needs_Action/` folder exists in vault
- [ ] Read permissions verified for agent user
- [ ] Optional: `TRIAGE_AUTO_CLASSIFY` configured (true/false)
- [ ] Optional: `TRIAGE_KEYWORD_BOOST` customized (comma-separated keywords)
- [ ] Optional: `TRIAGE_VIP_SENDERS` configured (comma-separated sender names)
- [ ] Optional: LLM API key set if using AI classification
- [ ] All environment variables documented in `.env.example`

### File System Validation

- [ ] Vault directory structure verified:
  ```
  $VAULT_PATH/
    Needs_Action/     (read-only for triage)
    Updates/          (write summaries here)
    Logs/             (write audit logs here)
  ```
- [ ] No symlinks in Needs_Action/ (security risk)
- [ ] All files in Needs_Action/ are <100KB
- [ ] All files have `.md` extension
- [ ] File permissions allow agent read access

### Dependencies

- [ ] `vault_state_manager` skill available
- [ ] Node.js >=18 (if using JavaScript implementation)
- [ ] Optional: `p-limit` package installed (rate limiting)
- [ ] Optional: LLM SDK installed (Anthropic, OpenAI, etc.)

### Security

- [ ] API keys stored in environment variables (not hardcoded)
- [ ] Logs sanitized (no PII, full email content)
- [ ] Path validation enabled (no traversal attacks)
- [ ] File size limits enforced (prevent DoS)
- [ ] Extension whitelist enforced (.md only)

---

## Runtime Validation Checklist

### Input Validation

- [ ] File size checked before reading (<100KB)
- [ ] File extension validated (.md only)
- [ ] File path validated (inside Needs_Action/ only)
- [ ] Content encoding verified (UTF-8)
- [ ] No binary files processed

### Classification

- [ ] Rule-based classification implemented (fallback)
- [ ] LLM classification wrapped in try/catch
- [ ] Confidence thresholds applied (default 0.70)
- [ ] Low-confidence items flagged for manual review
- [ ] Category set to 'general' if classification fails

### Metadata Extraction

- [ ] Optional chaining used for all fields (`?.`)
- [ ] Default values provided for missing fields
- [ ] Timestamps parsed as UTC (not local)
- [ ] Financial amounts validated (numeric only)
- [ ] Tags extracted safely (no injection)

### Priority Scoring

- [ ] Base score initialized (default 3)
- [ ] Each factor has max boost limit
- [ ] Final score clamped to 1-10 range
- [ ] Keyword matching case-insensitive
- [ ] Deadline proximity calculated in UTC
- [ ] VIP senders checked (configurable list)
- [ ] Financial thresholds validated

### Output Generation

- [ ] Results sorted by priority descending
- [ ] Summary statistics calculated
- [ ] Category breakdown included
- [ ] Next-step recommendations provided
- [ ] Markdown table formatted correctly
- [ ] Files list included
- [ ] Timestamps in ISO 8601 format

### Error Handling

- [ ] All errors return structured objects (not thrown)
- [ ] Partial failures handled gracefully
- [ ] Skipped files logged with reason
- [ ] LLM API errors trigger fallback
- [ ] Missing metadata doesn't crash
- [ ] Duplicate items deduplicated

---

## Performance Checklist

### Efficiency

- [ ] Batch processing (all files in single pass)
- [ ] Rule-based classification tried first (fast)
- [ ] LLM calls rate-limited (max 5 concurrent)
- [ ] File reads async (non-blocking)
- [ ] Results cached (if re-running within 5 min)
- [ ] Large files rejected early (before reading)

### Scalability

- [ ] Handles 100+ files without timeout
- [ ] Memory usage <100MB for typical workload
- [ ] LLM API rate limits respected
- [ ] Parallel execution supported (read-only)
- [ ] No database dependencies

### Benchmarks

- [ ] Triage 10 files: <5 seconds (rule-based)
- [ ] Triage 10 files: <30 seconds (LLM-based)
- [ ] Triage 100 files: <60 seconds (rule-based)
- [ ] Triage 100 files: <5 minutes (LLM-based)

---

## Integration Checklist

### Vault State Manager Integration

- [ ] Uses `readVaultFile()` for file reads
- [ ] Uses `listFolderFiles()` for scanning Needs_Action/
- [ ] Respects agent permissions (read-only for Needs_Action)
- [ ] Returns relative paths (not absolute)
- [ ] Handles FileNotFoundError gracefully

### Task Lifecycle Manager Integration

- [ ] Triage metadata enriches task files
- [ ] Priority scores influence claim order
- [ ] Category affects downstream processing
- [ ] Suggested action mapped to workflow steps
- [ ] Autonomy tier determines approval requirements

### Watcher Integration

- [ ] Processes outputs from all watchers:
  - [ ] Email watcher (email-*.md files)
  - [ ] WhatsApp watcher (whatsapp-*.md files)
  - [ ] File drop watcher (file-drop-*.md files)
  - [ ] Finance watcher (finance-*.md or invoice-*.md files)
- [ ] Handles various filename formats
- [ ] Extracts watcher metadata (source_type)

### Human Dashboard Integration

- [ ] Summary written to `Updates/` folder
- [ ] Filename includes date (inbox-summary-YYYY-MM-DD.md)
- [ ] Format is human-readable markdown
- [ ] High-priority items highlighted
- [ ] Actionable recommendations included

---

## Security Checklist

### Path Validation

- [ ] All paths validated against VAULT_PATH
- [ ] No `..` traversal allowed
- [ ] No absolute paths accepted
- [ ] Symlinks rejected
- [ ] Only files in Needs_Action/ processed

### PII Protection

- [ ] Never log full email content
- [ ] Sender emails sanitized in logs
- [ ] Subject lines redacted if sensitive
- [ ] Financial amounts redacted in public logs
- [ ] Logs whitelisted fields only

### API Security

- [ ] API keys stored in environment variables
- [ ] Never logged or printed
- [ ] HTTPS enforced for all API calls
- [ ] Rate limits respected
- [ ] Retry logic includes exponential backoff

### Audit Trail

- [ ] All triage runs logged to Logs/
- [ ] Timestamp, agent, file count recorded
- [ ] Skipped files logged with reason
- [ ] Errors logged with context
- [ ] No sensitive data in audit logs

---

## Testing Checklist

### Unit Tests

- [ ] `classifyWithRules()` tested with sample files
- [ ] `extractMetadata()` handles missing fields
- [ ] `calculatePriorityScore()` clamps to 1-10
- [ ] `deduplicateTriageResults()` detects duplicates
- [ ] `parseDeadlineUTC()` handles various formats
- [ ] `validateFileType()` rejects non-markdown

### Integration Tests

- [ ] End-to-end triage on test vault
- [ ] LLM fallback tested (simulate API failure)
- [ ] Rate limiting tested (100+ files)
- [ ] Large file rejection tested (>100KB)
- [ ] Duplicate detection tested
- [ ] Priority sorting verified

### Edge Cases

- [ ] Empty Needs_Action/ folder
- [ ] Single file in Needs_Action/
- [ ] All files same priority
- [ ] Missing metadata fields
- [ ] Corrupted markdown files
- [ ] Binary files mistakenly included
- [ ] Very long subject lines (>200 chars)
- [ ] Emoji in subject/sender
- [ ] Multiple deadlines in content
- [ ] Negative financial amounts

### Error Scenarios

- [ ] VAULT_PATH not set
- [ ] Needs_Action/ folder missing
- [ ] LLM API down
- [ ] LLM API rate limited (429)
- [ ] Invalid JSON in metadata
- [ ] File read permission denied
- [ ] Disk full (cannot write summary)

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
2. [ ] Deploy skill files to `.claude/skills/vault/needs_action_triage/`
3. [ ] Verify skill loaded (check agent logs)
4. [ ] Run smoke test (triage single file)
5. [ ] Run full test (triage all files)
6. [ ] Review generated summary in Updates/
7. [ ] Check audit logs in Logs/

### Post-Deployment

- [ ] Monitor agent logs for errors
- [ ] Check triage performance (time to complete)
- [ ] Verify priority scores make sense
- [ ] Confirm categories accurate
- [ ] Validate summary format
- [ ] Test human dashboard integration
- [ ] Review audit trail

### Rollback Plan

- [ ] Backup of previous skill version available
- [ ] Rollback procedure documented
- [ ] Vault backup preserved (pre-deployment)
- [ ] Environment variables reverted if needed

---

## Monitoring Checklist

### Metrics to Track

- [ ] Triage runs per day
- [ ] Average items per triage
- [ ] Average priority score
- [ ] Category distribution
- [ ] LLM classification usage
- [ ] Rule-based fallback rate
- [ ] Skipped files count
- [ ] Error rate
- [ ] LLM API costs

### Alerts

- [ ] Alert if triage fails >3 times in 1 hour
- [ ] Alert if >10% files skipped
- [ ] Alert if LLM API errors >50%
- [ ] Alert if triage takes >5 minutes
- [ ] Alert if priority scores all 10 (misconfiguration)

### Dashboard

- [ ] Daily summary sent to human
- [ ] High-priority items highlighted
- [ ] Error log summary included
- [ ] Category trends visualized
- [ ] Priority distribution chart

---

## Maintenance Checklist

### Weekly

- [ ] Review audit logs for anomalies
- [ ] Check for duplicate items
- [ ] Verify priority scores make sense
- [ ] Review skipped files
- [ ] Update VIP senders list if needed

### Monthly

- [ ] Review LLM classification accuracy
- [ ] Tune priority scoring weights
- [ ] Update keyword boost list
- [ ] Archive old triage summaries
- [ ] Review error patterns

### Quarterly

- [ ] Re-validate category rules
- [ ] Update documentation
- [ ] Review performance benchmarks
- [ ] Audit security (PII protection)
- [ ] Update dependencies

---

## Troubleshooting Checklist

### Issue: Triage takes too long

- [ ] Check file sizes (any >100KB?)
- [ ] Check LLM API response time
- [ ] Verify concurrent request limit (5 max)
- [ ] Review number of files in Needs_Action/

### Issue: All items same priority

- [ ] Review priority scoring logic
- [ ] Check keyword matching (too broad?)
- [ ] Verify deadline parsing
- [ ] Check financial threshold
- [ ] Test with diverse inputs

### Issue: Wrong categories

- [ ] Review rule-based classification logic
- [ ] Check LLM classification confidence
- [ ] Verify file name prefixes (email-, whatsapp-, etc.)
- [ ] Test with sample files

### Issue: Missing metadata

- [ ] Check extraction regex patterns
- [ ] Verify optional chaining used
- [ ] Review default values
- [ ] Test with various markdown formats

### Issue: PII leaked in logs

- [ ] Review all console.log statements
- [ ] Verify sanitization function used
- [ ] Check audit log format
- [ ] Grep logs for sensitive patterns

---

## Sign-Off Checklist

Before marking deployment complete:

- [ ] All pre-deployment checks passed
- [ ] All runtime validations working
- [ ] Security checklist completed
- [ ] Integration tests passed
- [ ] Documentation updated
- [ ] Monitoring configured
- [ ] Human dashboard operational
- [ ] Rollback plan documented
- [ ] Team trained on new skill
- [ ] Deployment log entry created

---

**Deployment Date:** ___________
**Deployed By:** ___________
**Version:** ___________
**Sign-Off:** ___________
