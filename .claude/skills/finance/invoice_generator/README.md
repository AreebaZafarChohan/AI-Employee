# Invoice Generator Skill

Generate professional invoice metadata with line items, tax calculations, and optional Odoo ERP integration.

## Quick Start

### 1. Configuration

Configure required company information in `.env`:
```bash
# Required
VAULT_PATH="/path/to/vault"
INVOICE_COMPANY_NAME="Your Company Name"
INVOICE_COMPANY_EMAIL="billing@yourcompany.com"

# Optional but recommended
INVOICE_COMPANY_ADDRESS="123 Main St, City, State, ZIP"
INVOICE_COMPANY_PHONE="+1-555-123-4567"
INVOICE_TAX_ID="12-3456789"
INVOICE_DEFAULT_TAX_RATE="0.08"
INVOICE_DEFAULT_PAYMENT_TERMS="Net 30"
```

### 2. Generate Your First Invoice

#### Simple Hourly Invoice
```javascript
const { generateInvoice } = require('./invoice_generator');

const invoice = await generateInvoice({
  client: {
    name: "Acme Corporation",
    email: "billing@acme.com",
    address: "456 Business Ave, New York, NY 10001"
  },
  items: [
    {
      description: "Consulting Services",
      quantity: 40,
      unit: "hours",
      rate: 150.00
    }
  ],
  options: {
    payment_terms: "Net 30",
    tax_rate: 0.08
  }
});

console.log(`Invoice: ${invoice.invoice_number}`);
console.log(`Total: ${invoice.total_formatted}`);
console.log(`File: ${invoice.file_path}`);
```

#### With Expenses
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Tech Startup Inc",
    email: "accounting@techstartup.io"
  },
  items: [
    {
      description: "Software Development",
      quantity: 30,
      unit: "hours",
      rate: 175.00
    }
  ],
  expenses: [
    {
      description: "Flight to client site",
      amount: 485.00,
      date: "2025-01-15",
      category: "travel"
    },
    {
      description: "Hotel (3 nights)",
      amount: 720.00,
      date: "2025-01-15",
      category: "lodging"
    }
  ],
  options: {
    payment_terms: "Net 15"
  }
});
```

### 3. Review Generated Invoice

Invoices are saved to: `$VAULT_PATH/Invoices/`

**File naming pattern:** `INV-{number}-{client-slug}.md`

**Example:** `Invoices/INV-10001-acme-corporation.md`

Each invoice includes:
- Invoice header with number, dates, payment terms
- Company and client information
- Line items table with calculations
- Expense breakdown (if applicable)
- Tax calculations
- Total amount due
- Payment instructions
- Terms and conditions
- Optional timesheet details
- Metadata and audit trail

---

## Features

### 🧾 Invoice Types

**Hourly Billing**
```javascript
items: [{
  description: "Consulting",
  quantity: 40,
  unit: "hours",
  rate: 150.00
}]
```

**Fixed-Price Projects**
```javascript
items: [{
  description: "Website Development",
  quantity: 1,
  unit: "project",
  rate: 5000.00
}]
```

**Monthly Retainer**
```javascript
recurring_config: {
  type: "monthly_retainer",
  billing_period: "2025-01-01 to 2025-01-31"
},
items: [{
  description: "Monthly Retainer - Support",
  quantity: 1,
  unit: "month",
  rate: 3000.00
}]
```

### 💰 Financial Features

**Tax Calculation**
```javascript
options: {
  tax_rate: 0.08,  // 8% sales tax
  currency: "USD"
}
```

**Early Payment Discount**
```javascript
options: {
  early_payment_discount: 2.0,  // 2% discount
  discount_period_days: 10       // if paid within 10 days
}
```

**Late Fees**
```javascript
options: {
  late_fee_percent: 1.5  // 1.5% monthly late fee for overdue
}
```

### 📊 Odoo ERP Integration

Generate Odoo-compatible JSON payload for direct import:

```javascript
options: {
  generate_odoo_payload: true,
  odoo_config: {
    partner_id: 47,      // Client's Odoo partner ID
    account_id: 400001,  // Revenue account
    journal_id: 1        // Sales journal
  }
}
```

**Output:** `Invoices/INV-{number}-odoo-payload.json`

**Import to Odoo:**
```bash
curl -X POST "https://your-company.odoo.com/jsonrpc" \
  -H "Content-Type: application/json" \
  -d @Invoices/INV-10001-odoo-payload.json
```

### 🕒 Timesheet Details

Include detailed time tracking breakdown:

```javascript
options: {
  include_timesheet: true
}
```

**Output includes:**
- Date-by-date breakdown of hours worked
- Task descriptions for each time entry
- Subtotals by role or project phase
- Total hours verification

### 📄 PDF Generation

Each invoice includes PDF generation hints and instructions for converting markdown to professional PDF invoices using tools like:
- Pandoc
- Markdown-pdf
- Weasyprint
- Your company's PDF templating system

---

## Output Format

### Invoice Markdown File

**Location:** `Invoices/INV-{number}-{client-slug}.md`

**YAML Frontmatter:**
```yaml
---
invoice_id: INV-10001
invoice_number: INV-10001
invoice_date: 2025-02-04
due_date: 2025-03-04
status: draft
client_id: CLIENT-001
client_name: Acme Corporation
subtotal: 6000.00
tax_rate: 0.08
tax_amount: 480.00
total: 6480.00
currency: USD
payment_terms: Net 30
---
```

**Markdown Sections:**
1. Invoice header (number, dates)
2. Bill From (your company)
3. Bill To (client)
4. Line Items (table)
5. Expenses (if any)
6. Invoice Summary (subtotal, tax, total)
7. Payment Information (methods, instructions)
8. Notes
9. Terms and Conditions
10. Timesheet Details (if included)
11. Metadata and Audit Trail

### Odoo JSON Payload

**Location:** `Invoices/INV-{number}-odoo-payload.json`

**Format:** Odoo JSON-RPC compatible payload ready for direct import via API

**Example Structure:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "service": "object",
    "method": "execute",
    "args": [
      "database_name",
      "user_id",
      "password",
      "account.move",
      "create",
      {
        "move_type": "out_invoice",
        "partner_id": 47,
        "invoice_date": "2025-02-04",
        "invoice_line_ids": [...]
      }
    ]
  }
}
```

---

## Configuration Options

### Company Information (Required)

```bash
INVOICE_COMPANY_NAME="Your Company Name"
INVOICE_COMPANY_EMAIL="billing@yourcompany.com"
INVOICE_COMPANY_ADDRESS="123 Main St, City, State, ZIP"
INVOICE_COMPANY_PHONE="+1-555-123-4567"
INVOICE_TAX_ID="12-3456789"  # EIN or VAT number
```

### Invoice Defaults

```bash
INVOICE_DEFAULT_CURRENCY="USD"
INVOICE_DEFAULT_PAYMENT_TERMS="Net 30"  # Net 15, Net 30, Net 60, Due on Receipt
INVOICE_DEFAULT_TAX_RATE="0.08"          # 8% (decimal format)
INVOICE_LATE_FEE_PERCENT="1.5"           # 1.5% monthly late fee
INVOICE_EARLY_PAYMENT_DISCOUNT="2.0"     # 2% early payment discount
```

### Invoice Numbering

```bash
INVOICE_NUMBER_PREFIX="INV-"      # Default: "INV-"
INVOICE_NUMBER_START="10001"      # Starting number
INVOICE_DATE_FORMAT="YYYY-MM-DD"  # Date format
```

### Odoo Integration (Optional)

```bash
ODOO_API_URL="https://your-company.odoo.com"
ODOO_DATABASE="production"
ODOO_ACCOUNT_ID="400001"  # Default revenue account
ODOO_JOURNAL_ID="1"       # Default sales journal
```

### Output Preferences

```bash
INVOICE_OUTPUT_FORMAT="markdown"          # markdown | json | html
INVOICE_GENERATE_PDF_HINTS="true"         # Include PDF generation instructions
INVOICE_ATTACH_TIMESHEETS="true"          # Include timesheet breakdown
INVOICE_INCLUDE_PAYMENT_LINK="false"      # Include online payment link
```

---

## Integration Examples

### With Email Drafter

Send invoice email automatically:
```javascript
const invoice = await generateInvoice(invoiceData);

await draftEmail({
  intent: "invoice",
  recipient: { email: invoice.client.email },
  context: {
    invoice_number: invoice.invoice_number,
    invoice_path: invoice.file_path,
    total: invoice.total_formatted,
    due_date: invoice.due_date
  }
});
```

### With Time Event Scheduler

Schedule recurring invoice generation:
```javascript
await scheduleEvent({
  name: "Monthly Retainer Invoice - Acme Corp",
  frequency: "monthly",
  day_of_month: 1,
  action: {
    skill: "invoice_generator",
    params: {
      client_id: "CLIENT-001",
      recurring_config: { type: "monthly_retainer" }
    }
  }
});
```

### With Approval Request Creator

Require approval for high-value invoices:
```javascript
const invoice = await generateInvoice(invoiceData);

if (invoice.total > 10000) {
  await createApprovalRequest({
    type: "invoice_approval",
    subject: `Approve invoice ${invoice.invoice_number}`,
    details: {
      client: invoice.client.name,
      amount: invoice.total_formatted,
      invoice_path: invoice.file_path
    }
  });
}
```

### With Dashboard Writer

Include in financial dashboard:
```javascript
const outstandingInvoices = getOutstandingInvoices();

await updateDashboard({
  section: "accounts_receivable",
  data: {
    outstanding_count: outstandingInvoices.length,
    total_outstanding: sumInvoices(outstandingInvoices),
    overdue_count: outstandingInvoices.filter(inv => inv.status === 'overdue').length
  }
});
```

---

## Common Use Cases

### Consulting Services
- Track hours by role/rate
- Include project phases
- Attach detailed timesheets
- Add travel expenses

### Freelance Work
- Multiple projects per invoice
- Mixed hourly and fixed-price items
- Expense reimbursement
- Early payment incentives

### Agency Billing
- Multiple team members
- Different rates per skill level
- Subcontractor expenses
- Monthly retainer + overages

### SaaS Subscriptions
- Recurring monthly billing
- Usage-based charges
- Add-on services
- Annual prepayment discounts

---

## Troubleshooting

### Invoice Number Already Exists

**Problem:** Duplicate invoice number error

**Solution:** System auto-increments to next available number. Ensure `INVOICE_NUMBER_START` is set correctly.

### Tax Calculation Incorrect

**Problem:** Tax amount doesn't match expected

**Solution:** Verify `tax_rate` is in decimal format (0.08 for 8%, not 8). Check which line items are taxable.

### Odoo Import Fails

**Problem:** Odoo JSON payload import error

**Solution:**
1. Verify `partner_id`, `account_id`, and `journal_id` are correct
2. Check Odoo API credentials
3. Ensure Odoo API endpoint is accessible
4. Review Odoo error logs for specific field issues

### PDF Generation

**Problem:** Need to convert markdown to PDF

**Solutions:**
- **Pandoc:** `pandoc invoice.md -o invoice.pdf --pdf-engine=xelatex`
- **Weasyprint:** `weasyprint invoice.html invoice.pdf` (convert to HTML first)
- **Node.js:** Use `markdown-pdf` package
- **Custom:** Use your company's invoice template system

---

## Performance

**Generation Speed:**
- Simple invoice (1-5 line items): ~50-100ms
- Complex invoice (10+ items + expenses): ~200-500ms
- With timesheet details: +100-200ms
- With Odoo payload: +50ms

**Throughput:**
- Can generate 20-50 invoices per second (if batching)
- Vault I/O is the primary bottleneck
- No external API calls required (except optional Odoo)

---

## Security Best Practices

### Data Protection
- ✅ Store vault on encrypted filesystem
- ✅ Restrict invoice folder permissions (user-only)
- ✅ Enable audit logging
- ✅ Never log client financial details
- ✅ Encrypt backups

### Compliance
- ✅ Retain invoices for required period (default: 7 years)
- ✅ Include all required tax information
- ✅ Maintain audit trail of modifications
- ✅ Handle client PII per GDPR/CCPA requirements

### Access Control
- ✅ Limit write access to Invoices/ folder
- ✅ Implement approval workflow for high-value invoices
- ✅ Review invoice history regularly
- ✅ Monitor for unusual invoice activity

---

## FAQ

**Q: Can I customize the invoice template?**
A: Yes, edit the template in `assets/invoice.template.md` to match your branding.

**Q: How do I handle multi-currency invoices?**
A: Set `currency` in options. Exchange rates must be handled separately.

**Q: Can I add custom fields?**
A: Yes, add custom fields to the frontmatter and include them in the markdown body.

**Q: How do I track invoice payments?**
A: Update the invoice status field (draft → sent → paid) and set `paid_at` timestamp. Use the transaction_classifier skill to match incoming payments.

**Q: Can I generate invoices in other languages?**
A: Yes, configure `INVOICE_LANGUAGE` and update template strings accordingly.

**Q: How do I handle partial payments?**
A: Set `amount_paid` and calculate `balance_due` in the frontmatter.

---

## Support

- **Documentation**: See SKILL.md for detailed usage
- **Examples**: See EXAMPLES.md for code samples
- **Troubleshooting**: See references/gotchas.md
- **Patterns**: See references/patterns.md

---

## Version

**Current Version:** v1.0.0
**Last Updated:** 2025-02-04
**Skill Type:** Finance/Invoice Generation
**Status:** Production Ready
