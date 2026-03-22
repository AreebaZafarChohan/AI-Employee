/**
 * PM2 Ecosystem Configuration — Production Deployment
 *
 * Manages Backend, Frontend, Watchers, and AI Reasoning Agent.
 */

module.exports = {
  apps: [
    // 1. FASTAPI BACKEND
    {
      name: 'ai-backend',
      script: 'main.py',
      cwd: './backend',
      interpreter: 'python3',
      // Run with uvicorn and multiple workers for production
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4',
      autorestart: True,
      watch: false,
      max_memory_restart: '500M',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: './logs/backend-error.log',
      out_file: './logs/backend-out.log',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '.'
      }
    },

    // 2. NEXT.JS FRONTEND
    {
      name: 'ai-frontend',
      script: 'npm',
      args: 'start',
      cwd: './frontend',
      autorestart: True,
      watch: false,
      max_memory_restart: '1G',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: './logs/frontend-error.log',
      out_file: './logs/frontend-out.log',
      env: {
        NODE_ENV: 'production',
        PORT: 3000,
        NEXT_PUBLIC_API_URL: 'http://localhost:8000/api/v1'
      }
    },

    // 3. WATCHER SYSTEM
    {
      name: 'ai-watchers',
      script: 'run_all_watchers.py',
      cwd: '.',
      interpreter: 'python3',
      autorestart: True,
      watch: false,
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: './logs/watchers-error.log',
      out_file: './logs/watchers-out.log',
      env: {
        VAULT_PATH: './AI-Employee-Vault'
      }
    },

    // 4. AI AGENT REASONING LOOP (RALPH)
    {
      name: 'ai-agent',
      script: 'ralph_loop.py',
      cwd: '.',
      interpreter: 'python3',
      autorestart: True,
      watch: false,
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      error_file: './logs/agent-error.log',
      out_file: './logs/agent-out.log',
      env: {
        VAULT_PATH: './AI-Employee-Vault'
      }
    }
  ]
};
