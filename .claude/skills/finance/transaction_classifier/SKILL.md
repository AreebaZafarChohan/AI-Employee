---
name: transaction_classifier
description: Classify bank transactions into categories (revenue, expense, subscription, anomaly) with reasoning and actionable suggestions.
---

# Transaction Classifier

## Purpose

This skill analyzes bank transactions and automatically classifies them into predefined categories. It processes CSV or structured transaction data and provides detailed categorization with reasoning, confidence scores, and actionable suggestions for each transaction. The skill is designed to help with financial analysis, anomaly detection, and automated bookkeeping workflows.

## When to Use This Skill

Use `transaction_classifier` when:

- **Financial reconciliation**: Automatically categorizing bank transactions for accounting
- **Expense tracking**: Identifying and classifying business expenses
- **Revenue analysis**: Detecting and categorizing income sources
- **Subscription monitoring**: Identifying recurring subscription charges
- **Anomaly detection**: Flagging unusual or suspicious transactions
- **Budget analysis**: Understanding spending patterns across categories
- **Tax preparation**: Categorizing transactions for tax reporting
- **Cash flow management**: Analyzing inflows and outflows by category

Do NOT use this skill when:

- **Real-time fraud detection**: Critical security scenarios requiring immediate human oversight
- **Large batch processing**: Transactions exceeding 10,000 records (use specialized batch tools)
- **Complex multi-currency reconciliation**: Requires specialized forex handling
- **Legal investigations**: Forensic analysis requiring legal compliance and chain of custody
- **Credit card disputes**: Transaction classification for chargebacks requires human judgment

## Impact Analysis Workflow

### 1. Environment Variable Strategy

**Build-Time vs Runtime Variables:**

This skill operates at runtime only. No build-time variables required.

**Runtime variables:**
```bash
# Required
VAULT_PATH="/absolute/path/to/vault"
TRANSACTION_ANALYSIS_PATH="$VAULT_PATH/Transaction_Analysis"  # Auto-created if missing

# Optional: Classification configuration
TRANSACTION_CONFIDENCE_THRESHOLD="0.70"        # 0.0-1.0, default 0.70
TRANSACTION_ANOMALY_THRESHOLD="3.0"           # Standard deviations, default 3.0
TRANSACTION_AUTO_APPROVE_THRESHOLD="0.95"     # Auto-approve confidence, default 0.95

# Optional: Category definitions
TRANSACTION_CUSTOM_CATEGORIES=""              # Comma-separated custom categories
TRANSACTION_SUBSCRIPTION_PATTERNS=""          # Regex patterns for subscription detection
TRANSACTION_MERCHANT_ALIASES=""               # Custom merchant name mappings

# Optional: Output preferences
TRANSACTION_OUTPUT_FORMAT="markdown"          # markdown | json | csv
TRANSACTION_INCLUDE_SUGGESTIONS="true"        # Include actionable suggestions
TRANSACTION_INCLUDE_CONFIDENCE="true"         # Show confidence scores

# Optional: Compliance and audit
TRANSACTION_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
TRANSACTION_REQUIRE_REVIEW="false"            # Flag all classifications for review
TRANSACTION_SESSION_ID=""                     # Current agent session ID
TRANSACTION_RETAIN_RAW_DATA="true"           # Keep original CSV for audit trail
```

**Secrets Management:**

- This skill does NOT connect to bank APIs (local file processing only)
- No banking credentials required
- May process sensitive financial data (amounts, merchant names)
- Never log transaction amounts or merchant details to system logs
- Use encrypted vault storage for sensitive transaction data

**Variable Discovery Process:**
```bash
# Check transaction configuration
cat .env | grep TRANSACTION_

# Verify Transaction_Analysis folder exists
test -d "$VAULT_PATH/Transaction_Analysis" && echo "OK" || mkdir -p "$VAULT_PATH/Transaction_Analysis"

# Count classified transactions
find "$VAULT_PATH/Transaction_Analysis" -name '*.md' | wc -l
```

### 2. Network & Topology Implications

**Port Discovery:**

No network ports required. This skill operates on local filesystem only.

**Dependency Topology:**

```
Transaction Classifier
  ├── Vault State Manager (file writes to Transaction_Analysis/)
  │   └── Filesystem (Transaction_Analysis/ folder)
  └── Optional: CSV Parser
      └── Filesystem (input CSV files)
```

**Topology Notes:**
- Primary operation: local file reads and writes (no external dependencies)
- No bank API integration (processes local files only)
- No database dependencies
- Stateless operation (each classification is independent)

**Docker/K8s Implications:**

When containerizing agents that use this skill:
- Mount vault as read-write volume: `-v /host/vault:/vault:rw`
- Ensure `Transaction_Analysis/` folder is writable
- No network access required
- No persistent storage needed beyond vault mount

### 3. Auth / CORS / Security Impact

**Authentication Pattern Analysis:**

- No authentication for filesystem access (local only)
- Agent authorization: all agents have write access to Transaction_Analysis/ (per AGENTS.md §4)

**Security Considerations:**

| Risk | Mitigation |
|------|-----------|
| **Sensitive financial data exposure** | Never log transaction amounts or account numbers |
| **PII leakage** | Sanitize merchant names and descriptions before logging |
| **Path traversal** | Validate all paths via vault_state_manager |
| **Data injection** | Sanitize CSV input to prevent code injection |
| **Unauthorized access** | Restrict filesystem permissions to vault directory only |

**Validation Rules:**

Before processing any transaction:
```javascript
function validateTransaction(transaction) {
  // Required fields check
  if (!transaction.date || !transaction.amount || !transaction.description) {
    throw new Error("Transaction missing required fields: date, amount, description");
  }

  // Date format validation
  const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
  if (!dateRegex.test(transaction.date)) {
    throw new Error("Invalid date format. Expected YYYY-MM-DD");
  }

  // Amount validation
  if (isNaN(parseFloat(transaction.amount))) {
    throw new Error("Invalid amount format. Must be numeric");
  }

  // Description check
  if (!transaction.description || transaction.description.length < 3) {
    throw new Error("Description must be at least 3 characters");
  }

  return true;
}
```

---

## Usage Patterns

### Pattern 1: Single Transaction Classification

**Use Case:** Classifying a single transaction

**Input:**
```javascript
const { classifyTransaction } = require('./transaction_classifier');

const classification = await classifyTransaction({
  transaction: {
    date: "2025-02-04",
    amount: -49.99,
    description: "NETFLIX.COM - Subscription",
    merchant: "Netflix",
    account_id: "acct_12345",
    transaction_id: "txn_abc123"
  },
  options: {
    include_suggestions: true,
    confidence_threshold: 0.70
  },
  metadata: {
    agent: "lex",
    session_id: "session_xyz789",
    timestamp: "2025-02-04T10:15:22Z"
  }
});

console.log(`Classification: ${classification.category}`);
console.log(`Confidence: ${classification.confidence}`);
console.log(`File path: ${classification.file_path}`);
```

**Output File:** `Transaction_Analysis/20250204-101522-netflix-subscription.md`

**File Content:**
```markdown
---
classification_id: CLASSIFY-20250204-101522-ABC123
transaction_id: txn_abc123
date: 2025-02-04
amount: -49.99
currency: USD
category: subscription
subcategory: entertainment
confidence: 0.92
status: classified
requires_review: false
created_at: 2025-02-04T10:15:22Z
---

# Transaction Classification

**Classification ID:** CLASSIFY-20250204-101522-ABC123
**Date:** 2025-02-04
**Amount:** -$49.99 USD
**Merchant:** Netflix
**Status:** ✅ Classified

---

## Classification Results

**Primary Category:** Subscription
**Subcategory:** Entertainment
**Confidence Score:** 92%

**Reasoning:**
- Merchant "NETFLIX.COM" matches known subscription service pattern
- Regular monthly charge amount ($49.99) consistent with subscription
- Negative amount indicates expense/outflow
- Merchant category: streaming media services
- Historical pattern: recurring monthly charge detected

---

## Transaction Details

**Transaction ID:** txn_abc123
**Account ID:** acct_12345
**Date:** 2025-02-04
**Amount:** -$49.99 USD
**Merchant:** Netflix
**Description:** NETFLIX.COM - Subscription
**Transaction Type:** Debit (expense)

---

## Suggested Actions

- [ ] Verify subscription is still active and needed
- [ ] Check if current plan matches usage (streaming hours, users)
- [ ] Review subscription tier for cost optimization opportunities
- [ ] Update subscription tracker spreadsheet
- [ ] Consider annual plan if available for cost savings

---

## Category Breakdown

**Main Category:** Subscription
- **Definition:** Recurring charges for ongoing services or memberships
- **Tax Treatment:** Generally not deductible for personal use
- **Budget Impact:** Fixed recurring expense

**Subcategory:** Entertainment
- **Typical Merchants:** Netflix, Spotify, Disney+, HBO, Gaming services
- **Spending Trends:** Review monthly entertainment budget allocation
- **Optimization Tips:** Bundle services, use family plans, rotate subscriptions

---

## Anomaly Analysis

**Anomaly Score:** 0.05 (Low)
**Risk Level:** Normal
**Flags:** None

**Analysis:**
- Amount matches historical pattern (previous charges: $49.99)
- Timing consistent with monthly billing cycle (charged on 4th of each month)
- No unusual merchant name variations detected
- Transaction location matches service provider location

---

## Historical Context

**Previous Transactions from this Merchant:**
- 2025-01-04: -$49.99 (Subscription - Entertainment)
- 2024-12-04: -$49.99 (Subscription - Entertainment)
- 2024-11-04: -$49.99 (Subscription - Entertainment)

**Subscription Metrics:**
- Average monthly charge: $49.99
- Subscription duration: 12+ months
- Charge consistency: 100% (no missed/failed charges)
- Price stability: No increases in past 12 months

---

## Metadata

- **Agent:** lex (Local Executive Agent)
- **Session ID:** session_xyz789
- **Classification Model:** transaction_classifier_v1.0
- **Processing Time:** 125ms
- **Manual Review Required:** No

---

## Approval Workflow

**Review Required:** No (high confidence classification)

If you need to modify this classification:
1. Edit the category/subcategory above
2. Update confidence score if needed
3. Mark status as `reviewed` in frontmatter when approved
4. Add review notes below

To reject this classification:
1. Mark status as `rejected` in frontmatter
2. Add rejection reason and correct category

---

## Classification History

- **v1.0** - 2025-02-04 10:15:22 UTC - Initial classification (auto-approved, confidence: 92%)
```

---

### Pattern 2: Batch CSV Classification

**Use Case:** Classifying multiple transactions from a CSV export

**Input CSV:** `transactions_export.csv`
```csv
date,amount,description,merchant,account_id,transaction_id
2025-02-01,-125.00,WHOLE FOODS MARKET,Whole Foods,acct_12345,txn_001
2025-02-01,2500.00,PAYROLL DEPOSIT - ACME CORP,Acme Corp,acct_12345,txn_002
2025-02-02,-19.99,GITHUB.COM - MONTHLY,GitHub,acct_12345,txn_003
2025-02-03,-8500.00,WIRE TRANSFER TO UNKNOWN,Unknown,acct_12345,txn_004
2025-02-04,-49.99,NETFLIX.COM - Subscription,Netflix,acct_12345,txn_005
```

**Input:**
```javascript
const classification = await classifyTransactionBatch({
  csv_path: "transactions_export.csv",
  options: {
    confidence_threshold: 0.70,
    anomaly_threshold: 3.0,
    auto_approve_threshold: 0.95,
    flag_anomalies: true,
    output_format: "markdown"
  },
  metadata: {
    agent: "lex",
    session_id: "session_batch_001",
    timestamp: "2025-02-04T14:00:00Z"
  }
});

console.log(`Processed ${classification.total_transactions} transactions`);
console.log(`Anomalies detected: ${classification.anomalies_count}`);
console.log(`Summary file: ${classification.summary_path}`);
```

**Output File:** `Transaction_Analysis/20250204-140000-batch-summary.md`

**File Content:**
```markdown
---
batch_id: BATCH-20250204-140000-001
processed_at: 2025-02-04T14:00:00Z
total_transactions: 5
classified_count: 5
anomalies_count: 1
high_confidence_count: 4
requires_review_count: 1
---

# Batch Transaction Classification Summary

**Batch ID:** BATCH-20250204-140000-001
**Processed:** 2025-02-04 14:00:00 UTC
**Total Transactions:** 5
**Anomalies Detected:** 1 ⚠️

---

## Classification Summary

| Category | Count | Total Amount | Avg Confidence |
|----------|-------|--------------|----------------|
| **Revenue** | 1 | +$2,500.00 | 98% |
| **Expense** | 3 | -$194.98 | 91% |
| **Subscription** | 2 | -$69.98 | 92% |
| **Anomaly** | 1 | -$8,500.00 | 65% ⚠️ |

---

## Transaction Details

### ✅ High Confidence Classifications (4)

1. **txn_002** - Revenue: Payroll Deposit
   - Amount: +$2,500.00
   - Confidence: 98%
   - Category: Revenue > Salary
   - Status: Auto-approved

2. **txn_003** - Subscription: GitHub Monthly
   - Amount: -$19.99
   - Confidence: 94%
   - Category: Subscription > Software/Tools
   - Status: Auto-approved

3. **txn_005** - Subscription: Netflix
   - Amount: -$49.99
   - Confidence: 92%
   - Category: Subscription > Entertainment
   - Status: Auto-approved

4. **txn_001** - Expense: Grocery Shopping
   - Amount: -$125.00
   - Confidence: 88%
   - Category: Expense > Groceries
   - Status: Auto-approved

### ⚠️ Anomalies Requiring Review (1)

1. **txn_004** - SUSPICIOUS: Large Wire Transfer
   - Amount: -$8,500.00
   - Confidence: 65%
   - Category: Anomaly > Unusual Large Transaction
   - **Anomaly Flags:**
     - Amount exceeds 3σ from mean (-$8,500 vs avg -$75)
     - Unknown merchant/recipient
     - Wire transfer method (higher risk)
     - No historical pattern match
   - **Status:** 🔴 REQUIRES MANUAL REVIEW
   - **Suggested Actions:**
     - Verify transaction legitimacy with account holder
     - Check for authorization records
     - Contact bank if unrecognized
     - Consider fraud investigation if unauthorized

---

## Category Distribution

**Revenue (20% of transactions)**
- Salary/Payroll: $2,500.00

**Subscriptions (40% of transactions)**
- Software/Tools: -$19.99
- Entertainment: -$49.99

**Expenses (20% of transactions)**
- Groceries: -$125.00

**Anomalies (20% of transactions)**
- Unusual Large Transaction: -$8,500.00 ⚠️

---

## Actionable Insights

### 💰 Revenue Analysis
- Single payroll deposit of $2,500.00
- Consistent with bi-weekly pay schedule
- No additional income sources detected

### 📊 Spending Breakdown
- Total expenses: -$194.98 (excluding anomaly)
- Subscription costs: -$69.98 (36% of regular expenses)
- Grocery spending: -$125.00 (64% of regular expenses)

### ⚠️ Anomaly Alerts
- **1 HIGH-PRIORITY ALERT:** Large wire transfer of $8,500.00
  - **Action Required:** Immediate verification recommended
  - **Risk Level:** Medium-High
  - **Timeline:** Review within 24 hours

### 💡 Optimization Suggestions
- Subscription audit: Review $69.98/month in recurring charges
- Consider bundling GitHub with other developer tools
- Monitor grocery spending trend (baseline established)

---

## Files Generated

Individual classification files:
- `20250204-140000-txn_001-grocery.md`
- `20250204-140000-txn_002-payroll.md`
- `20250204-140000-txn_003-github-subscription.md`
- `20250204-140000-txn_004-wire-transfer-ANOMALY.md` ⚠️
- `20250204-140000-txn_005-netflix-subscription.md`

---

## Processing Metadata

- **Agent:** lex (Local Executive Agent)
- **Session ID:** session_batch_001
- **Input File:** transactions_export.csv
- **Output Path:** Transaction_Analysis/
- **Processing Time:** 847ms
- **Errors:** 0
- **Warnings:** 1 (anomaly detected)

---

## Next Steps

- [ ] Review flagged anomaly transaction (txn_004)
- [ ] Approve or reject low-confidence classifications
- [ ] Update budget tracker with classified transactions
- [ ] Export approved classifications to accounting system
- [ ] Archive original CSV file with timestamp
```

---

### Pattern 3: Anomaly Detection Focus

**Use Case:** Scanning transactions specifically for anomalies and fraud indicators

**Input:**
```javascript
const anomalyReport = await detectAnomalies({
  transactions: [
    { date: "2025-02-01", amount: -45.00, description: "Regular gas station purchase", merchant: "Shell" },
    { date: "2025-02-02", amount: -2800.00, description: "ATM WITHDRAWAL - 3AM", merchant: "ATM" },
    { date: "2025-02-03", amount: -12.50, description: "Coffee shop", merchant: "Starbucks" },
    { date: "2025-02-04", amount: -1500.00, description: "Online purchase - Electronics", merchant: "Unknown Overseas Vendor" }
  ],
  options: {
    anomaly_sensitivity: "high",  // low | medium | high
    flag_patterns: ["unusual_time", "large_amount", "unknown_merchant", "overseas"],
    baseline_period_days: 90
  },
  metadata: {
    agent: "lex",
    session_id: "session_anomaly_check"
  }
});

console.log(`Anomalies detected: ${anomalyReport.anomaly_count}`);
console.log(`High-risk transactions: ${anomalyReport.high_risk_count}`);
```

**Output:**
```markdown
---
anomaly_report_id: ANOMALY-20250204-150000-XYZ
generated_at: 2025-02-04T15:00:00Z
total_transactions: 4
anomalies_detected: 2
high_risk_count: 2
medium_risk_count: 0
---

# Transaction Anomaly Detection Report

**Report ID:** ANOMALY-20250204-150000-XYZ
**Generated:** 2025-02-04 15:00:00 UTC
**Risk Level:** 🔴 HIGH - Multiple anomalies detected

---

## Executive Summary

**Anomalies Detected:** 2 out of 4 transactions (50%)
**Risk Assessment:** HIGH
**Recommended Action:** Immediate account review and verification

**Key Findings:**
- 1 unusual time withdrawal (3AM ATM transaction)
- 1 unknown overseas vendor transaction
- Combined suspicious amount: $4,300.00
- Pattern: Possible compromised card activity

---

## High-Risk Anomalies

### 🔴 Transaction 1: Large ATM Withdrawal at Unusual Time

**Transaction Details:**
- Date: 2025-02-02
- Amount: -$2,800.00
- Description: ATM WITHDRAWAL - 3AM
- Merchant: ATM
- Time: 3:00 AM (unusual)

**Anomaly Indicators:**
- ⚠️ Unusual withdrawal time (outside normal 6AM-11PM pattern)
- ⚠️ Amount exceeds typical ATM withdrawal by 800%
- ⚠️ Cash withdrawal (higher fraud risk than card purchases)
- ⚠️ No recent ATM usage pattern in past 90 days

**Confidence:** 88% anomaly
**Risk Score:** 8.5/10 (HIGH)

**Suggested Actions:**
- [ ] URGENT: Verify transaction with cardholder
- [ ] Check ATM location against cardholder's known locations
- [ ] Review security camera footage if available
- [ ] Consider temporary card freeze pending verification
- [ ] If unauthorized, report to fraud department immediately

---

### 🔴 Transaction 2: Unknown Overseas Vendor Purchase

**Transaction Details:**
- Date: 2025-02-04
- Amount: -$1,500.00
- Description: Online purchase - Electronics
- Merchant: Unknown Overseas Vendor
- Location: Overseas (non-domestic)

**Anomaly Indicators:**
- ⚠️ Unknown merchant (no previous transaction history)
- ⚠️ Overseas transaction (cardholder typically domestic only)
- ⚠️ Electronics purchase (high-value, commonly targeted by fraud)
- ⚠️ No delivery address verification available

**Confidence:** 82% anomaly
**Risk Score:** 8.0/10 (HIGH)

**Suggested Actions:**
- [ ] URGENT: Contact cardholder for purchase verification
- [ ] Verify shipping address matches cardholder address
- [ ] Check for other recent overseas transactions
- [ ] Consider international travel restrictions on card
- [ ] If unauthorized, initiate chargeback and card replacement

---

## Normal Transactions

### ✅ Transaction: Gas Station Purchase
- Date: 2025-02-01
- Amount: -$45.00
- Merchant: Shell
- Status: Normal (matches historical gas purchase pattern)
- Confidence: 95% normal

### ✅ Transaction: Coffee Shop Purchase
- Date: 2025-02-03
- Amount: -$12.50
- Merchant: Starbucks
- Status: Normal (typical daily coffee purchase)
- Confidence: 98% normal

---

## Risk Timeline

```
2025-02-01: ✅ Normal activity (gas purchase)
2025-02-02: 🔴 HIGH RISK - Unusual ATM withdrawal at 3AM
2025-02-03: ✅ Normal activity (coffee)
2025-02-04: 🔴 HIGH RISK - Unknown overseas vendor
```

**Pattern Analysis:** Suspicious activity spike on Feb 2-4 following normal activity. Possible card compromise.

---

## Recommended Next Steps

### Immediate Actions (within 1 hour)
1. Contact cardholder to verify both flagged transactions
2. Temporarily freeze card to prevent additional unauthorized charges
3. Review all transactions in past 7 days for additional suspicious activity

### Short-term Actions (within 24 hours)
1. If fraud confirmed, issue new card and cancel compromised card
2. File fraud report with bank's fraud department
3. Update account alerts and security settings
4. Review and strengthen authentication methods

### Long-term Actions (within 1 week)
1. Enable transaction alerts for large purchases (>$500)
2. Set geographic restrictions on card usage
3. Enable two-factor authentication for online purchases
4. Schedule follow-up review in 30 days

---

## Statistical Analysis

**Baseline (90-day historical average):**
- Average transaction: -$67.50
- Typical transaction time: 8AM-10PM
- Geographic pattern: Domestic only
- ATM usage: 0-1 times per month

**Current Period Deviations:**
- Average increased by 220% (anomaly indicator)
- Transaction outside normal time window (3AM)
- First overseas transaction in 90 days
- ATM withdrawal 800% above typical amount

**Z-Score Analysis:**
- Transaction 1 (ATM): Z-score = 4.2σ (highly anomalous)
- Transaction 2 (Overseas): Z-score = 3.8σ (highly anomalous)

---

## Metadata

- **Agent:** lex (Local Executive Agent)
- **Session ID:** session_anomaly_check
- **Detection Model:** anomaly_detector_v1.0
- **Sensitivity Level:** High
- **Baseline Period:** 90 days
- **Processing Time:** 234ms
```

---

## Key Guarantees

1. **Accurate Categorization**: High-confidence classification based on merchant patterns, transaction history, and amount analysis
2. **Structured Output**: Consistent markdown format with YAML frontmatter
3. **Unique IDs**: Each classification gets a cryptographically secure unique ID
4. **Confidence Scoring**: Every classification includes confidence percentage (0-100%)
5. **Anomaly Detection**: Flags unusual transactions based on statistical analysis
6. **Actionable Suggestions**: Provides next steps for each classified transaction
7. **Metadata Tracking**: Full audit trail of classification process
8. **Review Workflow**: Built-in approval process for low-confidence or anomalous transactions

---

## Output Schema

**Classification File:**
- **Location:** `Transaction_Analysis/`
- **Naming:** `YYYYMMDD-HHMMSS-<merchant-slug>-<category>.md`
- **Format:** Markdown with YAML frontmatter

**Frontmatter Fields:**
```yaml
classification_id: "CLASSIFY-YYYYMMDD-HHMMSS-HASH"
transaction_id: "original_transaction_id"
date: "YYYY-MM-DD"
amount: -123.45
currency: "USD"
category: "revenue | expense | subscription | anomaly"
subcategory: "specific_subcategory"
confidence: 0.92
status: "classified | reviewed | rejected | flagged"
requires_review: false
anomaly_score: 0.05
created_at: "ISO8601 timestamp"
```

---

## Supported Categories

| Category | Subcategories | Detection Criteria |
|----------|---------------|-------------------|
| **Revenue** | Salary, Freelance, Investment, Refund, Transfer In | Positive amounts, payroll patterns, known income sources |
| **Expense** | Groceries, Dining, Transportation, Shopping, Healthcare, Entertainment | Negative amounts, merchant category codes, typical spending patterns |
| **Subscription** | Software, Streaming, Utilities, Memberships, SaaS | Recurring charges, known subscription merchants, fixed amounts |
| **Anomaly** | Unusual Large, Unknown Merchant, Duplicate, Unusual Time, Overseas | Statistical outliers, suspicious patterns, fraud indicators |

---

## Integration Points

**Upstream Skills:**
- `company_handbook_enforcer` → Ensures transaction handling complies with financial policies
- `approval_request_creator` → Requires approval for high-value or anomalous transactions

**Downstream Skills:**
- `vault_state_manager` → Stores classifications and tracks transaction lifecycle
- `dashboard_writer` → Displays spending summaries and anomaly counts

**Related Skills:**
- `time_event_scheduler` → Schedule monthly transaction reconciliation tasks
- `email_drafter` → Send anomaly alert emails to stakeholders

---

## Error Handling

**Common Errors:**

1. **Invalid CSV Format:**
   ```
   Error: CSV missing required column 'amount'
   Solution: Ensure CSV has columns: date, amount, description
   ```

2. **Invalid Transaction Amount:**
   ```
   Error: Amount must be numeric, received: 'N/A'
   Solution: Clean CSV data, ensure amounts are valid numbers
   ```

3. **Missing Transaction Date:**
   ```
   Error: Transaction date is required
   Solution: Provide date in YYYY-MM-DD format
   ```

4. **File Write Failure:**
   ```
   Error: Permission denied writing to Transaction_Analysis/
   Solution: Ensure agent has write access to vault directory
   ```

---

## Configuration Examples

### Minimal Configuration:
```bash
VAULT_PATH="/path/to/vault"
```

### With Custom Thresholds:
```bash
VAULT_PATH="/path/to/vault"
TRANSACTION_CONFIDENCE_THRESHOLD="0.80"
TRANSACTION_ANOMALY_THRESHOLD="2.5"
TRANSACTION_AUTO_APPROVE_THRESHOLD="0.95"
```

### Production Setup (with review workflow):
```bash
VAULT_PATH="/path/to/vault"
TRANSACTION_CONFIDENCE_THRESHOLD="0.85"
TRANSACTION_REQUIRE_REVIEW="true"
TRANSACTION_AUDIT_LOG_PATH="$VAULT_PATH/Audit_Logs"
TRANSACTION_RETAIN_RAW_DATA="true"
```

---

## Testing Checklist

Before deploying this skill:

- [ ] Verify `Transaction_Analysis/` folder exists and is writable
- [ ] Test single transaction classification
- [ ] Test batch CSV processing (5-100 transactions)
- [ ] Verify unique ID generation (no collisions)
- [ ] Test confidence scoring accuracy
- [ ] Test anomaly detection with unusual transactions
- [ ] Verify category assignment for all supported types
- [ ] Test with missing required fields (expect validation error)
- [ ] Test with invalid amount format (expect validation error)
- [ ] Verify audit log entries created (if configured)
- [ ] Test subscription pattern detection
- [ ] Test revenue vs expense categorization

---

## Version History

- **v1.0.0** (2025-02-04): Initial release
  - Single transaction classification
  - Batch CSV processing
  - Anomaly detection with confidence scoring
  - Support for 4 main categories (revenue, expense, subscription, anomaly)
  - Actionable suggestions per transaction
  - Markdown output with YAML frontmatter
  - Audit trail integration
  - Statistical outlier detection
