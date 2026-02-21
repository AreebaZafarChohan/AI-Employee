# Transaction Classifier Examples

Real-world usage examples for the transaction classifier skill.

## Example 1: Personal Finance Tracking

**Scenario:** Individual wants to automatically categorize monthly bank transactions for budgeting.

### Input CSV: `my_transactions.csv`

```csv
date,amount,description,merchant
2025-02-01,-125.00,WHOLE FOODS MARKET,Whole Foods
2025-02-01,2500.00,PAYROLL DEPOSIT - ACME CORP,Acme Corp
2025-02-02,-19.99,GITHUB.COM - MONTHLY,GitHub
2025-02-03,-45.00,SHELL GAS STATION,Shell
2025-02-04,-49.99,NETFLIX.COM - Subscription,Netflix
2025-02-05,-12.50,STARBUCKS COFFEE,Starbucks
2025-02-06,-1500.00,RENT PAYMENT,Property Management Co
2025-02-07,-89.99,AMAZON.COM PURCHASE,Amazon
```

### Code

```javascript
const { classifyTransactionBatch } = require('./transaction_classifier');

async function categorizeMonthlyTransactions() {
  const result = await classifyTransactionBatch({
    csv_path: "my_transactions.csv",
    options: {
      confidence_threshold: 0.70,
      anomaly_threshold: 3.0,
      include_suggestions: true,
      output_format: "markdown"
    },
    metadata: {
      agent: "personal_finance_agent",
      session_id: "session_feb_2025",
      timestamp: new Date().toISOString()
    }
  });

  console.log(`✅ Processed ${result.total_transactions} transactions`);
  console.log(`📊 Revenue: $${result.revenue_total}`);
  console.log(`💸 Expenses: $${Math.abs(result.expense_total)}`);
  console.log(`🔄 Subscriptions: $${Math.abs(result.subscription_total)}`);
  console.log(`⚠️  Anomalies: ${result.anomalies_count}`);

  return result;
}

categorizeMonthlyTransactions();
```

### Expected Output

**Summary File:** `Transaction_Analysis/20250207-100000-batch-summary.md`

```
Total Transactions: 8
Revenue: $2,500.00 (1 transaction)
Expenses: -$1,842.47 (7 transactions)
Subscriptions: -$69.98 (2 transactions)
Anomalies: 0
```

**Category Breakdown:**
- Revenue > Salary: $2,500.00
- Expense > Groceries: -$125.00
- Expense > Transportation: -$45.00
- Expense > Dining: -$12.50
- Expense > Shopping: -$89.99
- Expense > Rent: -$1,500.00
- Subscription > Software: -$19.99
- Subscription > Entertainment: -$49.99

**Actionable Insights:**
- Total subscription costs: $69.98/month ($839.76/year)
- Largest expense category: Rent (81% of expenses)
- Consider reviewing subscription value

---

## Example 2: Small Business Expense Categorization

**Scenario:** Small business needs to categorize transactions for tax reporting.

### Input CSV: `business_transactions.csv`

```csv
date,amount,description,merchant,account_id
2025-02-01,5000.00,CLIENT PAYMENT - PROJECT A,Client Corp,business_checking
2025-02-02,-850.00,GOOGLE WORKSPACE ANNUAL,Google,business_credit
2025-02-03,-1200.00,OFFICE RENT,Landlord LLC,business_checking
2025-02-04,-45.00,INTERNET SERVICE - FEB,Comcast,business_checking
2025-02-05,-2500.00,CONTRACTOR PAYMENT,Freelancer,business_checking
2025-02-06,-89.00,OFFICE SUPPLIES - STAPLES,Staples,business_credit
2025-02-07,3500.00,CLIENT PAYMENT - PROJECT B,Another Client,business_checking
```

### Code

```javascript
const { classifyTransactionBatch } = require('./transaction_classifier');

async function categorizeBusinessTransactions() {
  const result = await classifyTransactionBatch({
    csv_path: "business_transactions.csv",
    options: {
      confidence_threshold: 0.80, // Higher threshold for tax accuracy
      custom_categories: {
        "contractor_payment": "Expense > Contractor Services",
        "office_expense": "Expense > Office Supplies"
      },
      include_tax_guidance: true
    },
    metadata: {
      agent: "business_finance_agent",
      business_context: "small_business_llc",
      tax_year: "2025"
    }
  });

  // Generate tax summary
  const taxSummary = {
    revenue: result.transactions.filter(t => t.category === 'Revenue'),
    deductible_expenses: result.transactions.filter(t =>
      t.category === 'Expense' && t.tax_deductible
    ),
    subscriptions: result.transactions.filter(t => t.category === 'Subscription')
  };

  console.log(`💼 Business Income: $${taxSummary.revenue.reduce((sum, t) => sum + t.amount, 0)}`);
  console.log(`📝 Deductible Expenses: $${Math.abs(taxSummary.deductible_expenses.reduce((sum, t) => sum + t.amount, 0))}`);

  return taxSummary;
}

categorizeBusinessTransactions();
```

### Expected Output

**Tax Summary:**
- **Revenue:** $8,500.00
  - Client payments: 2 transactions
  - All qualify as business income
- **Deductible Expenses:** -$4,684.00
  - Office rent: -$1,200.00 (100% deductible)
  - Contractor payment: -$2,500.00 (requires 1099 filing)
  - Office supplies: -$89.00 (100% deductible)
  - Software subscription: -$850.00 (annual, amortize over 12 months)
  - Internet service: -$45.00 (100% deductible if dedicated business line)

**Tax Recommendations:**
- ✅ Ensure 1099-NEC issued to contractor ($2,500 payment)
- ✅ Amortize Google Workspace annual payment over 12 months
- ✅ Document business use percentage for internet service
- ✅ Keep receipts for office supply purchases

---

## Example 3: Anomaly Detection and Fraud Monitoring

**Scenario:** Monitoring transactions for unusual activity that might indicate fraud.

### Input

```javascript
const { detectAnomalies } = require('./transaction_classifier');

async function monitorForFraud() {
  const recentTransactions = [
    { date: "2025-02-01", amount: -45.00, description: "Shell Gas Station", merchant: "Shell" },
    { date: "2025-02-02", amount: -2800.00, description: "ATM WITHDRAWAL 3AM", merchant: "ATM", timestamp: "2025-02-02T03:00:00Z" },
    { date: "2025-02-03", amount: -12.50, description: "Starbucks", merchant: "Starbucks" },
    { date: "2025-02-04", amount: -1500.00, description: "Wire Transfer - Unknown Recipient", merchant: "Unknown" },
    { date: "2025-02-05", amount: -55.00, description: "Restaurant Purchase", merchant: "Local Restaurant" },
    { date: "2025-02-05", amount: -55.00, description: "Restaurant Purchase", merchant: "Local Restaurant", timestamp: "2025-02-05T12:03:00Z" } // Duplicate
  ];

  const anomalyReport = await detectAnomalies({
    transactions: recentTransactions,
    options: {
      anomaly_sensitivity: "high",
      flag_patterns: ["unusual_time", "large_amount", "unknown_merchant", "duplicate"],
      baseline_period_days: 90
    }
  });

  // Send alerts for high-risk anomalies
  for (const anomaly of anomalyReport.high_risk_anomalies) {
    console.log(`🔴 HIGH RISK ALERT`);
    console.log(`Amount: $${Math.abs(anomaly.amount)}`);
    console.log(`Merchant: ${anomaly.merchant}`);
    console.log(`Risk Score: ${anomaly.risk_score}/10`);
    console.log(`Flags: ${anomaly.flags.join(', ')}`);
    console.log(`Recommended Action: ${anomaly.suggested_action}`);
    console.log('---');

    // Send email alert (integration with email_drafter skill)
    await sendFraudAlert(anomaly);
  }

  return anomalyReport;
}

async function sendFraudAlert(anomaly) {
  const { draftEmail } = require('../communication/email_drafter');

  await draftEmail({
    intent: "fraud_alert",
    recipient: {
      email: "security@company.com",
      type: "security_team"
    },
    context: {
      transaction_id: anomaly.transaction_id,
      amount: anomaly.amount,
      merchant: anomaly.merchant,
      risk_score: anomaly.risk_score,
      flags: anomaly.flags,
      suggested_action: anomaly.suggested_action
    },
    tone: "urgent",
    key_points: [
      `High-risk transaction detected: $${Math.abs(anomaly.amount)}`,
      `Merchant: ${anomaly.merchant}`,
      `Risk flags: ${anomaly.flags.join(', ')}`,
      "Immediate verification required"
    ]
  });
}

monitorForFraud();
```

### Expected Anomalies Detected

**🔴 Anomaly 1: Large ATM Withdrawal at Unusual Time**
- Amount: -$2,800.00
- Time: 3:00 AM
- Risk Score: 8.5/10
- Flags:
  - Unusual time (outside 6AM-11PM window)
  - Large amount (>3σ from mean)
  - Cash withdrawal (higher fraud risk)
- Suggested Action: Contact cardholder immediately, consider temporary card freeze

**🔴 Anomaly 2: Unknown Wire Transfer**
- Amount: -$1,500.00
- Merchant: Unknown
- Risk Score: 8.0/10
- Flags:
  - Unknown recipient
  - Wire transfer (irreversible)
  - No historical pattern
- Suggested Action: Verify authorization, check for fraud indicators

**🟠 Anomaly 3: Duplicate Transaction**
- Amount: -$55.00
- Merchant: Local Restaurant
- Risk Score: 6.0/10
- Flags:
  - Duplicate transaction within 5 minutes
- Suggested Action: Check with merchant, consider chargeback if unauthorized

---

## Example 4: Subscription Tracking and Management

**Scenario:** Identify all recurring subscriptions and track spending.

### Code

```javascript
const { classifyTransactionBatch } = require('./transaction_classifier');

async function trackSubscriptions() {
  // Process last 6 months of transactions
  const result = await classifyTransactionBatch({
    csv_path: "transactions_6months.csv",
    options: {
      detect_subscriptions: true,
      subscription_minimum_occurrences: 3,
      subscription_variance_tolerance: 0.05 // 5%
    }
  });

  const subscriptions = result.transactions
    .filter(t => t.category === 'Subscription')
    .reduce((acc, txn) => {
      const key = txn.merchant;
      if (!acc[key]) {
        acc[key] = {
          merchant: txn.merchant,
          subcategory: txn.subcategory,
          avg_amount: 0,
          frequency: null,
          occurrences: 0,
          total_spent: 0
        };
      }
      acc[key].occurrences++;
      acc[key].total_spent += Math.abs(txn.amount);
      return acc;
    }, {});

  // Calculate averages and frequencies
  for (const merchant in subscriptions) {
    const sub = subscriptions[merchant];
    sub.avg_amount = sub.total_spent / sub.occurrences;

    // Estimate frequency based on 6 months
    const monthlyFrequency = sub.occurrences / 6;
    sub.frequency = monthlyFrequency >= 0.9 ? 'monthly' :
                    monthlyFrequency >= 0.4 ? 'quarterly' :
                    'annual';

    sub.annual_cost = sub.frequency === 'monthly' ? sub.avg_amount * 12 :
                      sub.frequency === 'quarterly' ? sub.avg_amount * 4 :
                      sub.avg_amount;
  }

  // Generate subscription report
  console.log('📊 Subscription Report\n');
  console.log('Monthly Subscriptions:');
  Object.values(subscriptions)
    .filter(s => s.frequency === 'monthly')
    .sort((a, b) => b.avg_amount - a.avg_amount)
    .forEach(sub => {
      console.log(`  ${sub.merchant}: $${sub.avg_amount.toFixed(2)}/month ($${sub.annual_cost.toFixed(2)}/year)`);
    });

  const totalAnnual = Object.values(subscriptions)
    .reduce((sum, sub) => sum + sub.annual_cost, 0);

  console.log(`\n💰 Total Annual Subscription Cost: $${totalAnnual.toFixed(2)}`);

  // Optimization suggestions
  console.log('\n💡 Optimization Suggestions:');
  const topSubscriptions = Object.values(subscriptions)
    .sort((a, b) => b.annual_cost - a.annual_cost)
    .slice(0, 3);

  topSubscriptions.forEach((sub, i) => {
    console.log(`${i + 1}. ${sub.merchant} ($${sub.annual_cost.toFixed(2)}/year):`);
    console.log(`   - Review usage to ensure value for cost`);
    if (sub.frequency === 'monthly') {
      console.log(`   - Consider annual plan for potential 10-20% savings`);
    }
    console.log(`   - Check for family/team plan options`);
  });

  return subscriptions;
}

trackSubscriptions();
```

### Expected Output

```
📊 Subscription Report

Monthly Subscriptions:
  Netflix: $15.99/month ($191.88/year)
  Spotify: $9.99/month ($119.88/year)
  GitHub: $7.00/month ($84.00/year)
  Adobe Creative Cloud: $54.99/month ($659.88/year)
  Microsoft 365: $9.99/month ($119.88/year)
  Dropbox: $11.99/month ($143.88/year)

💰 Total Annual Subscription Cost: $1,319.40

💡 Optimization Suggestions:
1. Adobe Creative Cloud ($659.88/year):
   - Review usage to ensure value for cost
   - Consider annual plan for potential 10-20% savings
   - Check for family/team plan options

2. Netflix ($191.88/year):
   - Review usage to ensure value for cost
   - Consider annual plan for potential 10-20% savings
   - Check for family/team plan options

3. Dropbox ($143.88/year):
   - Review usage to ensure value for cost
   - Consider annual plan for potential 10-20% savings
   - Check for family/team plan options

💡 Potential Savings: $130-260/year by switching to annual plans
```

---

## Example 5: Integration with Accounting Software

**Scenario:** Automatically export classified transactions to QuickBooks.

### Code

```javascript
const { classifyTransactionBatch } = require('./transaction_classifier');
const { exportToQuickBooks } = require('./exporters/quickbooks');

async function syncToAccountingSoftware() {
  // Classify transactions
  const result = await classifyTransactionBatch({
    csv_path: "transactions.csv",
    options: {
      confidence_threshold: 0.85, // High threshold for accounting accuracy
      require_review_if_below: true
    }
  });

  // Map categories to QuickBooks accounts
  const categoryMapping = {
    'Revenue > Salary': 'Income:Payroll',
    'Revenue > Freelance': 'Income:Contract Work',
    'Expense > Groceries': 'Expenses:Food',
    'Expense > Dining': 'Expenses:Meals & Entertainment',
    'Expense > Transportation': 'Expenses:Auto & Travel',
    'Subscription > Software': 'Expenses:Software & Subscriptions',
    'Subscription > Streaming': 'Expenses:Entertainment',
    'Expense > Rent': 'Expenses:Rent',
    'Expense > Shopping': 'Expenses:General'
  };

  // Prepare for export (only high-confidence classifications)
  const exportTransactions = result.transactions
    .filter(t => t.confidence >= 0.85 && !t.requires_review)
    .map(t => ({
      date: t.date,
      amount: t.amount,
      description: t.description,
      category: categoryMapping[`${t.category} > ${t.subcategory}`] || 'Uncategorized',
      merchant: t.merchant,
      transaction_id: t.transaction_id
    }));

  // Export to QuickBooks
  const exportResult = await exportToQuickBooks(exportTransactions, {
    format: 'IIF', // QuickBooks import format
    output_path: 'quickbooks_import.iif'
  });

  console.log(`✅ Exported ${exportResult.exported_count} transactions to QuickBooks`);
  console.log(`⚠️  Skipped ${exportResult.skipped_count} low-confidence transactions for manual review`);

  // Generate review list for low-confidence transactions
  const reviewList = result.transactions.filter(t => t.requires_review);
  if (reviewList.length > 0) {
    console.log(`\n📋 Transactions requiring manual review:`);
    reviewList.forEach(t => {
      console.log(`  - ${t.date}: ${t.merchant} ($${Math.abs(t.amount)}) - Confidence: ${(t.confidence * 100).toFixed(0)}%`);
    });
  }

  return { exportResult, reviewList };
}

syncToAccountingSoftware();
```

---

## Example 6: Real-Time Transaction Monitoring

**Scenario:** Monitor bank account for new transactions and classify in real-time.

### Code

```javascript
const { classifyTransaction } = require('./transaction_classifier');
const { watchBankFeed } = require('./integrations/bank_api');

async function monitorTransactionsRealTime() {
  console.log('🔍 Starting real-time transaction monitoring...');

  // Subscribe to bank transaction feed
  watchBankFeed({
    account_id: 'acct_12345',
    onNewTransaction: async (transaction) => {
      console.log(`\n📥 New transaction received: ${transaction.merchant} - $${Math.abs(transaction.amount)}`);

      // Classify immediately
      const classification = await classifyTransaction({
        transaction: transaction,
        options: {
          include_suggestions: true,
          flag_anomalies: true
        }
      });

      console.log(`✅ Classified as: ${classification.category} > ${classification.subcategory}`);
      console.log(`📊 Confidence: ${(classification.confidence * 100).toFixed(0)}%`);

      // Check for anomalies
      if (classification.anomaly_score > 0.8) {
        console.log(`⚠️  ANOMALY DETECTED - Risk Score: ${classification.risk_score}/10`);

        // Send immediate alert
        await sendImmediateAlert({
          type: 'anomaly',
          transaction: transaction,
          classification: classification
        });

        // Optionally freeze card for very high risk
        if (classification.risk_score >= 9.0) {
          console.log(`🔴 HIGH RISK - Consider freezing card`);
          // await freezeCard(transaction.account_id);
        }
      }

      // Log for daily summary
      await logToDaily Summary(classification);
    }
  });
}

async function sendImmediateAlert(alert) {
  const { draftEmail } = require('../communication/email_drafter');

  await draftEmail({
    intent: "real_time_alert",
    recipient: { email: "alerts@company.com" },
    context: alert,
    tone: "urgent"
  });
}

monitorTransactionsRealTime();
```

---

## Running the Examples

### Install Dependencies
```bash
npm install papaparse  # CSV parsing
npm install date-fns    # Date utilities
```

### Execute Example Scripts
```bash
node examples/personal_finance_tracking.js
node examples/business_expense_categorization.js
node examples/anomaly_detection.js
node examples/subscription_tracking.js
```

### Custom Example Template
```javascript
const { classifyTransaction } = require('./transaction_classifier');

async function myCustomExample() {
  // Your custom logic here
  const result = await classifyTransaction({
    transaction: {
      date: "2025-02-04",
      amount: -100.00,
      description: "Your merchant",
      merchant: "Merchant Name"
    },
    options: {
      // Your options
    }
  });

  console.log(result);
}

myCustomExample();
```

---

For more examples and use cases, see the SKILL.md documentation.
