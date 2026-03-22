/**
 * PM2 Ecosystem Configuration — PLATINUM LOCAL
 * Run on: Your Primary Laptop
 *
 * Responsibilities:
 * - Final Approvals (Human-in-the-loop)
 * - WhatsApp Session Management (Local Browser)
 * - Financial Payments (Secure Environment)
 * - Final Sending (Verified Outbox)
 * - Local Hardware Access
 */

const VAULT_PATH = './AI-Employee-Vault';

module.exports = {
  apps: [
    {
      name: 'platinum-local-executive',
      script: 'ralph_loop.py',
      interpreter: 'python3',
      args: '--agent claude --role local --approval-mode',
      restart_delay: 10000,
      env: {
        AGENT_ROLE: 'local',
        VAULT_PATH: VAULT_PATH,
        LOG_LEVEL: 'INFO',
        PLATINUM_TIER: 'true'
      }
    },
    {
      name: 'whatsapp-watcher-local',
      script: 'whatsapp_sender.py', // Assuming this handles watching locally
      interpreter: 'python3',
      args: '--watch --local-session',
      env: {
        VAULT_PATH: VAULT_PATH
      }
    },
    {
      name: 'odoo-finalizer',
      script: 'test_odoo_connection.py', // Placeholder for final Odoo actions
      interpreter: 'python3',
      args: '--execute-approved',
      env: {
        VAULT_PATH: VAULT_PATH
      }
    },
    {
      name: 'local-health-beacon',
      script: 'src/health/pulse.py',
      interpreter: 'python3',
      args: '--role local',
      env: {
        VAULT_PATH: VAULT_PATH
      }
    }
  ]
};
