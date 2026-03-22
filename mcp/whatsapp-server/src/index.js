#!/usr/bin/env node
/**
 * MCP WhatsApp Server
 * Provides WhatsApp operations via the whatsapp_sender.py script
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { config } from 'dotenv';
import { exec } from 'child_process';
import * as path from 'path';
import { fileURLToPath } from 'url';

// Load environment variables
config();

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT_PATH = path.resolve(__dirname, '..', '..', '..');

// Create MCP server
const server = new McpServer({
  name: 'whatsapp-server',
  version: '1.0.0',
  description: 'MCP server for WhatsApp messaging'
});

// Register Tool: send_message
server.tool(
  'send_message',
  'Send a WhatsApp message via Playwright',
  {
    recipient: z.string().describe('The name of the contact as it appears in WhatsApp'),
    instruction: z.string().describe('Natural language instruction for the message'),
    dry_run: z.boolean().optional().default(false).describe('If true, only generate the message without sending')
  },
  async ({ recipient, instruction, dry_run }) => {
    return new Promise((resolve) => {
      const scriptPath = path.join(ROOT_PATH, 'whatsapp_sender.py');
      const env = { ...process.env, DRY_RUN: dry_run ? 'true' : 'false' };
      
      const cmd = `python "${scriptPath}" --contact "${recipient}" --instruction "${instruction}"`;
      
      exec(cmd, { cwd: ROOT_PATH, env }, (error, stdout, stderr) => {
        if (error) {
          resolve({
            content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message, stderr }) }],
            isError: true
          });
          return;
        }

        // Extract generated message from stdout if possible
        // The script prints it between dividers ==================================================
        const match = stdout.match(/Message\s*:\s*(.+?)\n=+/s);
        const message = match ? match[1].trim() : "See logs for output";

        resolve({
          content: [{ type: 'text', text: JSON.stringify({ success: true, message, stdout }) }]
        });
      });
    });
  }
);

// Start server
async function main() {
  try {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('MCP WhatsApp Server running on stdio');
  } catch (error) {
    console.error('Server error:', error);
    process.exit(1);
  }
}

main();
