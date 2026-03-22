# Accounting Integration

This folder contains all Odoo accounting integration files and reports.

## Folder Structure

```
Accounting/
├── Invoices/
│   ├── unpaid/          # Unpaid invoices tracking
│   ├── paid/            # Paid invoices archive
│   └── overdue/         # Overdue invoices alerts
├── Payments/
│   ├── received/        # Payments received
│   ├── sent/            # Payments made
│   └── pending/         # Pending payments
├── Customers/
│   ├── balances/        # Customer balance reports
│   └── statements/      # Customer statements
├── Vendors/
│   ├── balances/        # Vendor balance reports
│   └── statements/      # Vendor statements
├── Journals/
│   └── entries/         # Journal entries
└── Reports/
    ├── profit-loss/     # P&L reports
    ├── balance-sheet/   # Balance sheet reports
    └── cash-flow/       # Cash flow reports
```

## Integration with Odoo

The Gold Tier system integrates with Odoo Community Edition via JSON-RPC API.

### Configuration

Set the following environment variables in `.env`:

```bash
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_api_key
```

### Automated Workflows

1. **Invoice Processing**: Unpaid invoices are tracked and payment tasks are created
2. **Overdue Alerts**: Invoices overdue by >7 days trigger alerts
3. **Payment Tracking**: Payments received are logged and reconciled
4. **Financial Reports**: Weekly and monthly reports generated automatically

## Related Files

- `odoo_watcher.py` - Monitors Odoo for accounting events
- `mcp/odoo-server/` - MCP server for Odoo integration
- `.claude/skills/gold/odoo_accounting_integration/` - Accounting skills

## File Naming Convention

- Invoices: `INV-{number}-{date}.md`
- Payments: `PAY-{number}-{date}.md`
- Reports: `{type}-{period}.md`

Example:
- `INV-2026-001-2026-03-06.md`
- `PAY-2026-045-2026-03-06.md`
- `profit-loss-2026-03.md`
