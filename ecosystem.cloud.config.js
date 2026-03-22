/**
 * PM2 Ecosystem Configuration — PLATINUM CLOUD
 * Run on: Cloud VM (DigitalOcean/AWS/Hetzner)
 *
 * Responsibilities:
 * - 24/7 Email Triage
 * - Social Media Drafting
 * - Marketing Automation
 * - Business Analytics
 * - Task Planning (Drafts only)
 */

const VAULT_PATH = './AI-Employee-Vault';

module.exports = {
  apps: [
    {
      name: 'platinum-cloud-triage',
      script: 'ralph_loop.py',
      interpreter: 'python3',
      args: '--agent gemini --max-iters 50 --role cloud --triage-only',
      restart_delay: 15000,
      env: {
        AGENT_ROLE: 'cloud',
        VAULT_PATH: VAULT_PATH,
        LOG_LEVEL: 'INFO',
        PLATINUM_TIER: 'true'
      }
    },
    {
      name: 'gmail-watcher-cloud',
      script: 'gmail_actions.py', // Assuming this handles watching in cloud mode
      interpreter: 'python3',
      args: '--watch --cloud',
      env: {
        VAULT_PATH: VAULT_PATH,
        POLL_INTERVAL: '60'
      }
    },
    {
      name: 'social-post-drafter',
      script: 'src/agent/social_media_drafter.py',
      interpreter: 'python3',
      args: '--draft-mode',
      env: {
        VAULT_PATH: VAULT_PATH
      }
    },
    {
      name: 'cloud-health-monitor',
      script: 'src/health/pulse.py',
      interpreter: 'python3',
      args: '--role cloud',
      env: {
        VAULT_PATH: VAULT_PATH
      }
    }
  ]
};
