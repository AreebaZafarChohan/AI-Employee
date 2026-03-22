import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { logger } from '../lib/logger';

export class McpClientService {
  private clients: Map<string, Client> = new Map();

  async getClient(serverName: string, command: string, args: string[]): Promise<Client> {
    if (this.clients.has(serverName)) {
      return this.clients.get(serverName)!;
    }

    const transport = new StdioClientTransport({
      command,
      args,
    });

    const client = new Client(
      {
        name: 'ai-employee-backend',
        version: '1.0.0',
      },
      {
        capabilities: {
          prompts: {},
          resources: {},
          tools: {},
        },
      }
    );

    await client.connect(transport);
    this.clients.set(serverName, client);
    logger.info(`Connected to MCP server: ${serverName}`);
    return client;
  }

  async callTool(serverName: string, command: string, args: string[], toolName: string, toolArgs: any) {
    const client = await this.getClient(serverName, command, args);
    return await client.callTool({
      name: toolName,
      arguments: toolArgs,
    });
  }
}

export const mcpClientService = new McpClientService();
