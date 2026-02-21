# Invoice Generator - Common Issues and Gotchas

Common problems, edge cases, and solutions when using the invoice generator skill.

---

## Issue 1: Invoice Number Collision

**Problem:**
```
Error: Invoice number INV-10001 already exists
```

**Cause:**
- Manual invoice number assignment conflicts with auto-generated numbers
- Concurrent invoice generation without proper locking
- Invoice deleted but number not released

**Solutions:**

1. **Let the system auto-generate invoice numbers:**
```javascript
// ❌ DON'T: Manually assign invoice numbers
const invoice = await generateInvoice({
  invoice_number: "INV-10001",  // Risky!
  ...
});

// ✅ DO: Let system auto-generate
const invoice = await generateInvoice({
  // No invoice_number specified - system assigns next available
  ...
});
```

2. **Use proper locking for concurrent generation:**
```javascript
const lock = await acquireInvoiceLock();
try {
  const invoice = await generateInvoice({...});
} finally {
  await releaseLock(lock);
}
```

3. **Check for next available number:**
```javascript
const nextNumber = await getNextInvoiceNumber();
console.log(`Next invoice will be: ${nextNumber}`);
```

---

## Issue 2: Tax Calculation Mismatch

**Problem:**
```
Expected tax: $480.00
Actual tax: $520.00
```

**Cause:**
- Tax applied to non-taxable items (expenses)
- Incorrect tax rate format (8 instead of 0.08)
- Tax compounding on discounted amounts

**Solutions:**

1. **Use decimal format for tax rates:**
```javascript
// ❌ DON'T: Use percentage
options: {
  tax_rate: 8  // Wrong!
}

// ✅ DO: Use decimal
options: {
  tax_rate: 0.08  // 8%
}
```

2. **Specify which items are taxable:**
```javascript
options: {
  tax_rate: 0.08,
  tax_applies_to: ["services"],  // Not expenses
  taxable_items: [0, 1, 2]  // Tax only first 3 line items
}
```

3. **Verify tax calculation:**
```javascript
const expectedTax = subtotal * tax_rate;
const actualTax = invoice.tax_amount;

if (Math.abs(expectedTax - actualTax) > 0.01) {
  console.warn(`Tax mismatch: expected ${expectedTax}, got ${actualTax}`);
}
```

---

## Issue 3: Client Email Validation Failure

**Problem:**
```
Error: Invalid client email format
```

**Cause:**
- Missing @ symbol
- Extra spaces in email
- Invalid domain
- Multiple emails in one field

**Solutions:**

1. **Validate email before invoice generation:**
```javascript
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email.trim());
}

if (!validateEmail(client.email)) {
  throw new Error(`Invalid email: ${client.email}`);
}
```

2. **Handle multiple recipients:**
```javascript
// ❌ DON'T: Put multiple emails in email field
client: {
  email: "billing@acme.com, finance@acme.com"  // Wrong!
}

// ✅ DO: Use primary email + CC list
client: {
  email: "billing@acme.com",
  cc_emails: ["finance@acme.com", "manager@acme.com"]
}
```

---

## Issue 4: Expense Reimbursement Tax Applied Incorrectly

**Problem:**
Tax is being applied to expense reimbursements, inflating the total.

**Cause:**
Default behavior taxes all line items, including expenses.

**Solution:**

```javascript
// ✅ Explicitly exclude expenses from tax
options: {
  tax_rate: 0.08,
  tax_applies_to: ["services"],  // Only tax service items
  taxable_expense_categories: []  // No expense categories taxed
}
```

**Verification:**
```javascript
// Verify services taxed, expenses not taxed
const serviceTotal = items.reduce((sum, item) => sum + (item.quantity * item.rate), 0);
const expenseTotal = expenses.reduce((sum, exp) => sum + exp.amount, 0);
const expectedTax = serviceTotal * tax_rate;  // Expenses NOT included

assert(invoice.tax_amount === expectedTax, "Tax should only apply to services");
```

---

## Issue 5: Odoo Import Fails with "Partner Not Found"

**Problem:**
```
Odoo Error: Partner ID 999 does not exist
```

**Cause:**
- Incorrect partner_id in odoo_config
- Partner archived/deleted in Odoo
- Wrong Odoo database specified

**Solutions:**

1. **Verify partner_id in Odoo first:**
```bash
# Search for partner in Odoo
curl -X POST "https://your-company.odoo.com/jsonrpc" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "service": "object",
      "method": "execute",
      "args": ["database", "uid", "password", "res.partner", "search", [["name", "=", "Acme Corporation"]]]
    },
    "id": 1
  }'
```

2. **Create client in Odoo if missing:**
```javascript
const odooPartner = await createOdooPartner({
  name: client.name,
  email: client.email,
  street: client.address
});

odoo_config.partner_id = odooPartner.id;
```

3. **Store Odoo partner_id in client record:**
```javascript
// Store mapping for future invoices
await updateClient(client.client_id, {
  odoo_partner_id: 123
});
```

---

## Issue 6: Currency Conversion Rounding Errors

**Problem:**
```
Subtotal in EUR: €10,000.00
Converted to USD: $10,799.9999
Expected: $10,800.00
```

**Cause:**
Floating-point arithmetic precision issues.

**Solutions:**

1. **Use proper rounding:**
```javascript
function roundCurrency(amount, decimals = 2) {
  return Math.round(amount * Math.pow(10, decimals)) / Math.pow(10, decimals);
}

const convertedAmount = roundCurrency(amountEUR * exchangeRate);
```

2. **Use a decimal library:**
```javascript
const Decimal = require('decimal.js');

const amountUSD = new Decimal(amountEUR)
  .times(exchangeRate)
  .toDecimalPlaces(2)
  .toNumber();
```

---

## Issue 7: PDF Generation Fails with Unicode Characters

**Problem:**
Invoice markdown contains special characters (é, ñ, €) that don't render in PDF.

**Cause:**
PDF generator doesn't support UTF-8 encoding properly.

**Solutions:**

1. **Use XeLaTeX for Pandoc:**
```bash
# ❌ DON'T: Use default pdflatex
pandoc invoice.md -o invoice.pdf

# ✅ DO: Use XeLaTeX with UTF-8 support
pandoc invoice.md -o invoice.pdf --pdf-engine=xelatex
```

2. **Specify UTF-8 encoding:**
```bash
pandoc invoice.md -o invoice.pdf \
  --pdf-engine=xelatex \
  --variable mainfont="DejaVu Sans" \
  --metadata charset=utf-8
```

---

## Issue 8: Late Fee Calculation Compounds Too Aggressively

**Problem:**
Late fees accumulate too quickly, damaging client relationships.

**Cause:**
Daily compounding instead of monthly.

**Solution:**

```javascript
// ❌ DON'T: Compound daily
const daysOverdue = getDaysOverdue(invoice.due_date);
const lateFee = invoice.total * (LATE_FEE_PERCENT / 100) * daysOverdue;  // Wrong!

// ✅ DO: Compound monthly
const monthsOverdue = Math.ceil(daysOverdue / 30);
const lateFee = invoice.total * (LATE_FEE_PERCENT / 100) * monthsOverdue;

// ✅ BETTER: Cap maximum late fee
const maxLateFee = invoice.total * 0.15;  // Cap at 15% of original
const lateFee = Math.min(
  invoice.total * (LATE_FEE_PERCENT / 100) * monthsOverdue,
  maxLateFee
);
```

---

## Issue 9: Timesheet Hours Don't Match Invoice Hours

**Problem:**
```
Timesheet total: 42.5 hours
Invoice line item: 40 hours
```

**Cause:**
- Rounding discrepancies
- Non-billable hours included in timesheet
- Manual adjustments not documented

**Solutions:**

1. **Filter non-billable time:**
```javascript
const billableEntries = timeEntries.filter(entry => entry.billable === true);
const totalBillable = sumHours(billableEntries);
```

2. **Document adjustments:**
```javascript
const rawHours = sumHours(timeEntries);
const roundedHours = Math.round(rawHours * 4) / 4;  // Round to nearest 0.25

if (rawHours !== roundedHours) {
  notes.push(`Hours rounded from ${rawHours} to ${roundedHours} per agreement.`);
}
```

3. **Attach detailed timesheet:**
```javascript
options: {
  include_timesheet: true,  // Shows exact time entries
  show_rounding_note: true
}
```

---

## Issue 10: Recurring Invoice Skips a Month

**Problem:**
Monthly retainer invoice for March was not generated.

**Cause:**
- Scheduler missed execution
- Invoice generation script failed silently
- Incorrect next_invoice_date calculation

**Solutions:**

1. **Use reliable scheduler:**
```javascript
await scheduleRecurringInvoice({
  client_id: "CLIENT-004",
  frequency: "monthly",
  day_of_month: 1,
  failover: true,  // Retry on failure
  notification_email: "billing@yourcompany.com"
});
```

2. **Implement catch-up logic:**
```javascript
const missedInvoices = await detectMissedInvoices();

for (const missed of missedInvoices) {
  console.warn(`Generating missed invoice for ${missed.client} - ${missed.period}`);
  await generateInvoice(missed);
}
```

3. **Monitor invoice generation:**
```javascript
// Daily check for missed invoices
await scheduleEvent({
  name: "Check for missed invoices",
  frequency: "daily",
  time: "09:00",
  action: async () => {
    const missed = await detectMissedInvoices();
    if (missed.length > 0) {
      await sendAlert({
        subject: `${missed.length} missed invoices detected`,
        recipients: ["billing@yourcompany.com"]
      });
    }
  }
});
```

---

## Issue 11: Client Name with Special Characters Breaks File Path

**Problem:**
```
Error: Invalid file path: Invoices/INV-10001-acme-&-co.md
```

**Cause:**
Client name contains special characters (&, /, \, etc.) that are invalid in filenames.

**Solution:**

```javascript
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')  // Replace special chars with hyphens
    .replace(/^-+|-+$/g, '')      // Remove leading/trailing hyphens
    .substring(0, 50);             // Limit length
}

const filename = `INV-${invoice_number}-${slugify(client.name)}.md`;
// Output: INV-10001-acme-co.md
```

---

## Issue 12: Early Payment Discount Applied After Due Date

**Problem:**
Client paid 20 days after invoice date but still got early payment discount.

**Cause:**
Discount logic checked days from current date, not invoice date.

**Solution:**

```javascript
// ❌ DON'T: Use current date
const daysFromNow = getDaysBetween(new Date(), invoice.invoice_date);
const discountApplies = daysFromNow <= DISCOUNT_PERIOD_DAYS;  // Wrong!

// ✅ DO: Use payment date
const daysFromInvoice = getDaysBetween(payment.payment_date, invoice.invoice_date);
const discountApplies = daysFromInvoice <= DISCOUNT_PERIOD_DAYS;

if (discountApplies) {
  const discount = invoice.total * (DISCOUNT_PERCENT / 100);
  const amountDue = invoice.total - discount;
} else {
  const amountDue = invoice.total;
}
```

---

## Issue 13: Missing Payment Instructions for International Clients

**Problem:**
International client can't pay because SWIFT/IBAN information is missing.

**Cause:**
Default payment instructions only include domestic bank transfer info.

**Solution:**

```javascript
// Detect international client
const isInternational = client.country !== "US";

const paymentInfo = {
  ...defaultPaymentInfo,
  ...(isInternational && {
    international_payment: {
      iban: process.env.COMPANY_IBAN,
      swift: process.env.COMPANY_SWIFT,
      bank_name: "Your Bank Name",
      bank_address: "Bank Address",
      intermediary_bank: process.env.INTERMEDIARY_BANK  // For certain countries
    }
  })
};

const invoice = await generateInvoice({
  client: client,
  items: items,
  options: {
    payment_info: paymentInfo,
    include_wire_instructions: isInternational
  }
});
```

---

## Issue 14: Subtotal + Tax ≠ Total (Off by 1 Cent)

**Problem:**
```
Subtotal: $1,234.56
Tax (8%): $98.76
Total: $1,333.33  // Expected: $1,333.32
```

**Cause:**
Rounding applied at wrong stage (per-item vs. subtotal).

**Solution:**

```javascript
// ✅ Correct rounding approach
const lineItems = items.map(item => ({
  ...item,
  amount: roundCurrency(item.quantity * item.rate)  // Round per item
}));

const subtotal = roundCurrency(
  lineItems.reduce((sum, item) => sum + item.amount, 0)
);

const taxAmount = roundCurrency(subtotal * taxRate);  // Round tax

const total = roundCurrency(subtotal + taxAmount);    // Round total

// Verify
const calculatedTotal = subtotal + taxAmount;
if (Math.abs(total - calculatedTotal) > 0.01) {
  console.warn(`Rounding discrepancy: ${total} vs ${calculatedTotal}`);
}
```

---

## Issue 15: Approval Request Never Times Out

**Problem:**
Invoice stuck in "pending_approval" status indefinitely.

**Cause:**
No timeout or escalation logic for approval requests.

**Solution:**

```javascript
const approval = await createApprovalRequest({
  type: "invoice_approval",
  subject: `Approve ${invoice.invoice_number}`,
  approvers: ["finance_manager@company.com"],
  timeout_hours: 48,  // Auto-escalate after 48 hours
  escalation_to: ["cfo@company.com"],
  auto_reject_after_hours: 168  // Auto-reject after 7 days
});

// Set up timeout handler
setTimeout(async () => {
  const status = await getApprovalStatus(approval.id);

  if (status === "pending") {
    console.warn(`Approval timeout for ${invoice.invoice_number}`);

    // Escalate
    await escalateApproval(approval.id, {
      escalation_level: 2,
      notify: ["cfo@company.com"]
    });
  }
}, approval.timeout_hours * 3600 * 1000);
```

---

## Summary of Common Issues

| Issue | Root Cause | Prevention |
|-------|-----------|------------|
| **Invoice number collision** | Concurrent generation | Use locking/atomic increment |
| **Tax calculation mismatch** | Wrong tax rate format | Use decimal (0.08 not 8) |
| **Email validation failure** | Invalid email format | Validate before generation |
| **Expense tax applied** | Default taxes all items | Specify tax_applies_to |
| **Odoo import fails** | Wrong partner_id | Verify Odoo IDs first |
| **Currency rounding errors** | Floating-point precision | Use Decimal library |
| **PDF Unicode issues** | Encoding not supported | Use XeLaTeX with UTF-8 |
| **Late fees too aggressive** | Daily compounding | Use monthly compounding |
| **Timesheet mismatch** | Non-billable included | Filter billable only |
| **Recurring invoice skipped** | Scheduler failure | Implement monitoring |
| **Special chars in filename** | Invalid path characters | Use slugify function |
| **Discount after deadline** | Wrong date comparison | Check payment date |
| **Missing intl payment info** | Domestic-only config | Detect international |
| **Rounding off by 1 cent** | Rounding order wrong | Round at each stage |
| **Approval timeout** | No escalation logic | Set timeout + escalate |

---

## General Best Practices

1. **Validate all inputs** before generating invoices
2. **Use decimal library** for currency calculations
3. **Implement proper error handling** with retries
4. **Monitor invoice generation** for failures
5. **Test edge cases** (international, high-value, recurring)
6. **Log all operations** for audit trail
7. **Document custom logic** for future maintenance
8. **Set up alerts** for anomalies

For more information:
- **SKILL.md** - Complete documentation
- **patterns.md** - Best practices
- **EXAMPLES.md** - Code examples
- **impact-checklist.md** - Deployment checklist
