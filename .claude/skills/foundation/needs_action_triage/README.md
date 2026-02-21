# Needs Action Triage Skill

**Domain:** `foundation`
**Version:** 1.0.0
**Status:** Production Ready

## Quick Start

This skill provides intelligent classification, prioritization, and routing of action items with automatic duplicate detection and dependency analysis.

### Prerequisites

```bash
# Set required environment variables
export TRIAGE_RULES_PATH="./config/triage-rules.json"
export TRIAGE_STORAGE_PATH="./triage"
export TRIAGE_AUDIT_LOG="./logs/triage-audit.log"

# Set scoring thresholds
export TRIAGE_CRITICAL_THRESHOLD="90"
export TRIAGE_HIGH_THRESHOLD="70"
export TRIAGE_MEDIUM_THRESHOLD="40"
```

### Basic Usage

**Python:**
```python
from triage_engine import TriageEngine, TriageItem
from datetime import datetime

# Initialize
engine = TriageEngine()

# Create item
item = TriageItem(
    item_id="ITEM-001",
    title="Production database crash - URGENT",
    description="Main DB crashed, all users affected",
    source="github",
    created_at=datetime.utcnow().isoformat()
)

# Triage
triaged = engine.triage_item(item)

print(f"Category: {triaged.category}")
print(f"Priority: {triaged.priority}")
print(f"Score: {triaged.score}")
print(f"Owner: {triaged.owner}")
```

## Documentation Structure

- **[SKILL.md](./SKILL.md)** - Complete specification (1,200+ lines)
- **[docs/patterns.md](./docs/patterns.md)** - 7 triage strategies
- **[docs/impact-checklist.md](./docs/impact-checklist.md)** - 100+ assessment items
- **[docs/gotchas.md](./docs/gotchas.md)** - 15+ troubleshooting scenarios

## Asset Templates

- `assets/triage-rules.json` - Classification rules configuration
- `assets/triage_engine.py` - Python triage engine
- `assets/batch-triage.sh` - Batch processing script

## Key Features

✅ **Intelligent Classification**
- Multi-factor category detection
- Urgency and impact analysis
- Context-aware scoring
- ML-ready architecture

✅ **Duplicate Detection**
- Fingerprint-based matching
- Similarity scoring
- Configurable thresholds
- Near-duplicate detection

✅ **Smart Routing**
- Load-balanced assignment
- SLA-based deadlines
- Automatic escalation
- Team capacity awareness

✅ **Audit Trail**
- Complete decision logging
- Reasoning capture
- Compliance-ready
- Feedback integration

## Classification Categories

- `security` - Security vulnerabilities (Critical priority, 4h SLA)
- `bug_critical` - Production outages (Critical priority, 2h SLA)
- `bug_major` - Significant bugs (High priority, 24h SLA)
- `feature_request` - New features (Medium priority, 7d SLA)
- `question` - Support questions (Low priority, 48h SLA)

## Priority Levels

- **Critical** (≥90): Security, outages, data loss
- **High** (70-89): Major bugs, urgent requests
- **Medium** (40-69): Regular bugs, features
- **Low** (<40): Minor issues, questions

## Anti-Patterns to Avoid

❌ Ignoring urgency signals in critical items
❌ Poor duplicate detection (exact match only)
❌ Static rules without feedback loop
❌ No audit trail
❌ Ignoring task dependencies

See [SKILL.md](./SKILL.md#anti-patterns) for detailed examples.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Low accuracy | Update keyword lists, tune thresholds |
| False positive duplicates | Lower similarity threshold |
| Routing errors | Verify team mappings |
| SLA breaches | Check escalation triggers |

See [gotchas.md](./docs/gotchas.md) for comprehensive troubleshooting.

## Integration Patterns

### Pattern 1: GitHub Issues
```python
@app.route('/webhook/github', methods=['POST'])
def github_webhook():
    event = request.json
    if event['action'] == 'opened':
        item = TriageItem(
            item_id=event['issue']['number'],
            title=event['issue']['title'],
            description=event['issue']['body'],
            source='github',
            created_at=event['issue']['created_at']
        )
        triaged = engine.triage_item(item)
        # Assign labels based on triage
        add_github_labels(item.item_id, triaged.priority, triaged.category)
```

### Pattern 2: Email Inbox
```python
for email in get_unread_emails():
    item = TriageItem(
        item_id=email.message_id,
        title=email.subject,
        description=email.body,
        source='email',
        created_at=email.received_at
    )
    triaged = engine.triage_item(item)
    if triaged.priority == 'critical':
        notify_oncall(triaged)
```

## Architecture

```
needs_action_triage/
├── SKILL.md                    # Main specification
├── README.md                   # This file
├── assets/                     # Reusable templates
│   ├── triage-rules.json      # Classification rules
│   ├── triage_engine.py       # Python engine
│   └── batch-triage.sh        # Batch processor
└── docs/                       # Supporting documentation
    ├── patterns.md             # Triage strategies
    ├── impact-checklist.md     # System assessment
    └── gotchas.md              # Troubleshooting guide
```

## Best Practices

1. **Tune Thresholds** - Adjust based on your workload
2. **Update Rules** - Review keywords monthly
3. **Monitor Accuracy** - Track classification metrics
4. **Collect Feedback** - Implement feedback loop
5. **Test Edge Cases** - Validate with real examples
6. **Balance Load** - Distribute work evenly
7. **Audit Everything** - Log all decisions
8. **Escalate Proactively** - Don't wait for SLA breach

## Requirements

- **Python 3.7+**
- **jq** (for bash scripts)
- **Storage** for items and audit logs
- **Optional:** ML libraries for enhanced classification

## Performance

- Classification: <1s per item
- Batch processing: 100+ items/min
- Duplicate detection: O(1) with indexing
- Scalable to 10,000+ items

## Support

For issues or questions:
1. Check [gotchas.md](./docs/gotchas.md) for known problems
2. Review [patterns.md](./docs/patterns.md) for usage examples
3. Complete [impact-checklist.md](./docs/impact-checklist.md)
4. Consult [SKILL.md](./SKILL.md) for complete reference

---

**Maintained by:** Foundation Team
**Last Updated:** 2026-02-06
**License:** Internal Use Only
