# Transaction Classification Patterns

This document describes common patterns for transaction classification and how the skill identifies different transaction types.

## Category Detection Patterns

### Revenue (Income) Detection

**Pattern Indicators:**
- Positive transaction amounts
- Known payroll processors (ADP, Paychex, Gusto)
- Keywords: "PAYROLL", "SALARY", "DEPOSIT", "INCOME", "PAYMENT RECEIVED"
- Regular recurring deposits (bi-weekly, monthly patterns)
- Direct deposits from known employers
- Refunds from merchants (amount reversal)

**Subcategories:**
- **Salary/Payroll**: Regular deposits from employer
- **Freelance/Contract**: Payments from clients, platforms (Upwork, Fiverr)
- **Investment**: Dividends, interest, capital gains
- **Refund**: Product returns, service cancellations
- **Transfer In**: From savings, other accounts

**Example Patterns:**
```
ADP PAYROLL -> Revenue > Salary
UPWORK PAYMENT -> Revenue > Freelance
DIVIDEND - VANGUARD -> Revenue > Investment
REFUND AMAZON.COM -> Revenue > Refund
TRANSFER FROM SAVINGS -> Revenue > Transfer In
```

---

### Expense Detection

**Pattern Indicators:**
- Negative transaction amounts
- Known merchant categories (grocery, gas, retail)
- Keywords: "PURCHASE", "PAYMENT TO", "DEBIT"
- One-time or irregular purchases
- Point-of-sale (POS) transactions

**Subcategories:**
- **Groceries**: Supermarkets, food stores
- **Dining**: Restaurants, cafes, food delivery
- **Transportation**: Gas, parking, tolls, rideshare
- **Shopping**: Retail stores, online marketplaces
- **Healthcare**: Medical, pharmacy, insurance
- **Entertainment**: Movies, concerts, events
- **Utilities**: Electric, water, internet (non-recurring)
- **Other**: Miscellaneous one-time expenses

**Merchant Patterns:**
```
Groceries:
- WHOLE FOODS, SAFEWAY, TRADER JOE, COSTCO, TARGET
- Keywords: MARKET, GROCERY, FOOD STORE

Dining:
- STARBUCKS, CHIPOTLE, MCDONALD, UBER EATS, DOORDASH
- Keywords: RESTAURANT, CAFE, COFFEE, PIZZA, GRILL

Transportation:
- SHELL, CHEVRON, BP, UBER, LYFT, PARKING
- Keywords: GAS, FUEL, PARKING, TOLL, RIDE

Shopping:
- AMAZON, WALMART, TARGET, BEST BUY, MACY
- Keywords: PURCHASE, RETAIL, STORE

Healthcare:
- CVS PHARMACY, WALGREENS, URGENT CARE, DR.
- Keywords: PHARMACY, MEDICAL, DENTAL, DOCTOR, HEALTH
```

---

### Subscription Detection

**Pattern Indicators:**
- Recurring charges (same amount, regular interval)
- Known subscription merchants
- Keywords: "MONTHLY", "SUBSCRIPTION", "MEMBERSHIP", "RECURRING"
- Fixed amount charges (no variation)
- Predictable billing dates

**Subcategories:**
- **Software/SaaS**: GitHub, Adobe, Microsoft, Google Workspace
- **Streaming**: Netflix, Spotify, Disney+, HBO, YouTube Premium
- **Utilities**: Electric, water, internet (recurring)
- **Memberships**: Gym, clubs, professional associations
- **Cloud Services**: AWS, Azure, Digital Ocean

**Detection Logic:**
```javascript
function isSubscription(transactions) {
  // Check for at least 3 transactions from same merchant
  // with similar amounts within ±5% tolerance
  // occurring at regular intervals (monthly, yearly)

  const merchantTransactions = groupByMerchant(transactions);

  for (const merchant in merchantTransactions) {
    const txns = merchantTransactions[merchant];

    if (txns.length >= 3) {
      const amounts = txns.map(t => t.amount);
      const avgAmount = average(amounts);
      const variance = standardDeviation(amounts) / avgAmount;

      // Low variance indicates fixed amount
      if (variance < 0.05) {
        const intervals = calculateIntervals(txns);
        const avgInterval = average(intervals);

        // Check if interval is ~30 days (monthly) or ~365 days (yearly)
        if (isNear(avgInterval, 30, 5) || isNear(avgInterval, 365, 15)) {
          return {
            isSubscription: true,
            frequency: avgInterval < 100 ? 'monthly' : 'yearly',
            avgAmount: avgAmount
          };
        }
      }
    }
  }

  return { isSubscription: false };
}
```

**Example Patterns:**
```
NETFLIX.COM         -> Subscription > Streaming (monthly, $15.99)
GITHUB.COM          -> Subscription > Software (monthly, $7.00)
SPOTIFY             -> Subscription > Streaming (monthly, $9.99)
AWS                 -> Subscription > Cloud Services (monthly, varies)
BLUE CROSS BLUE SHIELD -> Subscription > Insurance (monthly, fixed)
```

---

### Anomaly Detection

**Pattern Indicators:**
- Statistical outliers (>3σ from mean)
- Unusual transaction times (late night, early morning)
- Unknown or new merchants
- Overseas transactions (if cardholder is domestic)
- Duplicate transactions (same amount, merchant, time)
- Large amounts (exceeding typical spending)
- Sudden spending pattern changes

**Anomaly Types:**
- **Unusual Large**: Amount significantly above average
- **Unknown Merchant**: No previous transaction history
- **Duplicate**: Multiple identical transactions
- **Unusual Time**: Transaction outside normal hours (11PM-6AM)
- **Overseas**: International transaction from typically domestic account
- **Velocity**: Multiple transactions in short time period

**Detection Algorithms:**

**1. Z-Score Analysis:**
```javascript
function calculateZScore(transaction, historicalData) {
  const amounts = historicalData.map(t => Math.abs(t.amount));
  const mean = average(amounts);
  const stdDev = standardDeviation(amounts);

  const zScore = (Math.abs(transaction.amount) - mean) / stdDev;

  return {
    zScore: zScore,
    isAnomaly: zScore > 3.0,  // >3 standard deviations
    severity: zScore > 4.0 ? 'high' : zScore > 3.0 ? 'medium' : 'low'
  };
}
```

**2. Time-Based Anomaly:**
```javascript
function detectTimeAnomaly(transaction) {
  const hour = new Date(transaction.timestamp).getHours();

  // Flag transactions between 11PM and 6AM as unusual
  if (hour >= 23 || hour < 6) {
    return {
      isAnomaly: true,
      reason: `Unusual transaction time: ${hour}:00`,
      severity: 'medium'
    };
  }

  return { isAnomaly: false };
}
```

**3. Merchant Recognition:**
```javascript
function detectUnknownMerchant(transaction, historicalData) {
  const knownMerchants = new Set(
    historicalData.map(t => t.merchant.toLowerCase())
  );

  const currentMerchant = transaction.merchant.toLowerCase();

  if (!knownMerchants.has(currentMerchant)) {
    // Check if it's a variation of a known merchant
    const similar = findSimilarMerchants(currentMerchant, knownMerchants);

    if (similar.length === 0) {
      return {
        isAnomaly: true,
        reason: 'Unknown merchant with no transaction history',
        severity: 'high'
      };
    }
  }

  return { isAnomaly: false };
}
```

**4. Duplicate Detection:**
```javascript
function detectDuplicates(transaction, recentTransactions) {
  const timeWindow = 5 * 60 * 1000; // 5 minutes

  const duplicates = recentTransactions.filter(t => {
    const timeDiff = Math.abs(
      new Date(transaction.timestamp) - new Date(t.timestamp)
    );

    return timeDiff < timeWindow &&
           t.amount === transaction.amount &&
           t.merchant === transaction.merchant;
  });

  if (duplicates.length > 0) {
    return {
      isAnomaly: true,
      reason: `Potential duplicate: ${duplicates.length} identical transaction(s) within 5 minutes`,
      severity: 'high'
    };
  }

  return { isAnomaly: false };
}
```

---

## Confidence Scoring

The skill calculates a confidence score (0-100%) for each classification based on multiple factors.

### Confidence Factors

**High Confidence Indicators (+):**
- Exact merchant name match with known merchant database
- Multiple previous transactions from same merchant
- Transaction amount matches historical pattern
- Category confirmed by merchant category code (MCC)
- Clear category keywords in transaction description
- Recurring pattern detected (for subscriptions)

**Low Confidence Indicators (-):**
- Unknown merchant (no previous transactions)
- Ambiguous transaction description
- Amount significantly different from historical pattern
- Generic merchant name (e.g., "ONLINE PURCHASE")
- Missing merchant category code
- Conflicting category signals

### Confidence Calculation Formula

```javascript
function calculateConfidence(transaction, classification, historicalData) {
  let confidence = 0.5; // Start at 50% baseline

  // Merchant recognition (+20%)
  if (isKnownMerchant(transaction.merchant, historicalData)) {
    confidence += 0.20;
  }

  // Historical pattern match (+15%)
  if (matchesHistoricalPattern(transaction, historicalData)) {
    confidence += 0.15;
  }

  // Description keyword match (+10%)
  if (hasStrongKeywords(transaction.description, classification.category)) {
    confidence += 0.10;
  }

  // Merchant Category Code match (+10%)
  if (transaction.mcc && mccMatchesCategory(transaction.mcc, classification.category)) {
    confidence += 0.10;
  }

  // Amount consistency (+5%)
  if (amountConsistentWithCategory(transaction.amount, classification.category)) {
    confidence += 0.05;
  }

  // Penalties

  // Ambiguous description (-15%)
  if (hasAmbiguousDescription(transaction.description)) {
    confidence -= 0.15;
  }

  // Outlier amount (-10%)
  if (isAmountOutlier(transaction.amount, historicalData)) {
    confidence -= 0.10;
  }

  // Unknown merchant (-20%)
  if (!isKnownMerchant(transaction.merchant, historicalData)) {
    confidence -= 0.20;
  }

  // Clamp to 0-1 range
  return Math.max(0, Math.min(1, confidence));
}
```

---

## Merchant Database

The skill maintains a database of known merchant patterns for accurate classification.

### Merchant Categories

```yaml
Groceries:
  - whole foods
  - trader joe
  - safeway
  - kroger
  - publix
  - costco
  - target

Dining:
  - starbucks
  - chipotle
  - panera
  - chick-fil-a
  - uber eats
  - doordash
  - grubhub

Software/SaaS:
  - github
  - adobe
  - microsoft 365
  - google workspace
  - dropbox
  - slack
  - zoom

Streaming:
  - netflix
  - spotify
  - hulu
  - disney+
  - hbo max
  - youtube premium
  - amazon prime

Transportation:
  - uber
  - lyft
  - shell
  - chevron
  - bp
  - parking

Cloud Services:
  - aws
  - azure
  - digital ocean
  - heroku
  - vercel
```

### Merchant Name Normalization

```javascript
function normalizeMerchant(rawMerchant) {
  let normalized = rawMerchant.toLowerCase().trim();

  // Remove common suffixes
  normalized = normalized
    .replace(/\s+(inc|llc|ltd|corp|co)\s*$/i, '')
    .replace(/\s+\d+$/, '') // Remove trailing numbers
    .replace(/[^a-z0-9\s]/g, ''); // Remove special characters

  // Apply known aliases
  const aliases = {
    'amzn mktp us': 'amazon',
    'amzn.com': 'amazon',
    'sq *': 'square',
    'tst*': 'toast',
    'spotify p': 'spotify'
  };

  for (const [alias, canonical] of Object.entries(aliases)) {
    if (normalized.includes(alias)) {
      return canonical;
    }
  }

  return normalized;
}
```

---

## Special Cases

### Split Transactions

Some transactions span multiple categories (e.g., Target purchase including groceries and clothing).

**Handling:**
- Classify by primary category (largest portion)
- Note in classification that transaction may include multiple categories
- Suggest manual review if amounts are ambiguous

### Refunds and Returns

**Detection:**
- Positive amount from merchant with previous negative transaction
- Keywords: "REFUND", "RETURN", "CREDIT"

**Classification:**
- Categorize as "Revenue > Refund"
- Link to original purchase transaction if available
- Note original category in metadata

### Transfers Between Own Accounts

**Detection:**
- Keywords: "TRANSFER", "FROM SAVINGS", "TO CHECKING"
- Amount matches between two accounts

**Classification:**
- Categorize as "Transfer" (neutral, not income or expense)
- Do not include in spending analysis
- Flag as informational only

---

## Testing Patterns

Use these test cases to validate classification accuracy:

```javascript
const testCases = [
  // Revenue
  { amount: 3000, description: "ADP PAYROLL", expected: "Revenue > Salary", confidence: ">0.95" },
  { amount: 500, description: "UPWORK PAYMENT", expected: "Revenue > Freelance", confidence: ">0.90" },

  // Expenses
  { amount: -45.67, description: "WHOLE FOODS MARKET", expected: "Expense > Groceries", confidence: ">0.90" },
  { amount: -12.50, description: "STARBUCKS", expected: "Expense > Dining", confidence: ">0.90" },

  // Subscriptions
  { amount: -9.99, description: "SPOTIFY", expected: "Subscription > Streaming", confidence: ">0.90" },
  { amount: -15.99, description: "NETFLIX.COM", expected: "Subscription > Streaming", confidence: ">0.95" },

  // Anomalies
  { amount: -5000, description: "WIRE TRANSFER", expected: "Anomaly > Unusual Large", confidence: ">0.80" },
  { amount: -200, description: "UNKNOWN MERCHANT 3AM", expected: "Anomaly > Unknown + Unusual Time", confidence: ">0.75" }
];
```
