# Needs Action Triage Skill

**Version:** 1.0.0
**Last Updated:** 2025-02-03

## Overview

The `needs_action_triage` skill provides intelligent classification and prioritization of incoming items in the `Needs_Action/` folder. It categorizes files by type (email, whatsapp, file_drop, finance, general), assigns priority scores (1-10), extracts metadata, and generates actionable recommendations.

## Quick Start

### Basic Usage

```javascript
const { triageNeedsAction } = require('./needs_action_triage');

// Run triage on all items
const result = await triageNeedsAction({
  minPriorityScore: 1,    // Include all items
  autoClassify: true,     // Use LLM if available
  extractMetadata: true   // Parse structured fields
});

// Display results
console.log(`Total items: ${result.summary.total}`);
console.log(`High priority: ${result.summary.high_priority}`);

// Process top priority item
const topItem = result.items[0];
console.log(`Next task: ${topItem.metadata.subject}`);
console.log(`Action: ${topItem.suggested_action}`);
```

### Configuration

Add to `.env`:

```bash
# Required
VAULT_PATH="/absolute/path/to/vault"

# Optional
TRIAGE_AUTO_CLASSIFY="true"                 # Enable LLM classification
TRIAGE_KEYWORD_BOOST="urgent,asap,critical" # Priority keywords
TRIAGE_VIP_SENDERS="ceo,manager,client"     # VIP sender names
TRIAGE_MIN_PRIORITY_SCORE="1"               # Filter threshold
```

## Key Features

- **Multi-Category Classification**: Email, WhatsApp, file drop, finance, general
- **Priority Scoring**: 1-10 scale based on keywords, deadlines, sender, amount
- **Metadata Extraction**: Sender, subject, deadline, financial amounts, tags
- **Rule-Based Fallback**: Works without LLM (offline mode)
- **Duplicate Detection**: Fingerprint-based deduplication
- **PII Protection**: Sanitized logging, no sensitive data exposure
- **Graceful Degradation**: Handles missing metadata, API failures

## Output Format

```json
{
  "success": true,
  "items": [
    {
      "file_name": "email-20250203-invoice.md",
      "file_path": "Needs_Action/email-20250203-invoice.md",
      "category": "finance",
      "subcategory": "invoice",
      "confidence": 0.95,
      "priority_score": 9,
      "metadata": {
        "source_type": "email",
        "sender": "Acme Corp <billing@acme.com>",
        "subject": "Invoice #1234 overdue",
        "received_at": "2025-01-15T10:00:00Z",
        "deadline": "2025-01-31T23:59:59Z",
        "financial_amount": 5432.00,
        "tags": ["urgent", "payment", "overdue"]
      },
      "suggested_action": "approve",
      "estimated_effort": "low",
      "requires_human_approval": true,
      "autonomy_tier": "silver",
      "summary": "Overdue payment of $5,432.00 from Acme Corp, requires immediate approval",
      "key_entities": ["Acme Corp", "Invoice #1234"],
      "sentiment": "urgent"
    }
  ],
  "summary": {
    "total": 8,
    "high_priority": 2,
    "medium_priority": 4,
    "low_priority": 2,
    "by_category": {
      "email": 4,
      "whatsapp": 2,
      "finance": 1,
      "file_drop": 1
    }
  },
  "errors": []
}
```

## Categories

| Category | Indicators | Examples |
|----------|-----------|----------|
| **email** | `From:`, `Subject:`, filename prefix `email-` | Gmail messages, Outlook emails |
| **whatsapp** | Timestamp format `MM/DD/YY, HH:MM AM`, `WhatsApp Chat` | Chat exports, message threads |
| **finance** | `$` amounts, `invoice`, `receipt`, `payment` | Invoices, receipts, statements |
| **file_drop** | `Attached:`, `File:`, filename prefix `file-drop-` | PDFs, documents, contracts |
| **general** | Fallback category for uncategorized items | Manual notes, misc tasks |

## Priority Scoring

**Base Score:** 3 (medium priority)

**Boosts:**
- **Keywords** (+2): "urgent", "asap", "critical", "immediate"
- **Deadline** (+0 to +3):
  - Overdue: +3
  - Due today (<24h): +3
  - Due this week (<72h): +2
  - Due next week (<168h): +1
- **VIP Sender** (+2): Configurable list of important senders
- **Financial Threshold** (+0 to +3):
  - >$10,000: +3
  - >$1,000: +2
  - >$100: +1
- **Category Boost** (+1): Finance items auto-elevated

**Final Score:** Clamped to 1-10 range

## Integration

### With Task Lifecycle Manager

```javascript
// Triage inbox
const triage = await triageNeedsAction({ minPriorityScore: 5 });

// Claim highest-priority task
const topItem = triage.items[0];
const claim = await taskLifecycle.claimTask(topItem.file_name, 'lex');

if (claim.success) {
  console.log(`Claimed: ${topItem.metadata.subject}`);
  console.log(`Priority: ${topItem.priority_score}`);
  console.log(`Action: ${topItem.suggested_action}`);
}
```

### Generate Dashboard Summary

```javascript
// Run triage
const triage = await triageNeedsAction({ autoClassify: true });

// Generate summary
const summary = await generateDashboardSummary(triage);

// Write to Updates/ folder
await fs.writeFile(
  `${VAULT_PATH}/Updates/inbox-summary-${today}.md`,
  summary
);
```

## Error Handling

All functions return structured results:

```typescript
interface TriageResult {
  success: boolean;
  items: TriageItem[];
  summary: {
    total: number;
    high_priority: number;
    medium_priority: number;
    low_priority: number;
    by_category: Record<string, number>;
  };
  errors?: string[];  // Files that failed to process
}
```

**Common Errors:**
- `FILE_TOO_LARGE`: File >100KB (skipped)
- `INVALID_FILE_TYPE`: Non-markdown file (rejected)
- `LOW_CONFIDENCE`: Classification confidence <0.70 (fallback to 'general')
- `LLM_API_ERROR`: LLM unavailable (fallback to rule-based)

## Performance

**Benchmarks:**
- 10 files (rule-based): <5 seconds
- 10 files (LLM-based): <30 seconds
- 100 files (rule-based): <60 seconds
- 100 files (LLM-based): <5 minutes

**Optimization:**
- Batch processing (single pass)
- Rule-based first (fast fallback)
- Rate-limited LLM calls (max 5 concurrent)
- File size checks (reject >100KB early)

## Security

**PII Protection:**
- Never logs full email content
- Sanitizes sender/subject in logs
- Redacts financial amounts in public logs

**Path Validation:**
- All paths validated against VAULT_PATH
- No `..` traversal allowed
- Symlinks rejected

**API Security:**
- API keys in environment variables only
- HTTPS enforced for all API calls
- Rate limits respected

## Documentation

- **SKILL.md**: Complete skill specification
- **patterns.md**: Code examples and usage patterns
- **gotchas.md**: Common issues and edge cases
- **impact-checklist.md**: Deployment and validation checklist
- **EXAMPLES.md**: End-to-end workflow examples

## Support

For issues or questions:
1. Check `gotchas.md` for known issues
2. Review `patterns.md` for examples
3. Consult `impact-checklist.md` for troubleshooting
4. Contact: Digital FTE team

## License

Part of the Digital FTE Agent System.
