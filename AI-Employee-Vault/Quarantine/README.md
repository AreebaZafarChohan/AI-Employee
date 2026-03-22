# Quarantine

This folder contains failed items that require human review.

## Folder Structure

```
Quarantine/
├── network_errors/        # Network-related failures
├── auth_errors/           # Authentication failures
└── validation_errors/     # Validation failures
```

## Quarantine Triggers

Items are moved to Quarantine when:

1. **Max Retries Exceeded** - Operation failed after 3+ retry attempts
2. **Authentication Error** - API credentials invalid or expired
3. **Validation Error** - Data validation failed
4. **Unknown Error** - Unrecoverable error occurred

## File Metadata

Each quarantined file contains metadata:

```markdown
---
original_file: example.md
failure_reason: Max retries exceeded
error_type: NetworkTimeout
retry_attempts: 3
last_error: Connection timeout after 30s
quarantined_at: 2026-03-06T10:30:00Z
requires_human_review: true
---
```

## Human Review Workflow

1. **Review** - Check the failure reason and error details
2. **Decide** - Choose an action:
   - Retry manually
   - Fix data and resubmit
   - Skip and archive
3. **Action** - Move to appropriate folder:
   - `Needs_Action/` - For retry
   - `Done/` - If resolved
   - `Rejected/` - If skipping

## Recovery Commands

```bash
# Retry quarantined item
python src/cli/quarantine_retry.py --file Quarantine/network_errors/example.md

# Move to Done (if resolved)
python src/cli/quarantine_resolve.py --file Quarantine/network_errors/example.md --action done

# Reject (skip permanently)
python src/cli/quarantine_resolve.py --file Quarantine/network_errors/example.md --action reject
```

## Related Files

- `src/core/error_handler.py` - Error handling logic
- `src/core/dead_letter_handler.py` - Dead letter queue management
- `.claude/skills/gold/error_handling_retry/dead_letter_handler.py` - Skill
