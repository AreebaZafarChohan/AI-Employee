# Transaction Classifier - Quick Start Guide

Get up and running with the transaction classifier skill in 5 minutes.

## Step 1: Configure Environment (1 minute)

Create `.env` file in your project root:

```bash
# Copy example file
cp .claude/skills/finance/transaction_classifier/assets/.env.example .env

# Edit .env with your settings
VAULT_PATH="/path/to/your/vault"
TRANSACTION_CONFIDENCE_THRESHOLD="0.70"
```

**Minimal config (just this!):**
```bash
VAULT_PATH="/path/to/vault"
```

## Step 2: Prepare Your Data (2 minutes)

### Option A: Use Sample Data (fastest)
```bash
cp .claude/skills/finance/transaction_classifier/assets/sample-transactions.csv ./my-transactions.csv
```

### Option B: Export from Your Bank
Export transactions as CSV with these columns:
- `date` (YYYY-MM-DD format)
- `amount` (negative for expenses, positive for income)
- `description` (merchant/transaction description)

Example:
```csv
date,amount,description
2025-02-04,-49.99,NETFLIX.COM
2025-02-05,2500.00,PAYROLL DEPOSIT
```

## Step 3: Run Classification (2 minutes)

### Single Transaction
```javascript
const { classifyTransaction } = require('./transaction_classifier');

const result = await classifyTransaction({
  transaction: {
    date: "2025-02-04",
    amount: -49.99,
    description: "NETFLIX.COM - Subscription"
  }
});

console.log(result.category);  // "subscription"
console.log(result.confidence); // 0.92
```

### Batch Classification (CSV file)
```javascript
const { classifyTransactionBatch } = require('./transaction_classifier');

const result = await classifyTransactionBatch({
  csv_path: "my-transactions.csv"
});

console.log(`Processed: ${result.total_transactions}`);
console.log(`Summary: ${result.summary_path}`);
```

## Step 4: Review Results

Classifications saved to: `$VAULT_PATH/Transaction_Analysis/`

Each transaction gets a markdown file with:
- ✅ Category and confidence score
- 💡 Suggested actions
- 📊 Statistical analysis
- ⚠️ Anomaly flags (if any)

**Summary file** includes:
- Category breakdown
- Total amounts by category
- Anomaly alerts
- Optimization suggestions

## Common Use Cases

### Personal Finance Tracking
```bash
# Monthly budget analysis
node -e "
const {classifyTransactionBatch} = require('./transaction_classifier');
classifyTransactionBatch({csv_path: 'bank_export.csv'}).then(r =>
  console.log('Monthly Expenses:', r.expense_total)
);
"
```

### Find All Subscriptions
```bash
# Identify recurring charges
node -e "
const {classifyTransactionBatch} = require('./transaction_classifier');
classifyTransactionBatch({csv_path: 'transactions.csv'}).then(r => {
  const subs = r.transactions.filter(t => t.category === 'Subscription');
  console.log('Monthly Subscriptions:', subs.length);
  console.log('Total Cost:', subs.reduce((sum,t) => sum + Math.abs(t.amount), 0));
});
"
```

### Detect Anomalies
```bash
# Find suspicious transactions
node -e "
const {detectAnomalies} = require('./transaction_classifier');
detectAnomalies({csv_path: 'transactions.csv'}).then(r =>
  console.log('Anomalies:', r.anomaly_count, 'High Risk:', r.high_risk_count)
);
"
```

## Next Steps

### Improve Accuracy
1. **Add merchant aliases** (in `.env`):
   ```bash
   TRANSACTION_MERCHANT_ALIASES='{"AMZN MKTP US":"Amazon"}'
   ```

2. **Build historical data**:
   - Process 90+ days of transactions for better baseline
   - More history = better anomaly detection

3. **Review low-confidence classifications**:
   - Check files with `requires_review: true`
   - Correct categories to train the system

### Integration Examples

**With Email Alerts:**
```javascript
const classification = await classifyTransaction(transaction);
if (classification.anomaly_score > 0.8) {
  await sendEmailAlert(classification);
}
```

**With Accounting Software:**
```javascript
const result = await classifyTransactionBatch({csv_path: 'transactions.csv'});
await exportToQuickBooks(result.transactions);
```

**With Dashboard:**
```javascript
const summary = await classifyTransactionBatch({csv_path: 'today.csv'});
await updateDashboard({
  revenue: summary.revenue_total,
  expenses: summary.expense_total,
  anomalies: summary.anomalies_count
});
```

## Troubleshooting

### "CSV missing required column"
**Fix:** Ensure CSV has `date`, `amount`, `description` columns

### "Invalid date format"
**Fix:** Use YYYY-MM-DD format or configure:
```bash
TRANSACTION_DATE_FORMAT="MM/DD/YYYY"
```

### Low confidence scores
**Fix:**
- Add more historical data (30-90 days minimum)
- Configure merchant aliases for name variations
- Lower threshold temporarily: `TRANSACTION_CONFIDENCE_THRESHOLD="0.65"`

### Too many false positive anomalies
**Fix:**
- Increase threshold: `TRANSACTION_ANOMALY_THRESHOLD="4.0"`
- Lower sensitivity: `TRANSACTION_ANOMALY_SENSITIVITY="low"`

## Resources

- **Full Documentation:** See [SKILL.md](./SKILL.md)
- **Code Examples:** See [EXAMPLES.md](./EXAMPLES.md)
- **Troubleshooting:** See [references/gotchas.md](./references/gotchas.md)
- **Configuration:** See [assets/.env.example](./assets/.env.example)

## Support

Questions? Check these files:
1. [references/gotchas.md](./references/gotchas.md) - Common issues and solutions
2. [references/patterns.md](./references/patterns.md) - Classification logic explained
3. [EXAMPLES.md](./EXAMPLES.md) - Real-world usage examples

---

**That's it!** You're ready to classify transactions. Start with the sample data, then move to your own bank exports.
