# Transaction Classifier Skill

Automatically classify bank transactions into categories (revenue, expense, subscription, anomaly) with confidence scoring, reasoning, and actionable suggestions.

## Quick Start

### 1. Configuration

Copy the example environment file:
```bash
cp .claude/skills/finance/transaction_classifier/assets/.env.example .env
```

Configure required variables:
```bash
# Required
VAULT_PATH="/path/to/vault"
TRANSACTION_ANALYSIS_PATH="$VAULT_PATH/Transaction_Analysis"

# Optional - tune for your needs
TRANSACTION_CONFIDENCE_THRESHOLD="0.70"
TRANSACTION_ANOMALY_THRESHOLD="3.0"
```

### 2. Prepare Transaction Data

Ensure your CSV has these columns (names can vary):
- `date` (YYYY-MM-DD format recommended)
- `amount` (numeric, positive for income, negative for expenses)
- `description` (merchant/transaction description)

Optional columns:
- `merchant` (merchant name)
- `account_id` (account identifier)
- `transaction_id` (unique transaction ID)

### 3. Run Classification

#### Single Transaction
```javascript
const { classifyTransaction } = require('./transaction_classifier');

const result = await classifyTransaction({
  transaction: {
    date: "2025-02-04",
    amount: -49.99,
    description: "NETFLIX.COM - Subscription",
    merchant: "Netflix"
  }
});

console.log(`Category: ${result.category}`);
console.log(`Confidence: ${result.confidence * 100}%`);
console.log(`File: ${result.file_path}`);
```

#### Batch CSV Processing
```javascript
const { classifyTransactionBatch } = require('./transaction_classifier');

const result = await classifyTransactionBatch({
  csv_path: "transactions_export.csv",
  options: {
    confidence_threshold: 0.70,
    flag_anomalies: true
  }
});

console.log(`Processed: ${result.total_transactions}`);
console.log(`Anomalies: ${result.anomalies_count}`);
console.log(`Summary: ${result.summary_path}`);
```

### 4. Review Classifications

Classifications are saved to: `$VAULT_PATH/Transaction_Analysis/`

Each transaction gets a markdown file with:
- Category and subcategory
- Confidence score
- Reasoning
- Suggested actions
- Anomaly analysis
- Historical context

---

## Features

### 🎯 Accurate Categorization
- **Revenue**: Salary, freelance income, refunds, investment returns
- **Expense**: Groceries, dining, transportation, shopping, healthcare
- **Subscription**: Software, streaming, utilities, memberships
- **Anomaly**: Unusual amounts, unknown merchants, suspicious patterns

### 📊 Confidence Scoring
Every classification includes:
- Confidence percentage (0-100%)
- Factors increasing/decreasing confidence
- Recommendation for manual review if needed

### ⚠️ Anomaly Detection
Statistical analysis flags:
- Unusual large amounts (>3σ from mean)
- Unknown merchants (no transaction history)
- Unusual transaction times (late night/early morning)
- Duplicate transactions
- Overseas transactions (if account is domestic)

### 🔄 Subscription Detection
Automatically identifies recurring charges:
- Monthly subscriptions (Netflix, Spotify, GitHub)
- Annual subscriptions (software licenses)
- Utilities and memberships
- Tracks subscription metrics (duration, consistency)

### 💡 Actionable Insights
Each classification includes:
- Suggested next actions
- Tax treatment guidance
- Budget impact analysis
- Optimization tips

---

## Output Format

### Single Transaction Classification

**File:** `Transaction_Analysis/20250204-101522-netflix-subscription.md`

```yaml
---
classification_id: CLASSIFY-20250204-101522-ABC123
transaction_id: txn_abc123
date: 2025-02-04
amount: -49.99
category: subscription
subcategory: entertainment
confidence: 0.92
status: classified
requires_review: false
---
```

**Contents:**
- Classification results with reasoning
- Transaction details
- Suggested actions
- Category breakdown
- Anomaly analysis
- Historical context
- Statistical analysis
- Metadata and audit trail

### Batch Summary

**File:** `Transaction_Analysis/20250204-140000-batch-summary.md`

**Contents:**
- Total transactions processed
- Classification breakdown by category
- Anomalies detected (high-priority alerts)
- Spending analysis
- Optimization suggestions
- Links to individual classification files

---

## Configuration Options

### Confidence Thresholds

```bash
# Minimum confidence for auto-approval (default: 0.70)
TRANSACTION_CONFIDENCE_THRESHOLD="0.70"

# Auto-approve threshold (default: 0.95)
TRANSACTION_AUTO_APPROVE_THRESHOLD="0.95"
```

**Tuning Guide:**
- **High accuracy needed**: Set threshold to 0.85+
- **High volume, some errors acceptable**: Set threshold to 0.65
- **Pilot phase**: Set to 0.95 and review all classifications

### Anomaly Detection

```bash
# Standard deviations for anomaly threshold (default: 3.0)
TRANSACTION_ANOMALY_THRESHOLD="3.0"

# Anomaly sensitivity: low | medium | high (default: medium)
TRANSACTION_ANOMALY_SENSITIVITY="medium"
```

**Tuning Guide:**
- **Conservative (fewer false positives)**: Threshold 4.0, sensitivity low
- **Balanced**: Threshold 3.0, sensitivity medium (default)
- **Aggressive (catch more anomalies)**: Threshold 2.5, sensitivity high

### Merchant Aliases

Map merchant name variations:
```bash
TRANSACTION_MERCHANT_ALIASES='{"AMZN MKTP US":"Amazon","SQ *":"Square","TST*":"Toast"}'
```

Common aliases to add:
- Payment processors: `SQ *`, `PAYPAL *`, `STRIPE *`
- Amazon variations: `AMZN MKTP US`, `AMZN.COM`, `AMZN.COM/BILL`
- POS systems: `TST*`, `TOAST TAB*`

---

## Integration Examples

### With Email Drafter

Send anomaly alerts:
```javascript
const classification = await classifyTransaction(transaction);

if (classification.anomaly_score > 0.8) {
  await draftEmail({
    intent: "anomaly_alert",
    recipient: { email: "finance@company.com" },
    context: {
      transaction_id: classification.transaction_id,
      amount: classification.amount,
      merchant: classification.merchant,
      anomaly_reason: classification.anomaly_reason
    }
  });
}
```

### With Approval Request Creator

High-value transaction approval:
```javascript
const classification = await classifyTransaction(transaction);

if (Math.abs(classification.amount) > 1000 && classification.confidence < 0.80) {
  await createApprovalRequest({
    type: "transaction_classification",
    subject: `Review large transaction: ${classification.merchant}`,
    details: {
      amount: classification.amount,
      category: classification.category,
      confidence: classification.confidence
    }
  });
}
```

### With Dashboard Writer

Include in daily dashboard:
```javascript
const summary = await classifyTransactionBatch({ csv_path: "today.csv" });

await updateDashboard({
  section: "financial_summary",
  data: {
    total_transactions: summary.total_transactions,
    total_revenue: summary.revenue_total,
    total_expenses: summary.expense_total,
    anomalies: summary.anomalies_count,
    classification_accuracy: summary.avg_confidence
  }
});
```

---

## Troubleshooting

### Low Confidence Scores

**Causes:**
- Unknown merchant (no transaction history)
- Ambiguous transaction description
- Amount doesn't match historical pattern

**Solutions:**
1. Build historical data (30-90 days minimum)
2. Add merchant aliases for variations
3. Lower confidence threshold temporarily
4. Review and correct misclassifications to train system

### Missing Subscriptions

**Causes:**
- Not enough historical data (need 3+ recurring charges)
- Merchant name variations break pattern detection
- Irregular billing amounts (>5% variance)

**Solutions:**
1. Add merchant aliases to normalize names
2. Adjust subscription detection variance tolerance
3. Manually tag known subscriptions for training

### False Positive Anomalies

**Causes:**
- Legitimate large transactions flagged
- New but legitimate merchants
- Baseline period too short

**Solutions:**
1. Increase anomaly threshold (e.g., 3.5 or 4.0 σ)
2. Extend baseline period to 90+ days
3. Add exceptions for known large transaction categories

### CSV Parsing Errors

**Causes:**
- Missing required columns
- Inconsistent date formats
- Commas in description field break parsing

**Solutions:**
1. Use proper CSV parser (handles quoted fields)
2. Configure date format: `TRANSACTION_DATE_FORMAT`
3. Validate CSV structure before processing

---

## Performance Optimization

### For Large Batches (1000+ transactions)

1. **Enable parallel processing:**
```bash
TRANSACTION_ENABLE_PARALLEL="true"
TRANSACTION_MAX_WORKERS="4"
```

2. **Increase batch size:**
```bash
TRANSACTION_MAX_BATCH_SIZE="2000"
```

3. **Reduce baseline period:**
```bash
TRANSACTION_BASELINE_PERIOD_DAYS="30"  # Instead of 90
```

### Memory Usage

Estimated memory usage:
- Single transaction: ~2MB
- Batch of 100: ~50MB
- Batch of 1000: ~200MB
- Historical data (90 days, 500 transactions): ~100MB

For very large datasets:
- Process in chunks (500-1000 transactions per batch)
- Clear historical data cache between batches
- Use streaming CSV parser

---

## Security Best Practices

### Data Protection

- ✅ Store vault on encrypted filesystem
- ✅ Restrict vault directory permissions (user-only read/write)
- ✅ Enable audit logging: `TRANSACTION_AUDIT_LOG_PATH`
- ✅ Redact sensitive fields in logs: `TRANSACTION_REDACT_FIELDS`
- ✅ Use secure transfer for CSV files (encrypted channels)

### Access Control

- ✅ Limit agent write access to Transaction_Analysis/ only
- ✅ Implement approval workflow for high-value transactions
- ✅ Review classification history regularly
- ✅ Set up alerts for anomaly detections

### Compliance

- ✅ Document data retention policy
- ✅ Ensure PII handling complies with GDPR/CCPA
- ✅ Implement data deletion procedures
- ✅ Maintain audit trail for all classifications

---

## FAQ

**Q: How many historical transactions do I need?**
A: Minimum 30 days (recommended 90+ days) for accurate anomaly detection and confidence scoring.

**Q: Can I customize categories?**
A: Yes, use `TRANSACTION_CUSTOM_CATEGORIES` to add domain-specific categories.

**Q: What if a classification is wrong?**
A: Edit the frontmatter in the classification file, mark as `rejected`, and note the correct category. The system learns from corrections.

**Q: How do I handle multi-currency transactions?**
A: Enable multi-currency support with `TRANSACTION_MULTI_CURRENCY="true"` and configure currency API.

**Q: Can I export to accounting software?**
A: Yes, configure `TRANSACTION_EXPORT_FORMAT` (quickbooks, xero, csv) for automated export.

**Q: What's the accuracy rate?**
A: Typically 85-95% accuracy after training on 90+ days of data with proper merchant aliases configured.

---

## Support

- **Documentation**: See SKILL.md for detailed usage
- **Examples**: See EXAMPLES.md for code samples
- **Troubleshooting**: See references/gotchas.md
- **Patterns**: See references/patterns.md
- **Impact Checklist**: See references/impact-checklist.md

For issues or questions, check the gotchas.md file first for common problems and solutions.

---

## Version

**Current Version:** v1.0.0
**Last Updated:** 2025-02-04
**Skill Type:** Finance/Classification
**Status:** Production Ready
