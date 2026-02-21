# Invoice Generator - Examples

Practical examples demonstrating various invoice generation scenarios.

---

## Example 1: Simple Hourly Consulting Invoice

**Scenario:** Freelance consultant billing for 40 hours of work

**Input:**
```javascript
const { generateInvoice } = require('./invoice_generator');

const invoice = await generateInvoice({
  client: {
    name: "Acme Corporation",
    email: "billing@acme.com",
    address: "456 Business Ave, Suite 200, New York, NY 10001",
    contact_person: "Jane Smith",
    client_id: "CLIENT-001"
  },
  items: [
    {
      description: "Software Development Consulting",
      quantity: 40,
      unit: "hours",
      rate: 150.00,
      date_range: "2025-01-01 to 2025-01-15"
    }
  ],
  options: {
    payment_terms: "Net 30",
    due_date: "2025-03-04",
    tax_rate: 0.08,
    currency: "USD"
  }
});

console.log(`Generated: ${invoice.invoice_number}`);
console.log(`Total: ${invoice.total_formatted}`);
console.log(`Path: ${invoice.file_path}`);
```

**Output:**
```
Generated: INV-10001
Total: $6,480.00
Path: Invoices/INV-10001-acme-corporation.md
```

**Invoice Summary:**
- Subtotal: $6,000.00
- Tax (8%): $480.00
- **Total: $6,480.00**

---

## Example 2: Multi-Rate Project Invoice

**Scenario:** Agency billing with different rates for different team members

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Tech Startup Inc",
    email: "accounting@techstartup.io",
    address: "789 Innovation Drive, San Francisco, CA 94102",
    client_id: "CLIENT-002"
  },
  items: [
    {
      description: "Senior Developer - Backend Architecture",
      quantity: 60,
      unit: "hours",
      rate: 200.00,
      team_member: "Alex Johnson",
      date_range: "2025-01-01 to 2025-01-31"
    },
    {
      description: "Mid-Level Developer - Frontend Development",
      quantity: 80,
      unit: "hours",
      rate: 150.00,
      team_member: "Sarah Lee",
      date_range: "2025-01-01 to 2025-01-31"
    },
    {
      description: "Junior Developer - Testing and QA",
      quantity: 40,
      unit: "hours",
      rate: 100.00,
      team_member: "Mike Chen",
      date_range: "2025-01-01 to 2025-01-31"
    },
    {
      description: "Project Manager - Coordination",
      quantity: 20,
      unit: "hours",
      rate: 175.00,
      team_member: "Emily Davis",
      date_range: "2025-01-01 to 2025-01-31"
    }
  ],
  options: {
    payment_terms: "Net 15",
    due_date: "2025-02-19",
    tax_rate: 0.0725,  // 7.25% CA sales tax
    currency: "USD",
    include_timesheet: true
  }
});
```

**Invoice Summary:**
- Senior Dev (60h @ $200): $12,000.00
- Mid-Level Dev (80h @ $150): $12,000.00
- Junior Dev (40h @ $100): $4,000.00
- PM (20h @ $175): $3,500.00
- **Subtotal: $31,500.00**
- Tax (7.25%): $2,283.75
- **Total: $33,783.75**

---

## Example 3: Invoice with Reimbursable Expenses

**Scenario:** Consultant billing for services plus travel expenses

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Enterprise Solutions Ltd",
    email: "ap@enterprise-solutions.com",
    address: "1000 Corporate Plaza, Chicago, IL 60601",
    client_id: "CLIENT-003"
  },
  items: [
    {
      description: "On-Site Consulting - System Architecture Review",
      quantity: 24,
      unit: "hours",
      rate: 250.00,
      date_range: "2025-01-15 to 2025-01-17"
    }
  ],
  expenses: [
    {
      description: "Round-trip Flight: SFO to ORD",
      amount: 485.00,
      date: "2025-01-15",
      category: "travel",
      receipt_path: "receipts/flight-2025-01-15.pdf",
      receipt_number: "REC-001"
    },
    {
      description: "Hotel Accommodation (2 nights)",
      amount: 480.00,
      date: "2025-01-15",
      category: "lodging",
      receipt_path: "receipts/hotel-2025-01-15.pdf",
      receipt_number: "REC-002"
    },
    {
      description: "Ground Transportation (Uber/Taxi)",
      amount: 95.00,
      date: "2025-01-15",
      category: "transportation",
      receipt_path: "receipts/transportation-2025-01-15.pdf",
      receipt_number: "REC-003"
    },
    {
      description: "Client Dinner Meeting",
      amount: 180.00,
      date: "2025-01-16",
      category: "meals",
      receipt_path: "receipts/meals-2025-01-16.pdf",
      receipt_number: "REC-004"
    }
  ],
  options: {
    payment_terms: "Net 30",
    tax_rate: 0.10,  // Only services taxed, not expenses
    tax_applies_to: ["services"],  // Expenses are not taxed
    currency: "USD"
  }
});
```

**Invoice Summary:**
- Consulting Services (24h @ $250): $6,000.00
- Tax on Services (10%): $600.00
- **Services Total: $6,600.00**
- Flight: $485.00
- Hotel: $480.00
- Transportation: $95.00
- Meals: $180.00
- **Expenses Total: $1,240.00**
- **Invoice Total: $7,840.00**

---

## Example 4: Monthly Retainer with Overage

**Scenario:** Monthly retainer agreement with additional hours beyond retainer

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Marketing Agency Pro",
    email: "finance@marketingpro.com",
    address: "500 Madison Avenue, New York, NY 10022",
    client_id: "CLIENT-004"
  },
  recurring_config: {
    type: "monthly_retainer",
    billing_period: "2025-01-01 to 2025-01-31",
    retainer_hours: 40,
    rollover_hours: 0  // No rollover from previous month
  },
  items: [
    {
      description: "Monthly Retainer - Technical Support and Maintenance (40 hours included)",
      quantity: 1,
      unit: "month",
      rate: 5000.00,
      type: "retainer"
    },
    {
      description: "Additional Consulting Hours (beyond retainer)",
      quantity: 12,
      unit: "hours",
      rate: 175.00,
      type: "overage",
      note: "Feature development and code review"
    }
  ],
  options: {
    payment_terms: "Due on Receipt",
    tax_rate: 0.0,  // Services not taxed in this jurisdiction
    currency: "USD",
    early_payment_discount: 2.0,  // 2% discount if paid within 5 days
    discount_period_days: 5
  },
  metadata: {
    recurring_invoice_id: "RECURRING-004",
    next_invoice_date: "2025-03-01"
  }
});
```

**Invoice Summary:**
- Monthly Retainer: $5,000.00
- Additional Hours (12h @ $175): $2,100.00
- **Subtotal: $7,100.00**
- **Total: $7,100.00**
- **Early Payment Discount (2%):** -$142.00
- **Total if paid by 2025-02-09: $6,958.00**

---

## Example 5: Fixed-Price Project Invoice

**Scenario:** Web development project with milestone-based billing

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Boutique Retail Co",
    email: "owner@boutiqueretail.com",
    address: "250 Fashion Street, Los Angeles, CA 90014",
    client_id: "CLIENT-005"
  },
  project: {
    name: "E-commerce Website Development",
    project_id: "PROJ-2024-001",
    milestone: "Milestone 2: Frontend Development Complete"
  },
  items: [
    {
      description: "E-commerce Website Development - Milestone 2",
      quantity: 1,
      unit: "milestone",
      rate: 15000.00,
      type: "project",
      details: [
        "Responsive product catalog pages",
        "Shopping cart functionality",
        "User account management",
        "Payment gateway integration (Stripe)",
        "Mobile-optimized checkout flow"
      ]
    }
  ],
  options: {
    payment_terms: "Net 15",
    tax_rate: 0.095,  // 9.5% CA sales tax
    currency: "USD"
  },
  notes: [
    "Milestone 2 of 4 completed as of 2025-01-31.",
    "Project on schedule for final delivery by 2025-03-31.",
    "Remaining milestones: Backend API (Milestone 3), Testing & Launch (Milestone 4)."
  ]
});
```

**Invoice Summary:**
- Milestone 2 Payment: $15,000.00
- Tax (9.5%): $1,425.00
- **Total: $16,425.00**

---

## Example 6: Multi-Currency Invoice (International Client)

**Scenario:** Billing an international client in their local currency

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "European Tech GmbH",
    email: "buchhaltung@europeantech.de",
    address: "Hauptstraße 123, 10115 Berlin, Germany",
    client_id: "CLIENT-006",
    vat_number: "DE123456789"
  },
  items: [
    {
      description: "Software Development Services",
      quantity: 80,
      unit: "hours",
      rate: 140.00,  // EUR rate
      date_range: "2025-01-01 to 2025-01-31"
    },
    {
      description: "Technical Documentation",
      quantity: 1,
      unit: "project",
      rate: 2500.00
    }
  ],
  options: {
    payment_terms: "Net 30",
    tax_rate: 0.19,  // 19% German VAT
    currency: "EUR",
    include_reverse_charge: true,  // EU B2B reverse charge
    exchange_rate_info: {
      reference_currency: "USD",
      rate: 1.08,  // 1 EUR = 1.08 USD
      date: "2025-02-04"
    }
  }
});
```

**Invoice Summary:**
- Software Development (80h @ €140): €11,200.00
- Technical Documentation: €2,500.00
- **Subtotal: €13,700.00**
- VAT (19%) - *Reverse Charge*: €0.00
- **Total: €13,700.00**
- *(Approx. $14,796.00 USD at 1.08 rate)*

**Note:** VAT reverse charge applies (EU B2B transaction)

---

## Example 7: Invoice with Early Payment Discount and Late Fees

**Scenario:** Invoice with payment incentives and penalties

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Manufacturing Corp",
    email: "payables@manufacturingcorp.com",
    address: "1500 Industrial Parkway, Detroit, MI 48201",
    client_id: "CLIENT-007"
  },
  items: [
    {
      description: "Custom Software Integration",
      quantity: 1,
      unit: "project",
      rate: 25000.00
    }
  ],
  options: {
    payment_terms: "Net 30",
    due_date: "2025-03-04",
    tax_rate: 0.06,
    currency: "USD",
    early_payment_discount: 3.0,  // 3% discount
    discount_period_days: 10,      // if paid within 10 days
    late_fee_percent: 1.5,         // 1.5% per month late fee
    late_fee_grace_days: 5         // Grace period after due date
  }
});
```

**Invoice Summary:**
- Project Total: $25,000.00
- Tax (6%): $1,500.00
- **Total: $26,500.00**

**Payment Options:**
- **Pay by 2025-02-14 (10 days):** $25,705.00 (3% discount = -$795)
- **Pay by 2025-03-04 (due date):** $26,500.00
- **Overdue after 2025-03-09:** $26,500.00 + 1.5% per month

---

## Example 8: Subscription/SaaS Recurring Invoice

**Scenario:** Monthly SaaS subscription with usage-based charges

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Startup Ventures LLC",
    email: "billing@startupventures.com",
    address: "100 Silicon Valley Blvd, Palo Alto, CA 94301",
    client_id: "CLIENT-008"
  },
  subscription: {
    plan: "Business Plan",
    billing_cycle: "monthly",
    period: "2025-02-01 to 2025-02-28"
  },
  items: [
    {
      description: "Business Plan Subscription (10 users)",
      quantity: 1,
      unit: "month",
      rate: 499.00,
      type: "subscription"
    },
    {
      description: "Additional User Licenses (5 users)",
      quantity: 5,
      unit: "users",
      rate: 45.00,
      type: "addon"
    },
    {
      description: "API Usage Overage (50,000 calls beyond plan)",
      quantity: 50000,
      unit: "API calls",
      rate: 0.002,  // $0.002 per API call
      type: "usage"
    },
    {
      description: "Premium Support Add-on",
      quantity: 1,
      unit: "month",
      rate: 199.00,
      type: "addon"
    }
  ],
  options: {
    payment_terms: "Due on Receipt",
    auto_charge: true,  // Automatically charge payment method on file
    tax_rate: 0.0,  // SaaS often not taxed
    currency: "USD"
  },
  metadata: {
    subscription_id: "SUB-008",
    next_billing_date: "2025-03-01"
  }
});
```

**Invoice Summary:**
- Business Plan: $499.00
- Additional Users (5 @ $45): $225.00
- API Overage (50k @ $0.002): $100.00
- Premium Support: $199.00
- **Total: $1,023.00**

**Auto-charge on 2025-02-01**

---

## Example 9: Invoice with Odoo ERP Integration

**Scenario:** Generate invoice and Odoo JSON payload for automated import

**Input:**
```javascript
const invoice = await generateInvoice({
  client: {
    name: "Global Enterprises Inc",
    email: "ap@globalenterprises.com",
    address: "2000 Commerce Drive, Dallas, TX 75201",
    client_id: "CLIENT-009"
  },
  items: [
    {
      description: "Cloud Migration Consulting",
      quantity: 120,
      unit: "hours",
      rate: 225.00
    },
    {
      description: "Training and Documentation",
      quantity: 1,
      unit: "project",
      rate: 5000.00
    }
  ],
  options: {
    payment_terms: "Net 45",
    tax_rate: 0.0825,
    currency: "USD",
    generate_odoo_payload: true,
    odoo_config: {
      partner_id: 123,        // Client's Odoo partner ID
      account_id: 400001,     // Revenue account in Odoo
      journal_id: 1,          // Sales journal
      payment_term_id: 3,     // Net 45 payment term
      analytic_account_id: 15 // Project tracking
    }
  }
});

console.log(`Invoice: ${invoice.invoice_number}`);
console.log(`Odoo payload: ${invoice.odoo_payload_path}`);
```

**Output Files:**
1. `Invoices/INV-10009-global-enterprises-inc.md` (markdown invoice)
2. `Invoices/INV-10009-odoo-payload.json` (Odoo import file)

**Odoo Import Command:**
```bash
# Import to Odoo via API
curl -X POST "https://your-company.odoo.com/jsonrpc" \
  -H "Content-Type: application/json" \
  -d @Invoices/INV-10009-odoo-payload.json

# Or import via Odoo UI:
# 1. Login to Odoo
# 2. Go to Accounting → Customers → Invoices
# 3. Click Import
# 4. Upload INV-10009-odoo-payload.json
```

**Invoice Summary:**
- Cloud Migration (120h @ $225): $27,000.00
- Training: $5,000.00
- **Subtotal: $32,000.00**
- Tax (8.25%): $2,640.00
- **Total: $34,640.00**

---

## Example 10: Credit Note / Refund Invoice

**Scenario:** Issuing a credit note to correct a previous invoice

**Input:**
```javascript
const creditNote = await generateInvoice({
  client: {
    name: "Acme Corporation",
    email: "billing@acme.com",
    client_id: "CLIENT-001"
  },
  credit_note: {
    original_invoice: "INV-10001",
    reason: "Partial refund for uncompleted work"
  },
  items: [
    {
      description: "Refund: Uncompleted Consulting Hours",
      quantity: -10,  // Negative quantity for credit
      unit: "hours",
      rate: 150.00
    }
  ],
  options: {
    invoice_type: "credit_note",
    payment_terms: "Immediate Credit",
    tax_rate: 0.08,
    currency: "USD"
  }
});
```

**Credit Note Summary:**
- Refund Amount: -$1,500.00
- Tax Credit (8%): -$120.00
- **Total Credit: -$1,620.00**

**Original Invoice (INV-10001) Balance:**
- Original Total: $6,480.00
- Credit Applied: -$1,620.00
- **New Balance: $4,860.00**

---

## Integration Example: Complete Billing Workflow

**Scenario:** Full workflow from time tracking to invoice generation to email

```javascript
// Step 1: Fetch time entries from tracking system
const timeEntries = await fetchTimeEntries({
  client_id: "CLIENT-001",
  period: "2025-01-01 to 2025-01-31",
  billable_only: true
});

// Step 2: Group and summarize time entries
const lineItems = groupTimeEntriesByRole(timeEntries);

// Step 3: Generate invoice
const invoice = await generateInvoice({
  client: await fetchClientInfo("CLIENT-001"),
  items: lineItems,
  options: {
    payment_terms: "Net 30",
    tax_rate: 0.08,
    include_timesheet: true
  }
});

// Step 4: Require approval for high-value invoices
if (invoice.total > 10000) {
  await createApprovalRequest({
    type: "invoice_approval",
    subject: `Approve ${invoice.invoice_number} - ${invoice.client.name}`,
    invoice_path: invoice.file_path,
    amount: invoice.total_formatted
  });

  // Wait for approval...
  await waitForApproval(invoice.invoice_number);
}

// Step 5: Update invoice status to "sent"
await updateInvoiceStatus(invoice.invoice_number, "sent");

// Step 6: Send invoice email
await draftEmail({
  intent: "invoice",
  recipient: { email: invoice.client.email },
  attachments: [invoice.file_path],
  context: {
    invoice_number: invoice.invoice_number,
    total: invoice.total_formatted,
    due_date: invoice.due_date
  }
});

// Step 7: Schedule payment reminder
await scheduleEvent({
  name: `Payment Reminder - ${invoice.invoice_number}`,
  date: invoice.due_date,
  action: {
    skill: "email_drafter",
    params: {
      intent: "payment_reminder",
      invoice_number: invoice.invoice_number
    }
  }
});

// Step 8: Add to dashboard
await updateDashboard({
  section: "accounts_receivable",
  data: {
    new_invoice: {
      number: invoice.invoice_number,
      client: invoice.client.name,
      amount: invoice.total,
      due_date: invoice.due_date
    }
  }
});

console.log(`✅ Invoice ${invoice.invoice_number} generated and sent!`);
console.log(`📧 Email sent to ${invoice.client.email}`);
console.log(`📅 Payment reminder scheduled for ${invoice.due_date}`);
```

---

## Summary

These examples demonstrate:
- ✅ Hourly billing with time tracking
- ✅ Multi-rate project invoices
- ✅ Expense reimbursement
- ✅ Monthly retainers with overage
- ✅ Fixed-price project milestones
- ✅ Multi-currency invoicing
- ✅ Early payment discounts
- ✅ Late fee calculations
- ✅ SaaS subscription billing
- ✅ Odoo ERP integration
- ✅ Credit notes and refunds
- ✅ Complete billing workflow automation

For more details, see:
- **SKILL.md** - Complete skill documentation
- **README.md** - Quick start guide
- **references/patterns.md** - Best practices and patterns
- **references/gotchas.md** - Common issues and solutions
