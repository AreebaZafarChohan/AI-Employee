/**
 * Get Financial Summary Tool
 * 
 * Retrieves profit & loss summary from Odoo
 */

import { z } from 'zod';

const inputSchema = z.object({
  period: z.string().default('monthly').describe('Period: daily, weekly, monthly, yearly'),
  comparison: z.boolean().default(true).describe('Include prior period comparison')
});

export async function getFinancialSummary(params, odooClient) {
  const validated = inputSchema.parse(params);

  try {
    // Calculate date ranges
    const today = new Date();
    let startDate, priorStartDate, priorEndDate;

    switch (validated.period) {
      case 'daily':
        startDate = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        break;
      case 'weekly':
        startDate = new Date(today);
        startDate.setDate(today.getDate() - 7);
        break;
      case 'monthly':
      default:
        startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        break;
      case 'yearly':
        startDate = new Date(today.getFullYear(), 0, 1);
        break;
    }

    const startDateStr = startDate.toISOString().split('T')[0];

    // Get income accounts
    const incomeAccounts = await odooClient.searchRead(
      'account.account',
      [['account_type', '=', 'income']],
      ['id', 'code', 'name']
    );

    // Get expense accounts
    const expenseAccounts = await odooClient.searchRead(
      'account.account',
      [['account_type', '=', 'expense']],
      ['id', 'code', 'name']
    );

    // Get account moves for income
    const incomeMoves = await odooClient.searchRead(
      'account.move.line',
      [
        ['account_id', 'in', incomeAccounts.map(a => a.id)],
        ['date', '>=', startDateStr],
        ['parent_state', '=', 'posted']
      ],
      ['balance', 'credit', 'debit']
    );

    // Get account moves for expenses
    const expenseMoves = await odooClient.searchRead(
      'account.move.line',
      [
        ['account_id', 'in', expenseAccounts.map(a => a.id)],
        ['date', '>=', startDateStr],
        ['parent_state', '=', 'posted']
      ],
      ['balance', 'credit', 'debit']
    );

    // Calculate totals
    const totalIncome = incomeMoves.reduce((sum, line) => sum + (line.credit || 0), 0);
    const totalExpenses = expenseMoves.reduce((sum, line) => sum + (line.debit || 0), 0);
    const netIncome = totalIncome - totalExpenses;

    return {
      success: true,
      period: validated.period,
      start_date: startDateStr,
      summary: {
        total_income: totalIncome,
        total_expenses: totalExpenses,
        net_income: netIncome,
        profit_margin: totalIncome > 0 ? ((netIncome / totalIncome) * 100).toFixed(2) : 0
      },
      line_counts: {
        income_transactions: incomeMoves.length,
        expense_transactions: expenseMoves.length
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      summary: null
    };
  }
}
