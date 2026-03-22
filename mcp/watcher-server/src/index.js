#!/usr/bin/env node
/**
 * MCP Watcher Server
 * Provides tools to manage Python watchers via MCP protocol
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { config } from 'dotenv';
import * as fs from 'fs';
import * as path from 'path';
import { exec, spawn } from 'child_process';
import { fileURLToPath } from 'url';

// Load environment variables
config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Constants
const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');
const VAULT_PATH = process.env.VAULT_PATH || path.join(ROOT_PATH, 'AI-Employee-Vault');
const LOGS_DIR = path.join(VAULT_PATH, 'Logs');

const WATCHER_DEFS = [
  { name: 'Gmail Watcher', id: 'gmail', script: 'src/watcher/gmail_watcher.py' },
  { name: 'LinkedIn Watcher', id: 'linkedin', script: 'src/watcher/linkedin_watcher.py' },
  { name: 'WhatsApp Watcher', id: 'whatsapp', script: 'src/watcher/whatsapp_watcher.py' },
  { name: 'Odoo Watcher', id: 'odoo', script: 'src/watcher/odoo_watcher.py' },
  { name: 'Social Watcher', id: 'social', script: 'src/watcher/social_watcher.py' },
];

// Helper functions (same logic as in WatcherController.ts)
function readLogLines(logFile, maxLines = 50) {
  try {
    if (!fs.existsSync(logFile)) return [];
    const content = fs.readFileSync(logFile, 'utf-8');
    return content.split('\n').filter(l => l.trim()).slice(-maxLines);
  } catch { return []; }
}

function countTodayLogs(watcherId) {
  const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
  const logFiles = [
    path.join(LOGS_DIR, `master-${today}.log`),
    path.join(LOGS_DIR, `agent-${today}.log`),
    path.join(LOGS_DIR, `${watcherId}-${today}.log`),
  ];

  let count = 0;
  let lastLine = '';
  let lastTime = '';

  for (const lf of logFiles) {
    const lines = readLogLines(lf, 200);
    for (const line of lines) {
      const lower = line.toLowerCase();
      if (lower.includes(watcherId) || lower.includes('all') || lower.includes('master')) {
        count++;
        lastLine = line;
        const timeMatch = line.match(/\[(\d{2}:\d{2}:\d{2})\]/);
        if (timeMatch) lastTime = `${new Date().toISOString().slice(0, 10)}T${timeMatch[1]}`;
      }
    }
  }

  return { count, lastLine, lastTime };
}

// Create MCP server
const server = new McpServer({
  name: 'watcher-server',
  version: '1.0.0',
  description: 'MCP server for managing AI Employee Python watchers'
});

// Register Tool: list_watchers
server.tool(
  'list_watchers',
  'List all Python watchers and their status',
  {},
  async () => {
    const watchers = WATCHER_DEFS.map(def => {
      const scriptPath = path.join(ROOT_PATH, def.script);
      const exists = fs.existsSync(scriptPath);
      const logInfo = countTodayLogs(def.id);

      return {
        name: def.name,
        id: def.id,
        script: def.script,
        status: exists ? 'stopped' : 'error', // Note: simplistic status, would need PID check for 'running'
        logsToday: logInfo.count,
        itemsProcessed: logInfo.count,
        lastLog: logInfo.lastLine || undefined,
        lastLogTime: logInfo.lastTime || undefined,
      };
    });
    return { content: [{ type: 'text', text: JSON.stringify({ watchers }, null, 2) }] };
  }
);

// Register Tool: start_watcher
server.tool(
  'start_watcher',
  'Start a specific Python watcher',
  {
    id: z.string().describe('The ID of the watcher to start (e.g., gmail, whatsapp)')
  },
  async ({ id }) => {
    const def = WATCHER_DEFS.find(d => d.id === id);
    if (!def) {
      return { 
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: `Watcher ${id} not found` }) }],
        isError: true 
      };
    }

    const scriptPath = path.join(ROOT_PATH, def.script);
    if (!fs.existsSync(scriptPath)) {
      return { 
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: `Script not found: ${def.script}` }) }],
        isError: true 
      };
    }

    const child = spawn('python', [scriptPath, '--watch'], {
      cwd: ROOT_PATH,
      detached: true,
      stdio: 'ignore'
    });
    child.unref();

    return { content: [{ type: 'text', text: JSON.stringify({ success: true, message: `${def.name} started`, pid: child.pid }) }] };
  }
);

// Register Tool: get_watcher_logs
server.tool(
  'get_watcher_logs',
  'Get recent logs for a specific watcher',
  {
    id: z.string().describe('The ID of the watcher'),
    limit: z.number().optional().default(50).describe('Max number of lines to return')
  },
  async ({ id, limit }) => {
    const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    const logFiles = [
      path.join(LOGS_DIR, `master-${today}.log`),
      path.join(LOGS_DIR, `${id}-${today}.log`),
    ];

    const allLines = [];
    for (const lf of logFiles) {
      const lines = readLogLines(lf, 500);
      for (const line of lines) {
        if (id === 'all' || line.toLowerCase().includes(id)) {
          const timeMatch = line.match(/\[(\d{2}:\d{2}:\d{2})\]/);
          allLines.push({
            time: timeMatch ? timeMatch[1] : '',
            message: line,
          });
        }
      }
    }

    const logs = allLines.slice(-limit);
    return { content: [{ type: 'text', text: JSON.stringify({ logs, total: allLines.length }, null, 2) }] };
  }
);

// Register Tool: start_all_watchers
server.tool(
  'start_all_watchers',
  'Start the master orchestrator to run all watchers',
  {},
  async () => {
    const masterScript = path.join(ROOT_PATH, 'run_master.py');
    if (!fs.existsSync(masterScript)) {
      return { 
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: 'run_master.py not found' }) }],
        isError: true 
      };
    }

    const child = spawn('python', [masterScript], {
      cwd: ROOT_PATH,
      detached: true,
      stdio: 'ignore'
    });
    child.unref();

    return { content: [{ type: 'text', text: JSON.stringify({ success: true, message: 'Master orchestrator started', pid: child.pid }) }] };
  }
);

// Start server
async function main() {
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('MCP Watcher Server running on stdio');
  } catch (error) {
    console.error('Server error:', error);
    process.exit(1);
  }
}

main();
