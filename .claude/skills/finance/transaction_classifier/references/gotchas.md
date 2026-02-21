# Transaction Classifier Gotchas

Common pitfalls, edge cases, and troubleshooting guide for the transaction classifier skill.

## Common Pitfalls

### 1. Merchant Name Variations

**Problem:**
Same merchant appears with different names in transaction data.

**Examples:**
- "AMZN MKTP US" vs "AMAZON.COM" vs "AMZN.COM/BILL"
- "SQ *COFFEE SHOP" vs "SQUARE *COFFEE SHOP"
- "TST* RESTAURANT NAME" (Toast POS system)
- "PAYPAL *MERCHANT" (PayPal transactions)

**Impact:**
- Breaks subscription detection (can't detect recurring pattern)
- Historical context analysis fails
- Confidence scores decrease unnecessarily

**Solution:**
```javascript
// Implement merchant name normalization
const merchantAliases = {
  'amzn mktp us': 'amazon',
  'amzn.com': 'amazon',
  'amzn.com/bill': 'amazon',
  'sq *': 'square',
  'tst*': 'toast',
  'paypal *': 'paypal'
};

function normalizeMerchant(rawName) {
  const normalized = rawName.toLowerCase().trim();

  for (const [pattern, canonical] of Object.entries(merchantAliases)) {
    if (normalized.startsWith(pattern) || normalized.includes(pattern)) {
      return canonical;
    }
  }

  return normalized;
}
```

**Configuration:**
Use `TRANSACTION_MERCHANT_ALIASES` environment variable to define custom aliases:
```bash
TRANSACTION_MERCHANT_ALIASES='{"AMZN MKTP US":"Amazon","SQ *":"Square"}'
```

---

### 2. Subscription Detection False Positives

**Problem:**
Regular non-subscription expenses misclassified as subscriptions.

**Examples:**
- Weekly grocery shopping at same store with similar amounts
- Monthly rent payments
- Regular gas station visits

**Why It Happens:**
- Recurring pattern detected (weekly/monthly)
- Similar amounts (±10% variance)
- Same merchant

**Solution:**
Add additional heuristics:
```javascript
function isSubscription(transactions) {
  // ... existing recurring pattern check ...

  // Additional checks to reduce false positives:

  // 1. Subscription merchants typically have exact amounts
  const amountVariance = calculateVariance(transactions.map(t => t.amount));
  if (amountVariance > 0.05) { // >5% variance
    return false; // Likely variable expense, not subscription
  }

  // 2. Check merchant category
  const knownSubscriptionCategories = [
    'streaming', 'software', 'saas', 'membership', 'subscription'
  ];
  if (!merchantInCategory(merchant, knownSubscriptionCategories)) {
    // Require more evidence (4+ transactions instead of 3)
    if (transactions.length < 4) {
      return false;
    }
  }

  // 3. Check for subscription keywords
  const hasSubscriptionKeywords = transactions.some(t =>
    /subscription|membership|monthly|recurring/i.test(t.description)
  );

  return hasSubscriptionKeywords || transactions.length >= 6;
}
```

**Manual Override:**
Flag specific merchants to exclude from subscription detection:
```bash
TRANSACTION_EXCLUDE_FROM_SUBSCRIPTIONS="WHOLE FOODS,SHELL,CHEVRON,SAFEWAY"
```

---

### 3. Refund Classification Ambiguity

**Problem:**
Refunds difficult to distinguish from revenue.

**Examples:**
- +$50.00 from "AMAZON.COM" - Could be refund or gift card credit
- +$1200.00 from "INSURANCE CO" - Could be claim payout or refund
- +$25.00 from "RESTAURANT" - Could be refund or tip return

**Challenge:**
Both are positive amounts, need context to distinguish.

**Solution:**
```javascript
function classifyPositiveTransaction(transaction, historicalData) {
  // Check if there's a matching negative transaction in past 90 days
  const recentExpenses = historicalData.filter(t =>
    t.merchant === transaction.merchant &&
    t.amount < 0 &&
    daysAgo(t.date) <= 90
  );

  if (recentExpenses.length > 0) {
    // Check if amount closely matches (within $5)
    const matchingAmount = recentExpenses.find(t =>
      Math.abs(Math.abs(t.amount) - transaction.amount) <= 5
    );

    if (matchingAmount) {
      return {
        category: 'Revenue',
        subcategory: 'Refund',
        confidence: 0.85,
        linkedTransaction: matchingAmount.id,
        originalCategory: matchingAmount.category
      };
    }
  }

  // Check for refund keywords
  if (/refund|return|credit|reversal/i.test(transaction.description)) {
    return {
      category: 'Revenue',
      subcategory: 'Refund',
      confidence: 0.80
    };
  }

  // Default to general revenue with lower confidence
  return {
    category: 'Revenue',
    subcategory: 'Other',
    confidence: 0.65,
    requiresReview: true
  };
}
```

---

### 4. Large Amounts Don't Always Mean Anomaly

**Problem:**
Legitimate large transactions flagged as anomalies.

**Examples:**
- Annual subscriptions ($500-$2000)
- Rent payments ($1500-$3000)
- Tax payments ($5000+)
- Medical bills ($1000-$10000)

**Why It Happens:**
Z-score calculation treats all large amounts as outliers without considering context.

**Solution:**
Implement context-aware anomaly detection:
```javascript
function detectAnomaly(transaction, historicalData) {
  const zScore = calculateZScore(transaction.amount, historicalData);

  // Exception: known large transaction categories
  const legitimateLargeCategories = [
    'rent', 'mortgage', 'tax', 'medical', 'annual subscription', 'insurance'
  ];

  if (Math.abs(zScore) > 3.0) {
    // Check if merchant/category is known for large amounts
    const merchantHistory = historicalData.filter(t =>
      t.merchant === transaction.merchant
    );

    if (merchantHistory.length >= 2) {
      const avgMerchantAmount = average(merchantHistory.map(t => Math.abs(t.amount)));

      // If current amount is within 20% of merchant's average, not anomaly
      if (Math.abs(transaction.amount) <= avgMerchantAmount * 1.2) {
        return {
          isAnomaly: false,
          reason: 'Large amount but consistent with merchant history'
        };
      }
    }

    // Check for legitimacy keywords
    const description = transaction.description.toLowerCase();
    if (legitimateLargeCategories.some(cat => description.includes(cat))) {
      return {
        isAnomaly: false,
        reason: 'Large amount in expected high-value category',
        note: 'Consider manual review for first occurrence'
      };
    }

    return {
      isAnomaly: true,
      reason: 'Unusual large amount',
      severity: zScore > 4.0 ? 'high' : 'medium'
    };
  }

  return { isAnomaly: false };
}
```

---

### 5. CSV Parsing Edge Cases

**Problem:**
CSV files with inconsistent formatting cause parsing errors.

**Common Issues:**
- Missing headers
- Different column orders
- Commas in description field (breaks CSV parsing)
- Date format variations (MM/DD/YYYY vs YYYY-MM-DD vs DD-MM-YYYY)
- Currency symbols in amount field ($1,234.56 vs 1234.56)

**Example Problematic CSV:**
```csv
Date,Description,Amount
02/04/2025,"Purchase from ""Joe's Store"", Location: Main St.",$1,234.56
```

**Solution:**
Implement robust CSV parsing:
```javascript
function parseTransactionCSV(csvContent) {
  // Use proper CSV parser (not string.split(','))
  const Papa = require('papaparse');

  const result = Papa.parse(csvContent, {
    header: true,
    skipEmptyLines: true,
    transformHeader: (header) => {
      // Normalize header names
      const normalized = header.toLowerCase().trim();
      const headerMap = {
        'trans date': 'date',
        'transaction date': 'date',
        'post date': 'date',
        'desc': 'description',
        'memo': 'description',
        'debit': 'amount',
        'credit': 'amount'
      };
      return headerMap[normalized] || normalized;
    },
    transform: (value, header) => {
      // Clean amount field
      if (header === 'amount') {
        return parseFloat(value.replace(/[$,]/g, ''));
      }

      // Normalize date
      if (header === 'date') {
        return normalizeDate(value);
      }

      return value;
    }
  });

  // Validate required columns
  const requiredColumns = ['date', 'amount', 'description'];
  const headers = result.meta.fields;

  const missingColumns = requiredColumns.filter(col => !headers.includes(col));
  if (missingColumns.length > 0) {
    throw new Error(`CSV missing required columns: ${missingColumns.join(', ')}`);
  }

  return result.data;
}

function normalizeDate(dateString) {
  // Try multiple date formats
  const formats = [
    /^(\d{4})-(\d{2})-(\d{2})$/,       // YYYY-MM-DD
    /^(\d{2})\/(\d{2})\/(\d{4})$/,     // MM/DD/YYYY
    /^(\d{2})-(\d{2})-(\d{4})$/        // DD-MM-YYYY
  ];

  for (const format of formats) {
    const match = dateString.match(format);
    if (match) {
      // Convert to YYYY-MM-DD
      if (format.source.startsWith('^(\\d{4})')) {
        return dateString; // Already in correct format
      } else if (format.source.includes('\\/')) {
        const [_, month, day, year] = match;
        return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
      } else {
        const [_, day, month, year] = match;
        return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
      }
    }
  }

  throw new Error(`Invalid date format: ${dateString}`);
}
```

---

### 6. Time Zone Issues with Timestamps

**Problem:**
Transaction timestamps in different time zones cause incorrect time-based anomaly detection.

**Example:**
- Transaction at 11:30 PM EST appears as 4:30 AM UTC
- Falsely flagged as "unusual time" anomaly

**Solution:**
```javascript
function normalizeTransactionTime(transaction) {
  // Parse timestamp with timezone awareness
  const timestamp = new Date(transaction.timestamp);

  // Convert to configured timezone (from TRANSACTION_TIMEZONE env var)
  const configuredTZ = process.env.TRANSACTION_TIMEZONE || 'UTC';

  const localTime = timestamp.toLocaleString('en-US', {
    timeZone: configuredTZ,
    hour12: false
  });

  return new Date(localTime);
}

function detectTimeAnomaly(transaction) {
  const localTime = normalizeTransactionTime(transaction);
  const hour = localTime.getHours();

  // Define normal hours based on user's timezone
  const normalHourStart = 6;  // 6 AM
  const normalHourEnd = 23;   // 11 PM

  if (hour < normalHourStart || hour >= normalHourEnd) {
    return {
      isAnomaly: true,
      reason: `Transaction at unusual hour: ${hour}:00 (local time)`,
      severity: 'medium'
    };
  }

  return { isAnomaly: false };
}
```

---

### 7. Multi-Currency Transactions

**Problem:**
Transactions in different currencies break amount-based comparisons.

**Example:**
- $100 USD vs €85 EUR vs ¥10,000 JPY
- Cannot directly compare amounts for anomaly detection

**Solution:**
```javascript
async function normalizeAmount(transaction) {
  const baseCurrency = process.env.TRANSACTION_DEFAULT_CURRENCY || 'USD';

  if (transaction.currency === baseCurrency) {
    return transaction.amount;
  }

  // Convert to base currency
  const rate = await getExchangeRate(transaction.currency, baseCurrency, transaction.date);

  return {
    originalAmount: transaction.amount,
    originalCurrency: transaction.currency,
    normalizedAmount: transaction.amount * rate,
    normalizedCurrency: baseCurrency,
    exchangeRate: rate
  };
}
```

**Configuration:**
```bash
TRANSACTION_MULTI_CURRENCY="true"
TRANSACTION_DEFAULT_CURRENCY="USD"
TRANSACTION_CURRENCY_API_KEY="your_api_key"
```

---

## Debugging Tips

### Enable Debug Logging

```bash
TRANSACTION_DEBUG="true"
TRANSACTION_LOG_LEVEL="debug"
```

This will output:
- CSV parsing details
- Merchant name normalization steps
- Confidence calculation breakdown
- Anomaly detection reasoning
- Historical data queries

### Dry Run Mode

Test classifications without writing files:

```bash
TRANSACTION_DRY_RUN="true"
```

Output will be printed to console instead of creating files.

### Manual Review Flagging

Force all transactions to require review:

```bash
TRANSACTION_REQUIRE_REVIEW="true"
```

Useful for:
- Initial setup and calibration
- Testing classification accuracy
- Training the system on your specific transaction patterns

---

## Performance Issues

### Slow Batch Processing

**Symptom:** Processing 1000+ transactions takes too long

**Causes:**
- Historical data queries for each transaction
- Synchronous processing
- Large baseline period (90+ days)

**Solutions:**

1. **Enable parallel processing:**
```bash
TRANSACTION_ENABLE_PARALLEL="true"
TRANSACTION_MAX_WORKERS="4"
```

2. **Reduce baseline period:**
```bash
TRANSACTION_BASELINE_PERIOD_DAYS="30"  # Instead of 90
```

3. **Batch historical queries:**
```javascript
// Don't query historical data per transaction
// Query once and cache
const historicalData = await loadHistoricalData(startDate, endDate);

transactions.forEach(txn => {
  const relevantHistory = historicalData.filter(h =>
    h.merchant === txn.merchant
  );
  classify(txn, relevantHistory);
});
```

---

## Common Error Messages

### "CSV missing required column 'amount'"

**Cause:** CSV file doesn't have standardized column names

**Fix:** Map your CSV columns to expected names or use TRANSACTION_CSV_COLUMN_MAPPING

### "Invalid date format: 02-04-2025"

**Cause:** Date parser doesn't recognize format

**Fix:** Configure date format:
```bash
TRANSACTION_DATE_FORMAT="DD-MM-YYYY"
```

### "Permission denied writing to Transaction_Analysis/"

**Cause:** Agent doesn't have write access to vault

**Fix:** Check file permissions:
```bash
chmod -R u+w /path/to/vault/Transaction_Analysis/
```

---

## Best Practices

1. **Start with small batches**: Test with 10-20 transactions before processing thousands
2. **Review classifications initially**: Set `TRANSACTION_REQUIRE_REVIEW="true"` for first few runs
3. **Configure merchant aliases early**: Save time by defining common merchant variations upfront
4. **Use confidence thresholds**: Set `TRANSACTION_CONFIDENCE_THRESHOLD="0.80"` for higher accuracy
5. **Enable audit logging**: Track classification decisions for troubleshooting
6. **Regular model updates**: Retrain with new data monthly for improved accuracy
